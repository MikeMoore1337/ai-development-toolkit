"""Offline negative and recovery tests for opt-in Issue Supervisor (#570)."""
from __future__ import annotations

from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import issue_supervisor as sup  # noqa: E402
import issue_supervisor_sdk as sdk  # noqa: E402


REPO = "example/toolkit"


def policy(root: Path, **override):
    checkout = root / "checkout"
    checkout.mkdir(exist_ok=True)
    (checkout / ".git").mkdir(exist_ok=True)
    p = {
        "schema": 1, "repo": REPO, "branch": "main",
        "issues": [1, 2, 3], "checkout": str(checkout),
        "max_issues": 3, "max_turns": 6, "max_attempts_per_issue": 2,
        "max_turn_seconds": 90, "poll_seconds": 2,
        "sdk_runtime_acknowledged": True,
        "chatgpt_included_usage_confirmed": True,
        "allow_merge": False,
    }
    p.update(override)
    return p


class SupervisorPolicyTests(unittest.TestCase):
    def test_init_is_safe_by_default_and_no_runtime_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = policy(root)
            self.assertEqual(p, sup.validate_policy(p))
            self.assertEqual("PAUSED", sup.initial_state(p)["mode"])
            self.assertEqual([], sup.initial_state(p)["finished"])
            self.assertEqual("NEW", sup.initial_state(p)["stage"])

    def test_scope_limits_and_consent_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = policy(Path(tmp))
            mutations = [
                ({"repo": "../danger"}, "INVALID_REPOSITORY"),
                ({"branch": "../main"}, "INVALID_BRANCH"),
                ({"issues": [1, 1, 2]}, "INVALID_SCOPE"),
                ({"issues": []}, "INVALID_SCOPE"),
                ({"issues": [2, 1, 3]}, "INVALID_SCOPE"),
                ({"issues": [True, 2]}, "INVALID_SCOPE"),
                ({"max_issues": 5}, "UNSAFE_BUDGET"),
                ({"max_turns": 0}, "INVALID_LIMIT_MAX_TURNS"),
                ({"max_attempts_per_issue": 100}, "INVALID_LIMIT_MAX_ATTEMPTS_PER_ISSUE"),
                ({"chatgpt_included_usage_confirmed": "true"}, "INVALID_CONSENT_FLAG"),
            ]
            for update, error in mutations:
                with self.subTest(update=update):
                    with self.assertRaisesRegex(sup.SupervisorError, error):
                        sup.validate_policy({**p, **update})

    def test_private_state_preserves_locks_and_atomic_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data"
            sup.prepare_root(root)
            target = root / "supervisor.json"
            sup.atomic_json(target, {"schema": 1, "message": "safe"})
            self.assertEqual("safe", sup.load_json(target)["message"])
            with sup.single_writer(root):
                with self.assertRaisesRegex(sup.SupervisorError, "SUPERVISOR_ALREADY_RUNNING"):
                    with sup.single_writer(root):
                        pass
            with sup.single_writer(root):
                pass

    def test_state_and_scope_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = policy(Path(tmp))
            root = Path(tmp) / "data"
            sup.prepare_root(root)
            st = sup.initial_state(p)
            sup.atomic_json(root / "supervisor.json", st)
            self.assertEqual("PAUSED", sup.read_runtime(root, p)["mode"])
            with self.assertRaisesRegex(sup.SupervisorError, "STATE_CONTEXT_OR_SCHEMA_MISMATCH"):
                sup.read_runtime(root, {**p, "issues": [2, 3]})
            st["mode"] = "UNTRUSTED_MODE"
            sup.atomic_json(root / "supervisor.json", st)
            with self.assertRaisesRegex(sup.SupervisorError, "STATE_CONTEXT_OR_SCHEMA_MISMATCH"):
                sup.read_runtime(root, p)

    def test_api_credentials_refused_before_live_calls(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "unused-synthetic"}, clear=False):
            with self.assertRaisesRegex(sup.SupervisorError, "API_KEY_ENVIRONMENT_REFUSED"):
                sup.assert_no_api_credentials()

    def test_sdk_auth_not_guessed_from_non_chatgpt_account(self):
        self.assertFalse(sdk.account_is_chatgpt(SimpleNamespace(account=None)))
        self.assertFalse(sdk.account_is_chatgpt(SimpleNamespace(
            account=SimpleNamespace(type="apiKey"))))
        self.assertTrue(sdk.account_is_chatgpt(SimpleNamespace(
            account=SimpleNamespace(type="chatgpt"))))

    def test_same_user_windows_sdk_runner_is_unconditionally_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            instance = sdk.CodexSDKRunner(policy(Path(tmp)))
            with self.assertRaisesRegex(sdk.SDKDenied, "OS_SEPARATED_WORKER_NOT_ATTESTED"):
                instance.verify_isolation()

    def test_direct_worker_bypass_is_refused_before_sdk_import(self):
        with self.assertRaisesRegex(sdk.SDKDenied, "OS_SEPARATED_WORKER_NOT_ATTESTED"):
            sdk.execute_worker({"action": "preflight",
                                "runtime_acknowledged": True,
                                "included_usage_confirmed": True})

    def test_prompt_never_grants_agent_push_or_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = policy(Path(tmp))
            prompt = sup.make_prompt(p, 2, None)
            self.assertIn("Do not push", prompt)
            self.assertIn("Do not", prompt)
            self.assertIn("privileged publisher", prompt)
            self.assertIn("Issue #2", prompt)
            self.assertNotIn("run gh pr merge", prompt)


