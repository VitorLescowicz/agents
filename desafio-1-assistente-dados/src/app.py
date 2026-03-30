"""Streamlit frontend for the Data Assistant."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.agent.graph import DB_PATH, ask  # noqa: E402
from src.db.connection import get_schema_info  # noqa: E402
from src.viz.chart_picker import render_chart  # noqa: E402

st.set_page_config(
    page_title="Assistente de Dados",
    page_icon="📊",
    layout="wide",
)

EXAMPLE_QUESTIONS: list[str] = [
    "Quais sao os 5 clientes que mais gastaram?",
    "Qual a distribuicao de compras por categoria?",
    "Quantos chamados de suporte foram resolvidos vs nao resolvidos?",
    "Qual o ticket medio por canal de compra?",
    "Quais clientes interagiram com campanhas de marketing mas nao compraram nos ultimos 3 meses?",
]


def render_assistant_extra(extra: dict) -> None:
    analysis_summary = extra.get("analysis_summary", "")
    step_questions = extra.get("step_questions", [])
    executed_queries = extra.get("executed_queries", [])
    trace = extra.get("trace", [])

    if analysis_summary or step_questions:
        with st.expander("Plano de analise", expanded=False):
            if analysis_summary:
                st.write(analysis_summary)
            for index, step in enumerate(step_questions, start=1):
                st.markdown(f"{index}. {step}")

    if trace:
        with st.expander("Execucao detalhada", expanded=False):
            for entry in trace:
                title = entry.get("title", entry.get("stage", "etapa"))
                status = entry.get("status")
                header = title if not status else f"{title} [{status}]"
                st.markdown(f"**{header}**")
                if entry.get("question"):
                    st.write(f"Pergunta da etapa: {entry['question']}")
                if entry.get("details"):
                    st.write(entry["details"])
                if entry.get("summary"):
                    st.write(entry["summary"])
                if entry.get("steps"):
                    for index, step in enumerate(entry["steps"], start=1):
                        st.markdown(f"{index}. {step}")
                if entry.get("sql"):
                    st.code(entry["sql"], language="sql")
                if entry.get("error"):
                    st.warning(entry["error"])

    if executed_queries:
        with st.expander("Consultas executadas", expanded=False):
            for index, sql in enumerate(executed_queries, start=1):
                st.caption(f"Tentativa {index}")
                st.code(sql, language="sql")


with st.sidebar:
    st.header("Assistente Virtual de Dados")
    st.caption("Franq Open Finance - Desafio 1")
    st.divider()

    st.subheader("Perguntas de exemplo")
    for question in EXAMPLE_QUESTIONS:
        if st.button(question, key=f"example_{question[:20]}", use_container_width=True):
            st.session_state["pending_question"] = question

    st.divider()
    st.subheader("Banco de dados")
    if DB_PATH.exists():
        st.success(f"Conectado: `{DB_PATH.name}`")
        with st.expander("Schema do banco"):
            st.markdown(get_schema_info(DB_PATH), unsafe_allow_html=True)
    else:
        st.error(f"Banco nao encontrado em `{DB_PATH}`")

    st.divider()
    st.caption("Powered by Gemini 2.5 Flash + LangGraph")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

st.title("Assistente Virtual de Dados")
st.markdown(
    "Faca perguntas em linguagem natural sobre a base de clientes, "
    "compras, suporte e campanhas de marketing."
)

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("extra"):
            extra = message["extra"]
            render_assistant_extra(extra)
            if extra.get("columns") and extra.get("rows"):
                render_chart(
                    extra.get("viz_type", "table"),
                    extra["columns"],
                    extra["rows"],
                    title="",
                )

pending_question = st.session_state.pop("pending_question", None)
user_input = st.chat_input("Digite sua pergunta sobre os dados...")
question = pending_question or user_input

if question:
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Analisando dados..."):
            try:
                result = ask(question)

                answer = result.get("answer", "Sem resposta.")
                extra = {
                    "sql": result.get("sql_query", ""),
                    "error": result.get("error", ""),
                    "viz_type": result.get("viz_type", "table"),
                    "columns": result.get("columns", []),
                    "rows": result.get("rows", []),
                    "analysis_summary": result.get("analysis_summary", ""),
                    "step_questions": result.get("step_questions", []),
                    "trace": result.get("trace", []),
                    "executed_queries": result.get("executed_queries", []),
                }

                st.markdown(answer)
                render_assistant_extra(extra)
                if extra["columns"] and extra["rows"]:
                    render_chart(extra["viz_type"], extra["columns"], extra["rows"], title="")

                st.session_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "extra": extra,
                    }
                )
            except Exception as exc:
                error_message = f"Erro ao processar a pergunta: {exc}"
                st.error(error_message)
                st.session_state["messages"].append(
                    {"role": "assistant", "content": error_message}
                )
