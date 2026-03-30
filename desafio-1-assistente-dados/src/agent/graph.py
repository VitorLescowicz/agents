"""LangGraph state-machine that powers the data assistant."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from src.agent.helpers import (
    clean_sql,
    extract_viz_type,
    format_prior_findings,
    message_text,
    normalize_steps,
    parse_json_object,
    summarize_step_result,
)
from src.agent.prompts import (
    ANSWER_SYNTHESIS_PROMPT,
    QUESTION_ANALYSIS_PROMPT,
    SQL_ERROR_CORRECTION_PROMPT,
    SQL_GENERATION_PROMPT,
)
from src.agent.state import AgentState
from src.agent.tools import fetch_schema, run_sql
from src.viz.chart_picker import pick_chart

load_dotenv()

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


def discover_schema(state: AgentState) -> dict[str, Any]:
    """Introspect the database and cache the schema in state."""
    schema = fetch_schema(DB_PATH)
    table_count = schema.count("### Tabela:")
    trace = _append_trace(
        state,
        stage="discover_schema",
        title="Schema inspecionado dinamicamente",
        details=f"{table_count} tabelas carregadas para contextualizar a analise.",
    )
    return {"schema_info": schema, "trace": trace}


def analyze_question(state: AgentState) -> dict[str, Any]:
    """Create an explicit execution plan with one to three analytical steps."""
    llm = _get_llm()
    prompt = QUESTION_ANALYSIS_PROMPT.format(
        schema=state["schema_info"],
        question=state["question"],
    )

    try:
        response = llm.invoke(prompt)
        plan = parse_json_object(response.content)
        analysis_summary = str(plan.get("analysis_summary", "")).strip()
        if not analysis_summary:
            analysis_summary = "Plano direto para responder a pergunta do usuario."
        step_questions = normalize_steps(plan.get("steps"), state["question"])
        trace = _append_trace(
            state,
            stage="analyze_question",
            title="Plano de analise definido",
            details=analysis_summary,
            steps=step_questions,
            status="success",
        )
    except Exception as exc:
        analysis_summary = (
            "Nao foi possivel obter um plano estruturado do modelo. "
            "A pergunta sera respondida em uma unica etapa."
        )
        step_questions = [state["question"]]
        trace = _append_trace(
            state,
            stage="analyze_question",
            title="Plano de analise em modo fallback",
            details=analysis_summary,
            steps=step_questions,
            status="fallback",
            error=str(exc),
        )

    return {
        "analysis_summary": analysis_summary,
        "step_questions": step_questions,
        "current_step_index": 0,
        "current_step_question": step_questions[0],
        "step_summaries": [],
        "executed_queries": [],
        "trace": trace,
    }


def plan_query(state: AgentState) -> dict[str, Any]:
    """Ask the LLM to generate a SQL query for the current analysis step."""
    llm = _get_llm()
    step_number = state["current_step_index"] + 1
    prompt = SQL_GENERATION_PROMPT.format(
        schema=state["schema_info"],
        question=state["question"],
        analysis_summary=state["analysis_summary"],
        step_number=step_number,
        total_steps=len(state["step_questions"]),
        current_step_question=state["current_step_question"],
        prior_findings=format_prior_findings(state.get("step_summaries", [])),
    )
    response = llm.invoke(prompt)
    sql = clean_sql(response.content)
    trace = _append_trace(
        state,
        stage="plan_query",
        title=f"SQL gerada para a etapa {step_number}",
        step=step_number,
        question=state["current_step_question"],
        sql=sql,
        attempt=state.get("retry_count", 0) + 1,
    )
    return {"sql_query": sql, "trace": trace}


def execute_sql(state: AgentState) -> dict[str, Any]:
    """Run the generated SQL against the database."""
    step_number = state["current_step_index"] + 1
    executed_queries = list(state.get("executed_queries", []))
    executed_queries.append(state["sql_query"])

    try:
        columns, rows = run_sql(DB_PATH, state["sql_query"])
        trace = _append_trace(
            state,
            stage="execute_sql",
            title=f"Etapa {step_number} executada",
            step=step_number,
            question=state["current_step_question"],
            status="success",
            row_count=len(rows),
            sql=state["sql_query"],
        )
        return {
            "sql_result": (columns, rows),
            "columns": columns,
            "rows": rows,
            "error": None,
            "executed_queries": executed_queries,
            "trace": trace,
        }
    except (sqlite3.Error, Exception) as exc:
        trace = _append_trace(
            state,
            stage="execute_sql",
            title=f"Etapa {step_number} falhou",
            step=step_number,
            question=state["current_step_question"],
            status="error",
            sql=state["sql_query"],
            error=str(exc),
        )
        return {
            "sql_result": None,
            "columns": [],
            "rows": [],
            "error": str(exc),
            "retry_count": state.get("retry_count", 0) + 1,
            "executed_queries": executed_queries,
            "trace": trace,
        }


def handle_error(state: AgentState) -> dict[str, Any]:
    """Ask the LLM to fix the failed SQL query."""
    llm = _get_llm()
    step_number = state["current_step_index"] + 1
    prompt = SQL_ERROR_CORRECTION_PROMPT.format(
        schema=state["schema_info"],
        question=state["question"],
        step_number=step_number,
        total_steps=len(state["step_questions"]),
        current_step_question=state["current_step_question"],
        prior_findings=format_prior_findings(state.get("step_summaries", [])),
        sql_query=state["sql_query"],
        error=state["error"],
    )
    response = llm.invoke(prompt)
    sql = clean_sql(response.content)
    trace = _append_trace(
        state,
        stage="handle_error",
        title=f"Nova tentativa de SQL para a etapa {step_number}",
        step=step_number,
        question=state["current_step_question"],
        sql=sql,
        error=state["error"],
        attempt=state.get("retry_count", 0) + 1,
    )
    return {"sql_query": sql, "trace": trace}


def advance_plan(state: AgentState) -> dict[str, Any]:
    """Persist step findings and decide whether another step is needed."""
    step_number = state["current_step_index"] + 1
    step_summaries = list(state.get("step_summaries", []))

    if state.get("error"):
        summary = (
            f"A etapa {step_number} falhou apos {state.get('retry_count', 0)} "
            f"tentativas: {state['error']}"
        )
        trace = _append_trace(
            state,
            stage="advance_plan",
            title=f"Etapa {step_number} encerrada com erro",
            step=step_number,
            status="error",
            summary=summary,
        )
        step_summaries.append(summary)
        return {"step_summaries": step_summaries, "trace": trace}

    summary = summarize_step_result(
        state["current_step_question"],
        state.get("columns", []),
        state.get("rows", []),
    )
    step_summaries.append(summary)
    trace = _append_trace(
        state,
        stage="advance_plan",
        title=f"Etapa {step_number} concluida",
        step=step_number,
        status="success",
        summary=summary,
    )

    if len(step_summaries) < len(state["step_questions"]):
        next_step_index = len(step_summaries)
        return {
            "step_summaries": step_summaries,
            "current_step_index": next_step_index,
            "current_step_question": state["step_questions"][next_step_index],
            "retry_count": 0,
            "error": None,
            "sql_query": "",
            "sql_result": None,
            "columns": [],
            "rows": [],
            "trace": trace,
        }

    return {"step_summaries": step_summaries, "trace": trace}


def synthesize_answer(state: AgentState) -> dict[str, Any]:
    """Produce a natural-language answer and choose a visualisation type."""
    columns = state.get("columns", [])
    rows = state.get("rows", [])
    trace = list(state.get("trace", []))

    if state.get("error") and not rows:
        answer = (
            "Desculpe, nao consegui concluir a analise automatica. "
            f"Ultimo erro: {state['error']}"
        )
        trace.append(
            {
                "stage": "synthesize_answer",
                "title": "Resposta final em modo fallback",
                "status": "error",
                "details": answer,
            }
        )
        return {"answer": answer, "viz_type": "table", "trace": trace}

    if not columns and not rows:
        answer = (
            "Nao encontrei dados suficientes para responder a pergunta "
            "com o contexto atual."
        )
        trace.append(
            {
                "stage": "synthesize_answer",
                "title": "Resposta final sem dados",
                "status": "empty",
                "details": answer,
            }
        )
        return {"answer": answer, "viz_type": "table", "trace": trace}

    llm = _get_llm()
    prompt = ANSWER_SYNTHESIS_PROMPT.format(
        question=state["question"],
        analysis_summary=state["analysis_summary"],
        step_summaries=format_prior_findings(state.get("step_summaries", [])),
        sql_query=state["sql_query"],
        columns=columns,
        rows=rows[:20],
    )
    response = llm.invoke(prompt)
    answer_text = message_text(response.content)
    viz_type = extract_viz_type(answer_text)
    if viz_type == "table":
        viz_type = pick_chart(columns, rows)

    clean_answer = answer_text
    for tag in ("[VIZ:table]", "[VIZ:bar]", "[VIZ:line]", "[VIZ:metric]"):
        clean_answer = clean_answer.replace(tag, "")
    clean_answer = clean_answer.strip()

    trace.append(
        {
            "stage": "synthesize_answer",
            "title": "Resposta final consolidada",
            "status": "success",
            "details": clean_answer,
            "viz_type": viz_type,
        }
    )
    return {"answer": clean_answer, "viz_type": viz_type, "trace": trace}


def route_after_execute(state: AgentState) -> str:
    """Decide whether to retry the SQL or advance the plan."""
    if state.get("error") and state.get("retry_count", 0) < MAX_RETRIES:
        return "handle_error"
    return "advance_plan"


def route_after_advance(state: AgentState) -> str:
    """Decide whether another analytical step is required."""
    if state.get("error"):
        return "synthesize_answer"
    if len(state.get("step_summaries", [])) < len(state.get("step_questions", [])):
        return "plan_query"
    return "synthesize_answer"


def build_graph() -> StateGraph:
    """Construct and compile the LangGraph agent."""
    graph = StateGraph(AgentState)

    graph.add_node("discover_schema", discover_schema)
    graph.add_node("analyze_question", analyze_question)
    graph.add_node("plan_query", plan_query)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("handle_error", handle_error)
    graph.add_node("advance_plan", advance_plan)
    graph.add_node("synthesize_answer", synthesize_answer)

    graph.set_entry_point("discover_schema")
    graph.add_edge("discover_schema", "analyze_question")
    graph.add_edge("analyze_question", "plan_query")
    graph.add_edge("plan_query", "execute_sql")

    graph.add_conditional_edges(
        "execute_sql",
        route_after_execute,
        {
            "handle_error": "handle_error",
            "advance_plan": "advance_plan",
        },
    )

    graph.add_edge("handle_error", "execute_sql")
    graph.add_conditional_edges(
        "advance_plan",
        route_after_advance,
        {
            "plan_query": "plan_query",
            "synthesize_answer": "synthesize_answer",
        },
    )
    graph.add_edge("synthesize_answer", END)

    return graph.compile()


def _append_trace(state: AgentState, **entry: Any) -> list[dict[str, Any]]:
    trace = list(state.get("trace", []))
    trace.append(entry)
    return trace


def ask(question: str) -> AgentState:
    """Run the full agent pipeline for a single question."""
    agent = build_graph()
    initial_state: AgentState = {
        "question": question,
        "schema_info": "",
        "analysis_summary": "",
        "step_questions": [],
        "current_step_index": 0,
        "current_step_question": "",
        "step_summaries": [],
        "trace": [],
        "executed_queries": [],
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
