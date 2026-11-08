"""Regression for explicit sensitive Globs using '?' and character classes (#438)."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "hooks" / "pretool_gate_review.py"
spec = importlib.util.spec_from_file_location("gate_review_glob_literals", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GateGuardGlobLiteralTests(unittest.TestCase):
    def event(self, tool: str, field: str, value: str):
        return {"schema_version": 1, "tool_name": tool, "tool_input": {field: value}}

    def test_sensitive_names_hidden_by_glob_syntax_need_review(self):
        patterns = (
            "**/[.]env",
            "**/id_?sa",
            "**/credenti?ls.json",
            "**/private.[p]em",
            "**/[.]env.production",
        )
        for pattern in patterns:
            with self.subTest(pattern=pattern):
                result = module.review_event(self.event("Glob", "pattern", pattern))
                self.assertEqual(result["decision"], "REVIEW_REQUIRED")
                self.assertEqual(result["reason_code"], "SENSITIVE_OR_OUT_OF_SCOPE_PATH")
                self.assertEqual(result["blocking_effect"], "NONE_SOURCE_ONLY")
                self.assertFalse(result["hook_registered"])

    def test_benign_globs_and_read_templates_remain_candidates(self):
        for pattern in ("src/**/*_test.py", "packages/*/README.md", "docs/**/*.md", "assets/**/*.svg"):
            with self.subTest(pattern=pattern):
                result = module.review_event(self.event("Glob", "pattern", pattern))
                self.assertEqual(result["decision"], "ALLOW_CANDIDATE")
        for path in (".env.example", "config/.env.dist", "src/app.py"):
            self.assertEqual(module.review_event(self.event("Read", "path", path))["decision"],
                             "ALLOW_CANDIDATE")
        self.assertEqual(module.review_event(self.event("Grep", "pattern", r"\.env"))["decision"],
                         "ALLOW_CANDIDATE")


if __name__ == "__main__":
    unittest.main()
