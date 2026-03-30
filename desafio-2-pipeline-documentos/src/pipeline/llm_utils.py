"""Helpers for normalizing LLM responses across provider payload formats."""

from __future__ import annotations

import time
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


def should_retry_llm_error(exc: Exception) -> bool:
    """Return True when an LLM error looks transient or quota-related."""
    text = str(exc).lower()
    markers = (
        "resource_exhausted",
        "429",
        "500",
        "503",
        "504",
        "unavailable",
        "rate limit",
        "temporarily unavailable",
        "internal error",
    )
    return any(marker in text for marker in markers)


def invoke_with_retry(
    llm: Any,
    prompt: str,
    *,
    max_attempts: int,
    base_delay: float,
    max_delay: float,
    logger: Any | None = None,
) -> Any:
    """Invoke an LLM with exponential backoff for transient failures."""
    for attempt in range(1, max_attempts + 1):
        try:
            return llm.invoke(prompt)
        except Exception as exc:
            if attempt >= max_attempts or not should_retry_llm_error(exc):
                raise

            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            if logger is not None:
                logger.warning(
                    "LLM call failed on attempt %d/%d. Retrying in %.1fs: %s",
                    attempt,
                    max_attempts,
                    delay,
                    exc,
                )
            time.sleep(delay)

    raise RuntimeError("LLM invocation exhausted retry loop unexpectedly.")
