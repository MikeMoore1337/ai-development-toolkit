"""Protocol and containment checks for the optional Codex guardrail."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "hooks" / "codex_pretool_gate.py"


class CodexPreToolGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.project = self.root / "project"
        self.project.mkdir()

    def event(self, tool="Bash", payload=None):
        return {"session_id": "test-session", "turn_id": "test-turn",
                "cwd": str(self.project),
                "hook_event_name": "PreToolUse", "tool_use_id": "test-use-1",
                "tool_name": tool,
                "tool_input": {"command": "pwd"} if payload is None else payload}

    def invoke(self, event=None, raw=None, local=True):
        if raw is None:
            raw = json.dumps(event, ensure_ascii=True).encode("utf-8")
        args = [sys.executable, "-B", str(SCRIPT), "--project-root", str(self.project)]
        if local:
            args.append("--assume-local-exec-cwd")
        p = subprocess.run(args,
                           input=raw, capture_output=True, timeout=10)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stderr, b"")
        return json.loads(p.stdout)

    def assert_denied(self, response):
        value = response["hookSpecificOutput"]
        self.assertEqual(value["hookEventName"], "PreToolUse")
        self.assertEqual(value["permissionDecision"], "deny")
        self.assertNotIn("updatedInput", value)

    def test_safe_candidate_defers_without_authorizing(self):
        self.assertEqual({}, self.invoke(self.event()))
        self.assertEqual({}, self.invoke(self.event(payload={"command": "git status --short"})))
        event = self.event(); event.update(agent_id="a", agent_type="worker")
        self.assertEqual({}, self.invoke(event))

    def test_unknown_write_and_risk_are_denied(self):
        for event in (self.event(payload={"command": "rm -rf SECRET_PLACEHOLDER"}),
                      self.event(payload={"command": "echo ambiguous"}),
                      self.event("apply_patch", {"command": "*** Begin Patch\n*** End Patch"}),
                      self.event("mcp__example__write", {"secret": "SECRET_PLACEHOLDER"}),
                      self.event("unknown", {})):
            with self.subTest(tool=event["tool_name"]):
                result = self.invoke(event)
                self.assert_denied(result)
                self.assertNotIn("SECRET_PLACEHOLDER", json.dumps(result))

    def test_missing_effective_workdir_and_outside_are_denied(self):
        self.assert_denied(self.invoke(self.event(), local=False))
        for cwd in (None, str(self.root), str(self.project / "missing"), "../relative"):
            event = self.event()
            if cwd is None:
                del event["cwd"]
            else:
                event["cwd"] = cwd
            with self.subTest(cwd=cwd):
                self.assert_denied(self.invoke(event))
        event = self.event()
        event["cwd"] = str(self.root)
        self.assert_denied(self.invoke(event))

    def test_symlink_escape_is_denied(self):
        target = self.root / "outside"
        target.mkdir()
        link = self.project / "link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symlink unavailable")
        event = self.event()
        event["cwd"] = str(link)
        self.assert_denied(self.invoke(event))

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_windows_junction_escape_is_denied(self):
        target = self.root / "outside"
        target.mkdir()
        link = self.project / "junction"
        proc = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
                              capture_output=True, timeout=10)
        if proc.returncode:
            self.skipTest("junction creation unavailable")
        event = self.event()
        event["cwd"] = str(link)
        self.assert_denied(self.invoke(event))

    def test_invalid_json_duplicate_keys_and_size_are_denied(self):
        for raw in (b"", b"\xff", b"{", b"x" * 65537,
                    b'{"tool_name":"Bash","tool_name":"Other"}',
                    b'{"tool_input":{"command":"pwd","command":"other"}}',
                    b'{"value":NaN}'):
            with self.subTest(raw=raw[:20]):
                self.assert_denied(self.invoke(raw=raw))

    def test_schema_missing_extra_or_untrusted_values_are_denied(self):
        variants = []
        missing = self.event(); del missing["tool_use_id"]; variants.append(missing)
        extra = self.event(); extra["approved"] = True; variants.append(extra)
        fabricated = self.event(); fabricated["tool_cwd"] = str(self.project); variants.append(fabricated)
        wrong = self.event(); wrong["tool_input"] = []; variants.append(wrong)
        surrogate = self.event(); surrogate["tool_name"] = "\ud800"; variants.append(surrogate)
        extra_input = self.event(payload={"command": "pwd", "approved": True}); variants.append(extra_input)
        wrong_event = self.event(); wrong_event["hook_event_name"] = "PostToolUse"; variants.append(wrong_event)
        for event in variants:
            with self.subTest(event=str(event)[:50]):
                self.assert_denied(self.invoke(event))

    def test_duplicate_event_is_stateless_and_does_not_execute(self):
        event = self.event("apply_patch", {"command": "marker-file"})
        before = set(self.project.iterdir())
        self.assertEqual(self.invoke(event), self.invoke(event))
        self.assertEqual(before, set(self.project.iterdir()))


if __name__ == "__main__":
    unittest.main()
