"""Source-only Hermes interop regression tests. No agent, network or API calls."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from agent_eval_hermes_contract import inspect_hermes, FLAGS


def fake_hermes(root: Path) -> str:
    files = {
        "eval_lane/protocol.py": """
KIND = "adt_skill_eval_pilot_v1"
CASES = frozenset({"python-api", "javascript-ui", "go-cli"})
PROVIDERS = frozenset({"codex", "claude"})
""",
        "eval_lane/fixed_plan.py": """
def fixed_plan(job):
    checked = job
    argv = (
        "/python", "/kit/scripts/agent_eval_runner.py",
        "--provider", checked["provider"], "--model", checked["model"],
        "--cases", *checked["case_ids"], "--trials", str(checked["trials"]),
        "--max-seconds", str(checked["timeout_seconds"]),
        "--output", "/tmp/output",
        "--execute", "--acknowledge-costs", "--acknowledge-isolation",
    )
    return argv
""",
        "eval_lane/local_executor.py": """
class LocalBoundedExecutor:
    def __call__(self, job):
        self._preflight()
        assert_owner_real_execution_allowed()
        plan = fixed_plan(job)
        return plan
""",
        "eval_lane/owner_spend_lock.py": """
OWNER_REAL_AGENT_EXECUTION_LOCKED = True
""",
    }
    for name, source in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    commands = [
        ["git", "init", "-q"],
        ["git", "add", "."],
        ["git", "-c", "user.name=Offline Test", "-c", "user.email=test@invalid.example",
         "-c", "commit.gpgsign=false", "commit", "-qm", "synthetic contract"],
        ["git", "rev-parse", "HEAD"],
    ]
    for command in commands:
        proc = subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)
    return proc.stdout.strip()


class HermesContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.pin = fake_hermes(self.root)

    def assert_denied(self, expression: str):
        with self.assertRaisesRegex(ValueError, expression):
            inspect_hermes(self.root, expected_sha=self.pin)

    def test_compatible_source_is_not_a_model_result(self):
        result = inspect_hermes(self.root, expected_sha=self.pin)
        self.assertEqual(result["argv_contract"], "MATCH")
        self.assertEqual(result["real_agent_trials"], 0)
        self.assertEqual(result["real_agent_outcomes"], "NOT_MEASURED")
        self.assertEqual(result["provider_calls"], 0)
        self.assertEqual(len(FLAGS), 9)
        self.assertNotIn("accepted", json.dumps(result))

    def test_unexpected_commit_and_dirty_worktree_fail(self):
        self.assert_denied_after_wrong_sha()
        source = self.root / "eval_lane" / "protocol.py"
        source.write_text(source.read_text(encoding="utf-8") + "\n# tamper\n",
                          encoding="utf-8")
        self.assert_denied("hermes_checkout_dirty")

    def assert_denied_after_wrong_sha(self):
        with self.assertRaisesRegex(ValueError, "hermes_sha_mismatch"):
            inspect_hermes(self.root, expected_sha="f" * 40)

    def test_unknown_case_and_provider_drift_fail_after_repin(self):
        protocol = self.root / "eval_lane" / "protocol.py"
        value = protocol.read_text(encoding="utf-8")
        for old, new, failure in (
            ('"go-cli"', '"unknown-cli"', "hermes_case_registry_drift"),
            ('"claude"', '"unapproved-provider"', "hermes_provider_registry_drift"),
        ):
            with self.subTest(new=new):
                protocol.write_text(value.replace(old, new), encoding="utf-8")
                self.recommit()
                self.assert_denied(failure)
        protocol.write_text(value, encoding="utf-8")

    def test_missing_lock_and_unsafe_argv_fail_after_repin(self):
        lock = self.root / "eval_lane" / "owner_spend_lock.py"
        lock.write_text("OWNER_REAL_AGENT_EXECUTION_LOCKED = False\n",
                        encoding="utf-8")
        self.recommit()
        self.assert_denied("owner_execution_freeze_removed")
        lock.write_text("OWNER_REAL_AGENT_EXECUTION_LOCKED = True\n",
                        encoding="utf-8")
        plan = self.root / "eval_lane" / "fixed_plan.py"
        plan.write_text(plan.read_text(encoding="utf-8").replace(
            '"--execute"', '"--dangerously-skip-permissions"'), encoding="utf-8")
        self.recommit()
        self.assert_denied("hermes_cli_flags_drift")

    def test_guard_order_and_symlink_source_fail(self):
        adapter = self.root / "eval_lane" / "local_executor.py"
        adapter.write_text(adapter.read_text(encoding="utf-8").replace(
            "        assert_owner_real_execution_allowed()\n", ""), encoding="utf-8")
        self.recommit()
        self.assert_denied("hermes_execution_guard_moved")
        adapter.write_text(
            "class LocalBoundedExecutor:\n"
            "    def __call__(self, job):\n"
            "        self._preflight()\n"
            "        assert_owner_real_execution_allowed()\n"
            "        return None\n", encoding="utf-8")
        # A symlink is refused even if a corresponding Git object could be pinned.
        src = self.root / "eval_lane" / "protocol.py"
        original = src.read_text(encoding="utf-8")
        src.unlink()
        target = self.root / "outside-source.txt"
        target.write_text(original, encoding="utf-8")
        try:
            src.symlink_to(target)
        except OSError:
            self.skipTest("Symlinks unavailable")
        self.recommit()
        self.assert_denied("unsafe_or_missing_source")

    def recommit(self):
        for cmd in (
            ["git", "add", "-A"],
            ["git", "-c", "user.name=Offline Test",
             "-c", "user.email=test@invalid.example",
             "-c", "commit.gpgsign=false", "commit", "-qm", "changed fixture"],
            ["git", "rev-parse", "HEAD"],
        ):
            p = subprocess.run(cmd, cwd=self.root, check=True,
                               capture_output=True, text=True)
        self.pin = p.stdout.strip()


if __name__ == "__main__":
    unittest.main()
