"""Offline, deterministic GateGuard security regressions (#438)."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "hooks" / "pretool_gate_review.py"
spec = importlib.util.spec_from_file_location("native_gate_review_hardening", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GateGuardHardeningTests(unittest.TestCase):
    def event(self, tool, payload):
        return {"schema_version": 1, "tool_name": tool, "tool_input": payload}

    def cmd(self, tool, command):
        return module.review_event(self.event(tool, {"command": command}))

    def cli(self, raw):
        proc = subprocess.run([sys.executable, "-B", str(SCRIPT)],
                              input=raw, capture_output=True, timeout=5)
        self.assertEqual(proc.stderr, b"")
        result = json.loads(proc.stdout)
        for field in ("blocking_effect", "host_enforcement", "hook_registered",
                      "tool_executed", "state_written", "owner_authorization"):
            self.assertIn(field, result)
        self.assertEqual(result["host_enforcement"], "NOT_VERIFIED")
        self.assertEqual(result["blocking_effect"], "NONE_SOURCE_ONLY")
        self.assertFalse(result["state_written"])
        self.assertFalse(result["tool_executed"])
        return proc.returncode, result

    def test_known_destructive_and_alias_variants(self):
        cases = [("Bash", "git -C .. reset --hard HEAD"),
                 ("Bash", "git --git-dir=/tmp/repo/.git clean --force"),
                 ("Bash", "git worktree remove --force /tmp/wt"),
                 ("Bash", "git push -f origin main"),
                 ("Bash", "rm --recursive tmp"),
                 ("Bash", "git branch -D old"),
                 ("Bash", "git status && rm -rf tmp"),
                 ("Bash", "echo $(rm -rf tmp)"),
                 ("PowerShell", "ri -Recurse test"),
                 ("PowerShell", "GET-LOCATION; remove-item -force a"),
                 ("PowerShell", "Get-ChildItem | Remove-Item")]
        for tool, command in cases:
            with self.subTest(tool=tool, command=command):
                self.assertEqual(self.cmd(tool, command)["decision"], "BLOCK_RECOMMENDED")

    def test_inert_quotes_are_not_known_destruction(self):
        for tool, command in [("Bash", 'echo "rm -rf project"'),
                              ("Bash", "echo git reset --hard HEAD"),
                              ("Bash", 'printf "DELETE FROM rows"'),
                              ("PowerShell", 'Write-Output "Remove-Item"'),
                              ("PowerShell", 'Write-Output "DROP TABLE t"')]:
            with self.subTest(command=command):
                self.assertEqual(self.cmd(tool, command)["decision"], "REVIEW_REQUIRED")

    def test_only_canonical_readonly_commands_are_candidates(self):
        for tool, command in [("Bash", "git status"), ("Bash", "git  status  "),
                              ("Bash", "git diff --check"), ("Bash", "pwd"),
                              ("PowerShell", "Get-Location"),
                              ("PowerShell", "get-location")]:
            self.assertEqual(self.cmd(tool, command)["decision"], "ALLOW_CANDIDATE")
        for tool, command in [("Bash", 'git "status"'),
                              ("Bash", r"git statu\s"),
                              ("Bash", "git status && echo hello"),
                              ("Bash", "git status\nls"),
                              ("Bash", "git status $(false)"),
                              ("PowerShell", "Get-Location; echo 1"),
                              ("PowerShell", "Get-Location($false)"),
                              ("PowerShell", "get-location -Path /")]:
            with self.subTest(command=command):
                self.assertNotEqual(self.cmd(tool, command)["decision"], "ALLOW_CANDIDATE")

    def test_readonly_schema_is_tool_specific(self):
        for tool, payload in [("Read", {"path": "src/foo.py"}),
                              ("Grep", {"pattern": "TODO"}),
                              ("Glob", {"pattern": "*.py"})]:
            self.assertEqual(module.review_event(self.event(tool, payload))["decision"],
                             "ALLOW_CANDIDATE")
        for tool, payload in [("Read", {"pattern": "src/foo.py"}),
                              ("Grep", {"path": "README.md"}),
                              ("Glob", {"path": "foo"}),
                              ("Read", {"path": "x\x00y"}),
                              ("Read", {"path": "x\ny"}),
                              ("Read", {"path": "\ud800"}),
                              ("Grep", {"pattern": "x" * 1025}),
                              ("Read", {"path": 22})]:
            with self.subTest(tool=tool, payload=str(payload)[:20]):
                with self.assertRaises(module.ReviewError):
                    module.review_event(self.event(tool, payload))

    def test_invalid_shell_input_and_versions(self):
        for event in [self.event("Bash", {"command": "    "}),
                      self.event("Bash", {"command": "pwd\x00git status"}),
                      self.event("Bash", {"command": "\ud800"}),
                      self.event("Bash", {"command": '"unterminated'}),
                      self.event("Bash", {"command": "pwd", "approved": True}),
                      {"schema_version": True, "tool_name": "Bash",
                       "tool_input": {"command": "pwd"}}]:
            with self.subTest(event=str(event)[:30]):
                with self.assertRaises(module.ReviewError):
                    module.review_event(event)

    def test_duplicate_and_nonstandard_json_fail_closed(self):
        raws = [
            b'{"schema_version":1,"tool_name":"Bash","tool_name":"Read","tool_input":{"path":"ok"}}',
            b'{"schema_version":1,"tool_name":"Bash","tool_input":{"command":"rm -rf stuff","command":"git status"}}',
            b'{"schema_version":1,"tool_name":"Bash","tool_input":{"command":"git status","extra":NaN}}',
            b'{"schema_version":1,"tool_name":"Bash","tool_input":{"command":Infinity}}',
            b"\xff", b'{"schema_version":1,"tool_name":"Read",', b"", b"x" * 16385,
        ]
        for raw in raws:
            with self.subTest(raw=raw[:35]):
                exit_code, result = self.cli(raw)
                self.assertEqual(exit_code, 1)
                self.assertEqual(result["decision"], "BLOCK_RECOMMENDED")
                self.assertNotIn("stuff", json.dumps(result))

    def test_bounded_cli_no_secrets_and_idempotence(self):
        payload = json.dumps(self.event("Bash", {"command": "git status"})).encode()
        ret1, first = self.cli(payload)
        ret2, second = self.cli(payload)
        self.assertEqual((ret1, ret2), (0, 0))
        self.assertEqual(first, second)
        self.assertEqual(first["decision"], "ALLOW_CANDIDATE")
        self.assertEqual(first["network_calls"], 0)
        self.assertEqual(first["model_calls"], 0)
        for command in ("rm -rf SUPER_SECRET_VALUE",
                        "git status; echo SUPER_SECRET_VALUE"):
            _status, response = self.cli(json.dumps(self.event(
                "Bash", {"command": command})).encode())
            self.assertNotIn("SUPER_SECRET_VALUE", json.dumps(response))

    def test_api_no_open_network_or_subprocess_calls(self):
        with (patch("builtins.open", side_effect=AssertionError("opened file")),
              patch("socket.socket", side_effect=AssertionError("network")),
              patch("subprocess.Popen", side_effect=AssertionError("process"))):
            out = self.cmd("Bash", "git status")
            self.assertEqual(out["decision"], "ALLOW_CANDIDATE")

    def test_quote_embedded_shell_metacharacters_need_review(self):
        for tool, command in (
            ("Bash", 'echo "notice; rm -rf folder"'),
            ("Bash", "printf 'shown; git reset --hard HEAD'"),
            ("Bash", "echo '$(rm -rf folder)'"),
            ("Bash", 'echo "audit; git push --force origin main"'),
            ("PowerShell", 'Write-Output "audit; Remove-Item -Recurse x"'),
            ("PowerShell", "Write-Output 'text | Remove-Item -Recurse x'"),
        ):
            with self.subTest(tool=tool, command=command):
                self.assertEqual(self.cmd(tool, command)["decision"], "REVIEW_REQUIRED")
        for tool, command in (
            ("Bash", "git status && rm -rf folder"),
            ("Bash", 'rm -rf "file;name"'),
            ("Bash", "echo $(rm -rf folder)"),
            ("PowerShell", 'Remove-Item -Path "a;b"'),
            ("PowerShell", "Get-ChildItem | Remove-Item"),
        ):
            with self.subTest(tool=tool, command=command):
                self.assertEqual(self.cmd(tool, command)["decision"], "BLOCK_RECOMMENDED")

    def test_sensitive_file_reads_require_owner_and_host_review(self):
        for tool, value in (
            ("Read", ".env"),
            ("Read", "src/.env.production"),
            ("Read", "../outside/file.txt"),
            ("Read", "C:\\Users\\test\\.ssh\\id_rsa"),
            ("Read", "config/service_account.json"),
            ("Read", "keys/private.pem"),
            ("Glob", "**/.aws/**"),
            ("Glob", "**/.env"),
            ("Glob", "**/*.p12"),
        ):
            with self.subTest(tool=tool, value=value):
                payload = {"path" if tool == "Read" else "pattern": value}
                out = module.review_event(self.event(tool, payload))
                self.assertEqual(out["decision"], "REVIEW_REQUIRED")
                self.assertEqual(out["reason_code"], "SENSITIVE_OR_OUT_OF_SCOPE_PATH")
                self.assertNotIn(value, json.dumps(out))
        for tool, value in (
            ("Read", "src/app.py"),
            ("Read", ".env.example"),
            ("Glob", "**/*.py"),
            ("Glob", "src/.env.template"),
            ("Grep", r"\.env"),
        ):
            with self.subTest(tool=tool, value=value):
                payload = {"path" if tool == "Read" else "pattern": value}
                self.assertEqual(module.review_event(self.event(tool, payload))["decision"],
                                 "ALLOW_CANDIDATE")

    def test_cli_catches_recursion_error_no_traceback(self):
        with patch.object(module.json, "loads", side_effect=RecursionError):
            fake_input = type("BytesInput", (), {"read": lambda _self, _size: b"{}"})()
            fake_stdin = type("Stdin", (), {"buffer": fake_input})()
            from io import StringIO
            with (patch.object(module.sys, "stdin", fake_stdin),
                  patch.object(module.sys, "stdout", new_callable=StringIO) as out):
                self.assertEqual(module.main(), 1)
                output = out.getvalue()
        self.assertEqual(json.loads(output)["decision"], "BLOCK_RECOMMENDED")


if __name__ == "__main__":
    unittest.main()
