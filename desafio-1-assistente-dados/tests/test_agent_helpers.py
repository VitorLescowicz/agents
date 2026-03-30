from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.helpers import (  # noqa: E402
    clean_sql,
    message_text,
    normalize_steps,
    parse_json_object,
    should_retry_llm_error,
    summarize_step_result,
)


class TestAgentHelpers(unittest.TestCase):
    def test_message_text_flattens_nested_content(self) -> None:
        raw = [{"text": "primeira"}, {"content": [{"text": "segunda"}]}, "terceira"]
        self.assertEqual(message_text(raw), "primeira\nsegunda\nterceira")

    def test_clean_sql_removes_markdown(self) -> None:
        self.assertEqual(clean_sql("```sql\nSELECT 1;\n```"), "SELECT 1;")

    def test_parse_json_object_accepts_code_fences(self) -> None:
        data = parse_json_object(
            '```json\n{"analysis_summary":"ok","steps":["etapa 1","etapa 2"]}\n```'
        )
        self.assertEqual(data["analysis_summary"], "ok")
        self.assertEqual(data["steps"], ["etapa 1", "etapa 2"])

    def test_normalize_steps_limits_and_dedupes(self) -> None:
        steps = normalize_steps(["a", "b", "a", "c", "d"], "fallback")
        self.assertEqual(steps, ["a", "b", "c"])

    def test_summarize_step_result_scalar(self) -> None:
        summary = summarize_step_result("contar clientes", ["total_clientes"], [(42,)])
        self.assertIn("total_clientes = 42", summary)

    def test_should_retry_llm_error_detects_quota_failure(self) -> None:
        exc = RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded")
        self.assertTrue(should_retry_llm_error(exc))


if __name__ == "__main__":
    unittest.main()
