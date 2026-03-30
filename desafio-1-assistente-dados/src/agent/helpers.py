"""Helper functions for parsing LLM responses and formatting agent traces."""

from __future__ import annotations

import json
import re
from typing import Any


def message_text(raw: Any) -> str:
    """Normalize provider-specific LLM content payloads into plain text."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        parts = [message_text(item) for item in raw]
        return "\n".join(part for part in parts if part).strip()
    if isinstance(raw, dict):
        if isinstance(raw.get("text"), str):
            return raw["text"]
        for key in ("content", "parts"):
            if key in raw:
                return message_text(raw[key])
    text_attr = getattr(raw, "text", None)
    if isinstance(text_attr, str):
        return text_attr
    return str(raw).strip()


def strip_code_fences(raw: Any) -> str:
    """Remove Markdown code fences from a model response when present."""
    content = message_text(raw).strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        content = content.rsplit("```", 1)[0]
    return content.strip()


def clean_sql(raw: Any) -> str:
    """Strip markdown wrappers and whitespace from SQL returned by the model."""
    text = strip_code_fences(raw)
    text = re.sub(r"^```(?:sql)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_viz_type(text: str) -> str:
    """Extract ``[VIZ:xxx]`` tag from the synthesis answer."""
    match = re.search(r"\[VIZ:(\w+)\]", text)
    if match:
        return match.group(1)
    return "table"


def parse_json_object(raw: Any) -> dict[str, Any]:
    """Parse a JSON object from a model response, tolerating fenced blocks."""
    content = strip_code_fences(raw)
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        content = match.group(0)

    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object from the model.")
    return data


def normalize_steps(steps: Any, fallback_question: str) -> list[str]:
    """Normalize a model-produced plan into one to three distinct step prompts."""
    if not isinstance(steps, list):
        return [fallback_question]

    normalized: list[str] = []
    for item in steps:
        text = " ".join(str(item).split()).strip()
        if text and text not in normalized:
            normalized.append(text)
        if len(normalized) == 3:
            break

    return normalized or [fallback_question]


def format_prior_findings(step_summaries: list[str]) -> str:
    """Render previous step findings for subsequent prompts."""
    if not step_summaries:
        return "Nenhum achado intermediario disponivel."
    return "\n".join(
        f"- Etapa {index}: {summary}"
        for index, summary in enumerate(step_summaries, start=1)
    )


def summarize_step_result(
    step_question: str,
    columns: list[str],
    rows: list[tuple],
) -> str:
    """Create a compact deterministic summary of a SQL step result."""
    if not columns or not rows:
        return f"A etapa '{step_question}' nao retornou linhas."

    if len(columns) == 1 and len(rows) == 1:
        return (
            f"A etapa '{step_question}' retornou {columns[0]} = "
            f"{_format_value(rows[0][0])}."
        )

    preview_rows = []
    for row in rows[:3]:
        pairs = ", ".join(
            f"{column}={_format_value(value)}"
            for column, value in zip(columns, row, strict=False)
        )
        preview_rows.append(f"({pairs})")

    preview = "; ".join(preview_rows)
    return (
        f"A etapa '{step_question}' retornou {len(rows)} linhas com colunas "
        f"{', '.join(columns)}. Amostra: {preview}"
    )


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)
