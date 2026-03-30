"""Heuristic chart-type selection and Plotly/Streamlit rendering.

No LLM calls — pure rule-based logic to choose the best visualisation
for a given query result.
"""

from __future__ import annotations

import re
from typing import Any

import plotly.express as px
import streamlit as st


# ── Detection helpers ────────────────────────────────────────────────

_DATE_PATTERN = re.compile(
    r"^(data|date|dia|mes|ano|month|year|periodo|dt_|data_)", re.IGNORECASE
)


def _looks_like_date_col(name: str) -> bool:
    return bool(_DATE_PATTERN.search(name))


def _is_numeric(value: Any) -> bool:
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value.replace(",", "."))
            return True
        except (ValueError, AttributeError):
            return False
    return False


# ── Public API ───────────────────────────────────────────────────────


def pick_chart(columns: list[str], rows: list[tuple]) -> str:
    """Choose the best chart type based on simple heuristics.

    Returns one of ``"metric"``, ``"line"``, ``"bar"``, or ``"table"``.
    """
    if not rows or not columns:
        return "table"

    # Single scalar value → metric card
    if len(columns) == 1 and len(rows) == 1:
        return "metric"

    # Two columns: detect date+number → line; category+number → bar
    if len(columns) == 2:
        has_date = any(_looks_like_date_col(c) for c in columns)
        has_numeric = any(_is_numeric(rows[0][i]) for i in range(len(columns)))

        if has_date and has_numeric:
            return "line"
        if has_numeric:
            return "bar"

    # More columns but first looks like a date and there is at least one number
    if len(columns) >= 2:
        if _looks_like_date_col(columns[0]) and any(
            _is_numeric(rows[0][i]) for i in range(1, len(columns))
        ):
            return "line"

        # Category + aggregated numbers
        non_numeric_cols = [
            i for i in range(len(columns)) if not _is_numeric(rows[0][i])
        ]
        numeric_cols = [
            i for i in range(len(columns)) if _is_numeric(rows[0][i])
        ]
        if len(non_numeric_cols) >= 1 and len(numeric_cols) >= 1 and len(rows) <= 30:
            return "bar"

    return "table"


def render_chart(
    chart_type: str,
    columns: list[str],
    rows: list[tuple],
    title: str = "",
) -> None:
    """Render *chart_type* inside the current Streamlit context."""
    import pandas as pd

    if not rows or not columns:
        st.info("Sem dados para exibir.")
        return

    df = pd.DataFrame(rows, columns=columns)

    if chart_type == "metric":
        value = rows[0][0]
        label = columns[0]
        # Format large numbers nicely
        if isinstance(value, (int, float)):
            formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            formatted = str(value)
        st.metric(label=label, value=formatted)

    elif chart_type == "line":
        x_col = columns[0]
        y_cols = columns[1:]
        fig = px.line(df, x=x_col, y=y_cols, title=title, markers=True)
        fig.update_layout(xaxis_title=x_col, yaxis_title="Valor")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "bar":
        # Find first non-numeric column as x, first numeric as y
        x_col = columns[0]
        y_cols = [
            c
            for i, c in enumerate(columns)
            if i > 0 and len(rows) > 0 and _is_numeric(rows[0][i])
        ]
        if not y_cols:
            y_cols = [columns[-1]]

        fig = px.bar(df, x=x_col, y=y_cols, title=title, text_auto=True)
        fig.update_layout(xaxis_title=x_col, yaxis_title="Valor")
        st.plotly_chart(fig, use_container_width=True)

    else:  # table
        st.dataframe(df, use_container_width=True, hide_index=True)
