"""LangGraph state-machine that powers the data assistant.

Flow
----
START -> discover_schema -> plan_query -> execute_sql
  -> (error & retries < 3) -> handle_error -> plan_query   (loop)
  -> synthesize_answer -> END
"""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from src.agent.prompts import (
    ANSWER_SYNTHESIS_PROMPT,
    SQL_ERROR_CORRECTION_PROMPT,
    SQL_GENERATION_PROMPT,
)
from src.agent.state import AgentState
from src.agent.tools import fetch_schema, run_sql
from src.viz.chart_picker import pick_chart

load_dotenv()

# ── Defaults ─────────────────────────────────────────────────────────

_DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "clientes_completo.db"
DB_PATH = Path(os.getenv("DB_PATH", str(_DEFAULT_DB)))
MAX_RETRIES = 3
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")


def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


# ── Node functions ───────────────────────────────────────────────────


def discover_schema(state: AgentState) -> dict[str, Any]:
    """Introspect the database and cache the schema in state."""
    schema = fetch_schema(DB_PATH)
    return {"schema_info": schema}


def plan_query(state: AgentState) -> dict[str, Any]:
    """Ask the LLM to generate a SQL query from the question + schema."""
    llm = _get_llm()
    prompt = SQL_GENERATION_PROMPT.format(
        schema=state["schema_info"],
        question=state["question"],
    )
    response = llm.invoke(prompt)
    sql = _clean_sql(response.content)
    return {"sql_query": sql}


def execute_sql(state: AgentState) -> dict[str, Any]:
    """Run the generated SQL against the database."""
    try:
        columns, rows = run_sql(DB_PATH, state["sql_query"])
        return {
            "sql_result": (columns, rows),
            "columns": columns,
            "rows": rows,
            "error": None,
        }
    except (sqlite3.Error, Exception) as exc:
        return {
            "sql_result": None,
            "columns": [],
            "rows": [],
            "error": str(exc),
            "retry_count": state.get("retry_count", 0) + 1,
        }


def handle_error(state: AgentState) -> dict[str, Any]:
    """Ask the LLM to fix the failed SQL query."""
    llm = _get_llm()
    prompt = SQL_ERROR_CORRECTION_PROMPT.format(
        schema=state["schema_info"],
        sql_query=state["sql_query"],
        error=state["error"],
        question=state["question"],
    )
    response = llm.invoke(prompt)
    sql = _clean_sql(response.content)
    return {"sql_query": sql}


def synthesize_answer(state: AgentState) -> dict[str, Any]:
    """Produce a natural-language answer and choose a visualisation type."""
    columns = state.get("columns", [])
    rows = state.get("rows", [])

    # If we exhausted retries with no data, produce a fallback answer
    if not columns and not rows:
        return {
            "answer": (
                "Desculpe, nao consegui obter os dados para responder "
                "sua pergunta. Tente reformula-la."
            ),
            "viz_type": "table",
        }

    # Truncate rows for the prompt to avoid token overflow
    display_rows = rows[:20]

    llm = _get_llm()
    prompt = ANSWER_SYNTHESIS_PROMPT.format(
        question=state["question"],
        sql_query=state["sql_query"],
        columns=columns,
        rows=display_rows,
    )
    response = llm.invoke(prompt)
    answer_text = _message_text(response.content)

    # Extract viz tag from LLM response
    viz_type = _extract_viz_type(answer_text)

    # Fall back to heuristic if LLM didn't include a tag
    if viz_type == "table":
        viz_type = pick_chart(columns, rows)

    # Strip the viz tag from the visible answer
    clean_answer = re.sub(r"\[VIZ:\w+\]", "", answer_text).strip()

    return {"answer": clean_answer, "viz_type": viz_type}


# ── Routing logic ────────────────────────────────────────────────────


def route_after_execute(state: AgentState) -> str:
    """Decide whether to retry or move to synthesis."""
    if state.get("error") and state.get("retry_count", 0) < MAX_RETRIES:
        return "handle_error"
    return "synthesize_answer"


# ── Graph construction ───────────────────────────────────────────────


def build_graph() -> StateGraph:
    """Construct and compile the LangGraph agent."""
    graph = StateGraph(AgentState)

    graph.add_node("discover_schema", discover_schema)
    graph.add_node("plan_query", plan_query)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("handle_error", handle_error)
    graph.add_node("synthesize_answer", synthesize_answer)

    graph.set_entry_point("discover_schema")
    graph.add_edge("discover_schema", "plan_query")
    graph.add_edge("plan_query", "execute_sql")

    graph.add_conditional_edges(
        "execute_sql",
        route_after_execute,
        {
            "handle_error": "handle_error",
            "synthesize_answer": "synthesize_answer",
        },
    )

    graph.add_edge("handle_error", "plan_query")
    graph.add_edge("synthesize_answer", END)

    return graph.compile()


# ── Helpers ──────────────────────────────────────────────────────────


def _message_text(raw: Any) -> str:
    """Normalize provider-specific LLM content payloads into plain text."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        parts = [_message_text(item) for item in raw]
        return "\n".join(part for part in parts if part).strip()
    if isinstance(raw, dict):
        if isinstance(raw.get("text"), str):
            return raw["text"]
        for key in ("content", "parts"):
            if key in raw:
                return _message_text(raw[key])
    text_attr = getattr(raw, "text", None)
    if isinstance(text_attr, str):
        return text_attr
    return str(raw).strip()


def _clean_sql(raw: Any) -> str:
    """Strip markdown code fences and whitespace from LLM output."""
    text = _message_text(raw).strip()
    # Remove ```sql ... ``` wrappers
    text = re.sub(r"^```(?:sql)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_viz_type(text: str) -> str:
    """Extract ``[VIZ:xxx]`` tag from the synthesis answer."""
    match = re.search(r"\[VIZ:(\w+)\]", text)
    if match:
        return match.group(1)
    return "table"


# ── Convenience runner ───────────────────────────────────────────────


def ask(question: str) -> AgentState:
    """Run the full agent pipeline for a single question."""
    agent = build_graph()
    initial_state: AgentState = {
        "question": question,
        "schema_info": "",
        "sql_query": "",
        "sql_result": None,
        "error": None,
        "retry_count": 0,
        "answer": "",
        "viz_type": "table",
        "columns": [],
        "rows": [],
    }
    result = agent.invoke(initial_state)
    return result
