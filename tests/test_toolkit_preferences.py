"""No-execution, scoped preference resolution and denial oracles (#394)."""
from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import toolkit_preferences as prefs


class LayeredPreferencesTests(unittest.TestCase):
    def layer(self, **changes):
        return {"schema_version": 1, **changes}

    def test_missing_settings_are_readonly_and_deny_real_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / "project"
            target.mkdir()
            with patch.object(prefs, "user_config_path", return_value=root / "absent.json"):
                before = list(root.rglob("*"))
                report = prefs.preview(target)
                self.assertEqual(before, list(root.rglob("*")))
            self.assertEqual("READ_ONLY_PREFERENCES_PREVIEW", report["classification"])
            self.assertFalse(report["effective"]["execution"]["real_agent_pilots"])
            self.assertFalse(report["effective"]["execution"]["allow_paid_api"])
            self.assertFalse(report["execution_authorized"])
            self.assertTrue(report["per_task_consent_required"])
            self.assertEqual(0, report["model_calls"])

    def test_user_opt_in_not_execution_permission(self):
        user = self.layer(
            clients={"preferred": "codex-cli", "allowed": ["codex-cli", "chatgpt"]},
            execution={"allow_cli_agents": True, "real_agent_pilots": True},
            language="ru",
        )
        result = prefs.resolve(user)
        self.assertEqual("codex-cli", result["effective"]["clients"]["preferred"])
        self.assertTrue(result["effective"]["execution"]["allow_cli_agents"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual("user", result["sources"]["execution.allow_cli_agents"])

    def test_scope_can_tighten_but_not_reenable_user_denial(self):
        user = self.layer(execution={"allow_cli_agents": True, "allow_network": True},
                          approvals={"deployment": "ask"},
                          skills={"excluded": ["ui-motion"]})
        project = self.layer(execution={"allow_network": False},
                             approvals={"deployment": "deny"},
                             skills={"excluded": ["motion-quality"]})
        task = self.layer(execution={"allow_cli_agents": False},
                          skills={"excluded": ["ui-motion", "qa-ci"]})
        result = prefs.resolve(user, project, task)
        self.assertEqual(["motion-quality", "qa-ci", "ui-motion"],
                         result["effective"]["skills"]["excluded"])
        self.assertEqual("deny", result["effective"]["approvals"]["deployment"])
        self.assertFalse(result["effective"]["execution"]["allow_network"])
        self.assertFalse(result["effective"]["execution"]["allow_cli_agents"])
        with self.assertRaisesRegex(prefs.PreferencesError, "cannot enable"):
            prefs.resolve(self.layer(), self.layer(execution={"allow_paid_api": True}))
        with self.assertRaisesRegex(prefs.PreferencesError, "cannot enable"):
            prefs.resolve(self.layer(), None, self.layer(execution={"allow_network": True}))
        with self.assertRaisesRegex(prefs.PreferencesError, "cannot loosen"):
            prefs.resolve(self.layer(approvals={"file_writes": "deny"}),
                          self.layer(approvals={"file_writes": "ask"}))

    def test_paid_api_requires_spend_opt_in_and_still_no_invocation(self):
        with self.assertRaisesRegex(prefs.PreferencesError, "Paid API"):
            prefs.resolve(self.layer(execution={"allow_paid_api": True}))
        report = prefs.resolve(self.layer(execution={
            "allow_paid_api": True, "additional_spend_allowed": True,
        }))
        self.assertTrue(report["effective"]["execution"]["allow_paid_api"])
        self.assertFalse(report["execution_authorized"])

    def test_client_whitelist_may_only_narrow(self):
        user = self.layer(clients={"allowed": ["chatgpt", "codex-desktop"]})
        narrowed = prefs.resolve(user, self.layer(clients={"allowed": ["chatgpt"]}))
        self.assertEqual(["chatgpt"], narrowed["effective"]["clients"]["allowed"])
        with self.assertRaisesRegex(prefs.PreferencesError, "cannot add"):
            prefs.resolve(user, self.layer(clients={"allowed": ["codex-cli"]}))
        with self.assertRaisesRegex(prefs.PreferencesError, "Preferred client"):
            prefs.resolve(self.layer(clients={"preferred": "codex-desktop"}),
                          self.layer(clients={"allowed": ["chatgpt"]}))

    def test_unknown_secrets_and_wrong_types_are_refused(self):
        bad = (
            {"schema_version": 1, "api_key": "not-a-real-key"},
            self.layer(execution={"OPENAI_API_KEY": "abc"}),
            self.layer(execution={"allow_paid_api": "true"}),
            self.layer(approvals={"git_merge": "allow"}),
            self.layer(clients={"allowed": ["chatgpt", "chatgpt"]}),
            {"schema_version": 2},
            self.layer(skills={"excluded": ["../../secret"]}),
            self.layer(language="xx"),
        )
        for item in bad:
            with self.subTest(item=item), self.assertRaises(prefs.PreferencesError):
                prefs.resolve(item)

    def test_cli_does_not_write_and_does_not_expose_file_contents(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            project = root / "project"
            (project / ".adt").mkdir(parents=True)
            (project / ".adt" / "config.json").write_text(
                json.dumps(self.layer(approvals={"deployment": "deny"})), encoding="utf-8")
            user = root / "user.json"
            user.write_text(json.dumps(self.layer(language="ru")), encoding="utf-8")
            original = {p.relative_to(root).as_posix(): p.read_bytes()
                        for p in root.rglob("*") if p.is_file()}
            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = prefs.main(["--target", str(project), "--user-config", str(user)])
            self.assertEqual(0, code, stderr.getvalue())
            self.assertEqual(original, {p.relative_to(root).as_posix(): p.read_bytes()
                                        for p in root.rglob("*") if p.is_file()})
            report = json.loads(stdout.getvalue())
            self.assertEqual("ru", report["effective"]["language"])
            self.assertEqual("deny", report["effective"]["approvals"]["deployment"])
            self.assertNotIn(str(user), stdout.getvalue())
            self.assertNotIn(str(project), stdout.getvalue())

    def test_file_and_parent_symlink_are_denied(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            real = root / "real.json"
            real.write_text('{"schema_version":1}', encoding="utf-8")
            link = root / "link.json"
            try:
                link.symlink_to(real)
            except OSError:
                self.skipTest("symlink unavailable")
            with self.assertRaisesRegex(prefs.PreferencesError, "Linked"):
                prefs.read_optional(link, "user")

    def test_bad_encoding_oversize_and_missing_explicit_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bad = root / "bad.json"
            bad.write_bytes(b"\\xff\\xfe")
            with self.assertRaises(prefs.PreferencesError):
                prefs.read_optional(bad, "user")
            bad.write_bytes(b" " * (prefs.MAX_BYTES + 1))
            with self.assertRaisesRegex(prefs.PreferencesError, "64KiB"):
                prefs.read_optional(bad, "user")
            with self.assertRaises(prefs.PreferencesError):
                prefs.read_optional(root / "missing.json", "user", required=True)


if __name__ == "__main__":
    unittest.main()
