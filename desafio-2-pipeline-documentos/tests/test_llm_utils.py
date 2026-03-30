from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.llm_utils import (  # noqa: E402
    message_text,
    should_retry_llm_error,
    strip_code_fences,
)


class TestLlmUtils(unittest.TestCase):
    def test_message_text_handles_mixed_blocks(self) -> None:
        raw = ["inicio", {"text": "meio"}, {"content": [{"text": "fim"}]}]
        self.assertEqual(message_text(raw), "inicio\nmeio\nfim")

    def test_strip_code_fences_removes_json_wrapper(self) -> None:
        raw = '```json\n{"status":"ok"}\n```'
        self.assertEqual(strip_code_fences(raw), '{"status":"ok"}')

    def test_should_retry_llm_error_detects_quota_failure(self) -> None:
        exc = RuntimeError("429 RESOURCE_EXHAUSTED: quota exceeded")
        self.assertTrue(should_retry_llm_error(exc))


if __name__ == "__main__":
    unittest.main()