class StubRunner:
    def __init__(self, *, denied=False):
        self.denied = denied
        self.calls = []

    def verify_isolation(self):
        self.calls.append("isolation")
        if self.denied:
            raise sdk.SDKDenied("OS_SEPARATED_WORKER_NOT_ATTESTED")

    def preflight(self):
        self.calls.append("preflight")

    def turn(self, number, prompt, thread_id, timeout, worktree):
        self.calls.append("turn")
        return {"status": "completed", "thread_id": "stub-local-thread-123"}


class SupervisorStepTests(unittest.TestCase):
    def _setup(self, tmp):
        root = Path(tmp) / "data"
        sup.prepare_root(root)
        p = policy(Path(tmp))
        st = sup.initial_state(p)
        st["mode"] = "RUNNING"
        return p, root, st

    def test_isolation_gate_denies_before_queue_and_worker_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, root, st = self._setup(tmp)
            runner = StubRunner(denied=True)
            with patch.object(sup, "github_owner", return_value="example"), \
                    patch.object(sup, "controller") as ctl:
                with self.assertRaisesRegex(sdk.SDKDenied, "OS_SEPARATED_WORKER_NOT_ATTESTED"):
                    sup.step(p, root, st, runner)
                ctl.assert_not_called()
                self.assertEqual(["isolation"], runner.calls)

    def test_synthetic_single_claim_and_durable_turn_accounting(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, root, st = self._setup(tmp)
            runner = StubRunner()

            def fake_ctl(_policy, action, **kwargs):
                if action == "status":
                    return {"active": None}
                if action == "plan":
                    return {"available": [{"number": 1}],
                            "complete": False, "excluded": []}
                if action == "start":
                    return {"status": "CLAIMED", "issue": 1}
                raise AssertionError(action)

            with patch.object(sup, "github_owner", return_value="example"), \
                    patch.object(sup, "controller", side_effect=fake_ctl), \
                    patch.object(sup, "sync_checkout"), \
                    patch.object(sup, "issue_worktree", return_value=str(Path(tmp) / "worktrees" / "1")):
                out = sup.step(p, root, st, runner)
            self.assertEqual("TURN_COMPLETED", out["status"])
            self.assertEqual(1, st["active"])
            self.assertEqual(1, st["turns_used"])
            self.assertEqual({"1": 1}, st["issue_attempts"])
            self.assertEqual("TURN_DONE", st["stage"])
            self.assertEqual("stub-local-thread-123", st["thread_id"])
            self.assertEqual("TURN_DONE", sup.load_json(sup.state_file(root))["stage"])

    def test_external_active_writer_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, root, st = self._setup(tmp)
            with patch.object(sup, "github_owner", return_value="example"), \
                    patch.object(sup, "controller", return_value={"active": 2}):
                with self.assertRaisesRegex(sup.SupervisorError, "FOREIGN_ACTIVE_QUEUE_WRITER"):
                    sup.step(p, root, st, StubRunner())

    def test_in_flight_crash_blocks_redispatch_without_duplicate_turn(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, root, st = self._setup(tmp)
            st.update(stage="TURN_IN_FLIGHT", active=1, turns_used=1)
            with patch.object(sup, "github_owner", return_value="example"), \
                    patch.object(sup, "controller", return_value={"active": 1}), \
                    patch.object(sup, "associated_pr", return_value=None):
                out = sup.step(p, root, st, StubRunner())
            self.assertEqual("RECONCILIATION_REQUIRED", out["status"])
            self.assertEqual(1, st["turns_used"])
            self.assertEqual("RECONCILIATION_REQUIRED", st["stage"])
            self.assertEqual(1, sup.load_json(sup.state_file(root))["active"])

    def test_open_pr_never_merges_without_review_publisher_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, root, st = self._setup(tmp)
            st.update(stage="TURN_DONE", active=1, turns_used=1)
            with patch.object(sup, "github_owner", return_value="example"), \
                    patch.object(sup, "controller", return_value={"active": 1}) as ctl, \
                    patch.object(sup, "associated_pr", return_value=4):
                out = sup.step(p, root, st, StubRunner())
            self.assertEqual("NEEDS_HUMAN", out["status"])
            self.assertIn("INDEPENDENT_REVIEW", out["reason"])
            ctl.assert_called_once()
            self.assertEqual("status", ctl.call_args.args[1])
            self.assertEqual("RECONCILIATION_REQUIRED", st["stage"])

    def test_stopped_process_does_not_call_github(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, root, st = self._setup(tmp)
            (root / "STOP").write_text("STOP\n")
            with patch.object(sup, "github_owner") as owner:
                out = sup.step(p, root, st, StubRunner())
            self.assertEqual("STOPPED", out["status"])
            owner.assert_not_called()

    def test_scope_max_issues_stops_early(self):
        with tempfile.TemporaryDirectory() as tmp:
            p, root, st = self._setup(tmp)
            st["finished"] = [1, 2, 3]
            with patch.object(sup, "github_owner", return_value="example"), \
                    patch.object(sup, "controller", return_value={"active": None}):
                out = sup.step(p, root, st, StubRunner())
            self.assertEqual("DONE", out["status"])
            self.assertEqual("DONE", st["stage"])


class HostGitIsolationTests(unittest.TestCase):
    def test_real_synthetic_worktree_shares_expected_git_dir(self):
        import subprocess
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "checkout"
            repo.mkdir()
            for command in (["git", "init", "-b", "main"],
                            ["git", "config", "user.name", "Local Test"],
                            ["git", "config", "user.email", "local-test@example.invalid"]):
                p = subprocess.run(command, cwd=repo, capture_output=True, text=True)
                self.assertEqual(0, p.returncode, p.stderr)
            (repo / "README.md").write_text("Fixture only\n", encoding="utf-8")
            for command in (["git", "add", "--", "README.md"],
                            ["git", "commit", "-m", "test: seed"]):
                p = subprocess.run(command, cwd=repo, capture_output=True, text=True)
                self.assertEqual(0, p.returncode, p.stderr)
            p = policy(root, checkout=str(repo))
            state_dir = root / "host-state"
            state_dir.mkdir()
            worktree = Path(sup.issue_worktree(p, state_dir, 2))
            self.assertTrue(worktree.is_dir())
            self.assertEqual("issue-orchestrator/issue-2-supervised",
                             sup.scrubbed_argv(["git", "-C", str(worktree),
                                               "branch", "--show-current"]))
            self.assertEqual(str(worktree), sup.issue_worktree(p, state_dir, 2))
            with self.assertRaisesRegex(sup.SupervisorError,
                                        "EXECUTOR_COMMAND_FAILED"):
                (worktree / ".git").rename(worktree / ".git.backup")
                try:
                    sup.issue_worktree(p, state_dir, 2)
                finally:
                    (worktree / ".git.backup").rename(worktree / ".git")

    def test_pr_ownership_and_duplicates_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            p = policy(Path(temp))
            def pr(number, branch, body, base="main"):
                return {"number": number, "headRefName": branch,
                        "body": body, "baseRefName": base}
            candidate = pr(13, "issue-orchestrator/issue-1-supervised", "Closes #1")
            with patch.object(sup.queue, "gh_json", return_value=[candidate]):
                self.assertEqual(13, sup.associated_pr(p, 1))
                self.assertIsNone(sup.associated_pr(p, 2))
            with patch.object(sup.queue, "gh_json", return_value=[
                    candidate, pr(14, "issue-orchestrator/issue-1-other", "Closes #1")]):
                with self.assertRaisesRegex(sup.SupervisorError, "AMBIGUOUS_ISSUE_PR"):
                    sup.associated_pr(p, 1)
            with patch.object(sup.queue, "gh_json", return_value=[
                    pr(15, "issue-orchestrator/issue-1-supervised", "See #1")]):
                self.assertIsNone(sup.associated_pr(p, 1))

    def test_corrupt_usage_counts_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = policy(root)
            sup.prepare_root(root / "state")
            st = sup.initial_state(p)
            for field, value in (
                ("issue_attempts", {"1": -1}),
                ("issue_attempts", {"4": 1}),
                ("issue_attempts", {"2": True}),
                ("finished", [1, 1]),
                ("finished", [4]),
                ("turns_used", 300),
            ):
                with self.subTest(field=field, value=value):
                    mutated = {**st, field: value}
                    sup.atomic_json(root / "state" / "supervisor.json", mutated)
                    with self.assertRaisesRegex(sup.SupervisorError,
                                                "CORRUPT_USAGE"):
                        sup.read_runtime(root / "state", p)

    def test_resident_run_action_is_not_a_disguised_single_step(self):
        from io import StringIO
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            p = policy(base)
            root = base / "host-state"
            sup.prepare_root(root)
            sup.atomic_json(root / "policy.json", p)
            sup.atomic_json(root / "supervisor.json", sup.initial_state(p))
            args = ["run", "--repo", REPO, "--state-dir", str(root)]
            output = StringIO()
            with patch("sys.stdout", output):
                code = sup.main(args)
            self.assertEqual(2, code)
            self.assertEqual("REFUSED", json.loads(output.getvalue())["status"])
            self.assertIn("PERSISTENT_SUPERVISOR_NOT_IMPLEMENTED",
                          output.getvalue())
            self.assertEqual("PAUSED", sup.load_json(root / "supervisor.json")["mode"])


if __name__ == "__main__":
    unittest.main()
