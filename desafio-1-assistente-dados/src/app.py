"""Streamlit frontend for the Data Assistant.

Run with:
    streamlit run src/app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on sys.path so `src.*` imports work when
# Streamlit is launched from the project directory.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.agent.graph import DB_PATH, ask  # noqa: E402
from src.db.connection import get_schema_info  # noqa: E402
from src.viz.chart_picker import render_chart  # noqa: E402

# ── Page config ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Assistente de Dados",
    page_icon="📊",
    layout="wide",
)

# ── Sidebar ──────────────────────────────────────────────────────────

EXAMPLE_QUESTIONS: list[str] = [
    "Quais são os 5 clientes que mais gastaram?",
    "Qual a distribuição de compras por categoria?",
    "Quantos chamados de suporte foram resolvidos vs não resolvidos?",
    "Qual o ticket médio por canal de compra?",
    "Quais clientes interagiram com campanhas de marketing mas não compraram nos últimos 3 meses?",
]

with st.sidebar:
    st.header("Assistente Virtual de Dados")
    st.caption("Franq Open Finance — Desafio 1")
    st.divider()

    st.subheader("Perguntas de exemplo")
    for q in EXAMPLE_QUESTIONS:
        if st.button(q, key=f"ex_{q[:20]}", use_container_width=True):
            st.session_state["pending_question"] = q

    st.divider()

    # DB summary
    st.subheader("Banco de dados")
    if DB_PATH.exists():
        st.success(f"Conectado: `{DB_PATH.name}`")
        with st.expander("Schema do banco"):
            schema_text = get_schema_info(DB_PATH)
            st.markdown(schema_text, unsafe_allow_html=True)
    else:
        st.error(f"Banco nao encontrado em `{DB_PATH}`")

    st.divider()
    st.caption("Powered by Gemini 2.5 Flash + LangGraph")

# ── Session state ────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ── Chat display ─────────────────────────────────────────────────────

st.title("Assistente Virtual de Dados")
st.markdown(
    "Faça perguntas em linguagem natural sobre a base de clientes, "
    "compras, suporte e campanhas de marketing."
)

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("extra"):
            extra = msg["extra"]
            with st.expander("Raciocínio e SQL"):
                st.code(extra.get("sql", ""), language="sql")
                if extra.get("error"):
                    st.warning(f"Erro corrigido: {extra['error']}")
            if extra.get("columns") and extra.get("rows"):
                render_chart(
                    extra.get("viz_type", "table"),
                    extra["columns"],
                    extra["rows"],
                    title="",
                )

# ── Input handling ───────────────────────────────────────────────────

# Check for pending question from sidebar buttons
pending = st.session_state.pop("pending_question", None)
user_input = st.chat_input("Digite sua pergunta sobre os dados...")

question = pending or user_input

if question:
    # Append user message
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("Analisando dados..."):
            try:
                result = ask(question)

                answer = result.get("answer", "Sem resposta.")
                sql = result.get("sql_query", "")
                error = result.get("error", "")
                viz_type = result.get("viz_type", "table")
                columns = result.get("columns", [])
                rows = result.get("rows", [])

                st.markdown(answer)

                with st.expander("Raciocínio e SQL"):
                    st.code(sql, language="sql")
                    if error:
                        st.warning(f"Erro corrigido: {error}")

                if columns and rows:
                    render_chart(viz_type, columns, rows, title="")

                # Save to history
                st.session_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "extra": {
                            "sql": sql,
                            "error": error,
                            "viz_type": viz_type,
                            "columns": columns,
                            "rows": rows,
                        },
                    }
                )

            except Exception as exc:
                error_msg = f"Erro ao processar a pergunta: {exc}"
                st.error(error_msg)
                st.session_state["messages"].append(
                    {"role": "assistant", "content": error_msg}
                )
