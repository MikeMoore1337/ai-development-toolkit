"""Synthetic regression tests for non-enforcing source-only GateGuard preflight."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "hooks" / "pretool_gate_review.py"
spec = importlib.util.spec_from_file_location("native_gate_review", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class NativeGateReviewTests(unittest.TestCase):
    def event(self, tool, payload):
        return {"schema_version": 1, "tool_name": tool, "tool_input": payload}

    def test_exact_readonly_commands_and_declared_reads(self):
        cases = [
            ("Bash", "git status --short"),
            ("Bash", "pwd"),
            ("Bash", "git diff --check"),
            ("PowerShell", "Get-Location"),
        ]
        for tool, command in cases:
            with self.subTest(tool=tool, command=command):
                result = module.review_event(self.event(tool, {"command": command}))
                self.assertEqual("ALLOW_CANDIDATE", result["decision"])
                self.assertFalse(result["tool_executed"])
                self.assertEqual("NOT_VERIFIED", result["host_enforcement"])
        for tool, payload in (("Read", {"path": "src/app.py"}),
                              ("Grep", {"pattern": "auth"}),
                              ("Glob", {"pattern": "**/*.py"})):
            with self.subTest(tool=tool):
                self.assertEqual(
                    "ALLOW_CANDIDATE", module.review_event(self.event(tool, payload))["decision"]
                )

    def test_destructive_commands_are_recommended_block_without_execution(self):
        cases = [
            ("Bash", "git reset --hard HEAD"),
            ("Bash", "git clean -fd"),
            ("Bash", "rm -rf project"),
            ("Bash", "DROP TABLE users"),
            ("PowerShell", "Remove-Item -Recurse C:/Windows"),
            ("PowerShell", "Invoke-WebRequest https://example.com"),
        ]
        for tool, command in cases:
            with self.subTest(tool=tool, command=command):
                response = module.review_event(self.event(tool, {"command": command}))
                self.assertEqual("BLOCK_RECOMMENDED", response["decision"])
                self.assertEqual("DANGEROUS_OPERATION", response["reason_code"])
                self.assertEqual("NONE_SOURCE_ONLY", response["blocking_effect"])
                self.assertEqual("NOT_ATTESTED", response["owner_authorization"])

    def test_unknown_commands_require_review_and_chained_shell_rejected(self):
        for name in ("git push", "python -m pip install x", "git status && echo ok",
                     "git status $(false)", "ls -la", "git diff | cat"):
            with self.subTest(name=name):
                result = module.review_event(self.event("Bash", {"command": name}))
                self.assertNotEqual("ALLOW_CANDIDATE", result["decision"])
        for name in ("Get-ChildItem | Remove-Item", "Get-Location; Remove-Item file",
                     "Get-Location -Path C:/Windows"):
            with self.subTest(name=name):
                self.assertNotEqual("ALLOW_CANDIDATE", module.review_event(
                    self.event("PowerShell", {"command": name}))["decision"])

    def test_writes_require_actual_host_and_owner_gate(self):
        for name, args in (
            ("Write", {"file_path": "src/a.py", "content": "print(1)"}),
            ("Edit", {"file_path": "src/a.py", "old_string": "x", "new_string": "y"}),
            ("NotebookEdit", {"notebook_path": "n.ipynb", "new_source": "1"}),
        ):
            with self.subTest(name=name):
                result = module.review_event(self.event(name, args))
                self.assertEqual("REVIEW_REQUIRED", result["decision"])
                self.assertFalse(result["state_written"])
                self.assertFalse(result["hook_registered"])

    def test_unknown_and_malformed_are_never_allow(self):
        result = module.review_event(self.event("ExecDangerous", {"command": "echo hi"}))
        self.assertEqual("BLOCK_RECOMMENDED", result["decision"])
        bad = [
            {"schema_version": 1, "tool_name": "Bash",
             "tool_input": {"command": "git status", "approved": True}},
            {"schema_version": True, "tool_name": "Bash", "tool_input": {"command": "pwd"}},
            self.event("Bash", {"command": 101}),
            self.event("Read", {"path": ""}),
            self.event("Glob", {"pattern": "x" * 1200}),
        ]
        for event in bad:
            with self.subTest(event=str(event)[:80]):
                with self.assertRaises(module.ReviewError):
                    module.review_event(event)

    def test_stateless_duplicate_calls_have_no_side_effects(self):
        payload = self.event("Write", {"path": "src/test.py", "content": "safe"})
        first = module.review_event(payload)
        second = module.review_event(payload)
        self.assertEqual(first, second)
        self.assertEqual(0, first["network_calls"])
        self.assertEqual(0, first["model_calls"])

    def test_cli_output_contains_no_private_command_and_rejects_oversized(self):
        for raw, expected_exit, expected_decision in (
            (json.dumps(self.event("Bash", {"command": "git status"})).encode(),
             0, "ALLOW_CANDIDATE"),
            (json.dumps(self.event("Bash", {"command": "rm -rf private-project"})).encode(),
             0, "BLOCK_RECOMMENDED"),
            (b"not json", 1, "BLOCK_RECOMMENDED"),
            (b"Z" * 16385, 1, "BLOCK_RECOMMENDED"),
        ):
            with self.subTest(size=len(raw)):
                result = subprocess.run([sys.executable, "-B", str(SCRIPT)],
                                        input=raw, capture_output=True, timeout=10)
                self.assertEqual(expected_exit, result.returncode)
                self.assertFalse(result.stderr)
                value = json.loads(result.stdout.decode("utf-8"))
                self.assertEqual(expected_decision, value["decision"])
                self.assertNotIn("private-project", result.stdout.decode())
                self.assertEqual("NOT_VERIFIED", value["host_enforcement"])


if __name__ == "__main__":
    unittest.main()
