"""Helpers for normalizing LLM responses across provider payload formats."""

from __future__ import annotations

from typing import Any


def message_text(raw: Any) -> str:
    """Collapse string/list/dict message payloads into plain text."""
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
