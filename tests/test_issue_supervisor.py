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

    def test_one_issue_scope_defaults_to_one_max_issue_without_model_run(self):
        from io import StringIO
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            checkout = base / "checkout"
            checkout.mkdir()
            (checkout / ".git").mkdir()
            directory = base / "host-state"
            output = StringIO()
            args = ["init", "--repo", REPO, "--branch", "main",
                    "--checkout", str(checkout), "--state-dir", str(directory),
                    "--issues", "1"]
            with patch("sys.stdout", output):
                result = sup.main(args)
            self.assertEqual(0, result, output.getvalue())
            self.assertEqual("INITIALIZED_PAUSED",
                             json.loads(output.getvalue())["status"])
            installed_policy = sup.load_json(directory / "policy.json")
            self.assertEqual([1], installed_policy["issues"])
            self.assertEqual(1, installed_policy["max_issues"])
            self.assertEqual("PAUSED",
                             sup.load_json(directory / "supervisor.json")["mode"])

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
            self.assertEqual("QUEUE_STOPPED_AT_LIMIT", out["status"])
            self.assertEqual("QUOTA_BLOCKED", st["stage"])


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


class QueueTerminalAuditTests(unittest.TestCase):
    def make_snapshot(self, states):
        rows = []
        for n, state in enumerate(states, 1):
            body = f"Depends on #{n-1}" if n > 1 else ""
            rows.append({"number": n, "title": f"[P{n-1}] Task {n}",
                         "state": state, "body": body, "labels": []})
        return {"issues": rows, "pull_requests": []}

    @staticmethod
    def gh_response(checks):
        def query(*args):
            if args[:2] == ("pr", "view"):
                return {"author": {"login": "code-author"}}
            if args[0] == "api" and "/reviews?" in args[1]:
                return [{"id": 7, "user": {"login": "independent-reviewer"},
                         "state": "APPROVED", "commit_id": "a" * 40}]
            if args[0] == "api" and "/check-runs" in args[1]:
                return checks
            raise AssertionError(f"Unexpected GitHub call: {args}")

        return query

    def verified_receipt(self, n):
        return {"status": "DONE", "pr": n + 3,
                "head_sha": "a" * 40, "merge_sha": "b" * 40}

    def make_pr(self, n):
        return {"headRefName": f"issue-orchestrator/issue-{n}-supervised",
                "headRefOid": "a" * 40, "baseRefName": "main",
                "headRepository": {"nameWithOwner": REPO},
                "body": f"Closes #{n}", "isDraft": False,
                "mergedAt": "2026-11-08T00:00:00Z",
                "mergeCommit": {"oid": "b" * 40},
                "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS"}],
                "reviewDecision": "APPROVED"}

    def test_final_success_requires_real_closed_pr_and_post_merge_ci(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = policy(Path(tmp))
            snapshot = self.make_snapshot(["CLOSED", "CLOSED", "CLOSED"])
            recorded = {"schema": 1, "repo": REPO, "branch": "main",
                        "entries": {str(n): self.verified_receipt(n)
                                    for n in p["issues"]},
                        "issue_scope": p["issues"], "active": None}
            checks = {"total_count": 1,
                      "check_runs": [{"head_sha": "b" * 40,
                                     "status": "completed", "conclusion": "success"}]}
            with patch.object(sup, "controller", return_value=recorded), \
                    patch.object(sup.queue, "live_snapshot", return_value=snapshot), \
                    patch.object(sup.queue, "pr_view", side_effect=lambda repo, n:
                                 self.make_pr(n - 3)), \
                    patch.object(sup.queue, "gh_json", side_effect=self.gh_response(checks)):
                result = sup.audit_queue(p)
            self.assertEqual("QUEUE_ALL_VERIFIED", result["status"])
            self.assertEqual([1, 2, 3], result["closed_verified"])
            self.assertEqual([], result["blocked"])

    def test_stale_review_or_changes_requested_never_attests(self):
        base = {"author": {"login": "code-author"}}
        stale = [{"id": 11, "user": {"login": "reviewer"},
                  "state": "APPROVED", "commit_id": "e" * 40}]
        requested = stale + [
            {"id": 12, "user": {"login": "reviewer"},
             "state": "CHANGES_REQUESTED", "commit_id": "a" * 40}]
        for reviews, expected in (
            (stale, "INDEPENDENT_EXACT_HEAD_REVIEW_MISSING"),
            (requested, "LATEST_REVIEW_REQUESTS_CHANGES"),
        ):
            with self.subTest(reviews=reviews), \
                    patch.object(sup.queue, "gh_json", side_effect=lambda *args:
                                 base if args[:2] == ("pr", "view") else reviews), \
                    self.assertRaisesRegex(sup.SupervisorError, expected):
                sup.independent_review_on_exact_head(REPO, 4, "a" * 40, "APPROVED")

    def test_queue_empty_is_not_complete_when_closed_receipt_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = policy(Path(tmp))
            snapshot = self.make_snapshot(["CLOSED", "CLOSED", "CLOSED"])
            recorded = {"schema": 1, "repo": REPO, "branch": "main",
                        "entries": {"1": self.verified_receipt(1),
                                    "2": self.verified_receipt(2)},
                        "issue_scope": p["issues"], "active": None}
            checks = {"total_count": 1,
                      "check_runs": [{"head_sha": "b" * 40,
                                     "status": "completed", "conclusion": "success"}]}
            with patch.object(sup, "controller", return_value=recorded), \
                    patch.object(sup.queue, "live_snapshot", return_value=snapshot), \
                    patch.object(sup.queue, "pr_view", side_effect=lambda repo, n:
                                 self.make_pr(n - 3)), \
                    patch.object(sup.queue, "gh_json", side_effect=self.gh_response(checks)):
                result = sup.audit_queue(p)
            self.assertEqual("QUEUE_NO_ELIGIBLE_WITH_BLOCKERS", result["status"])
            self.assertEqual([3], [i["issue"] for i in result["blocked"]])
            self.assertEqual([1, 2], result["closed_verified"])

    def test_missing_post_merge_checks_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = policy(Path(tmp))
            recorded = {"schema": 1, "repo": REPO, "branch": "main",
                        "entries": {str(n): self.verified_receipt(n)
                                    for n in p["issues"]},
                        "issue_scope": p["issues"], "active": None}
            with patch.object(sup, "controller", return_value=recorded), \
                    patch.object(sup.queue, "live_snapshot", return_value=self.make_snapshot(
                        ["CLOSED", "CLOSED", "CLOSED"])), \
                    patch.object(sup.queue, "pr_view", side_effect=lambda repo, n:
                                 self.make_pr(n - 3)), \
                    patch.object(sup.queue, "gh_json", side_effect=self.gh_response({"check_runs": []})):
                result = sup.audit_queue(p)
            self.assertEqual("QUEUE_NO_ELIGIBLE_WITH_BLOCKERS", result["status"])
            self.assertEqual([], result["closed_verified"])
            self.assertEqual(3, len(result["blocked"]))

    def test_truncated_post_merge_checks_cannot_hide_failed_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = policy(Path(tmp))
            recorded = {"schema": 1, "repo": REPO, "branch": "main",
                        "entries": {str(n): self.verified_receipt(n)
                                    for n in p["issues"]},
                        "issue_scope": p["issues"], "active": None}
            incomplete = {"total_count": 2, "check_runs": [
                {"head_sha": "b" * 40, "status": "completed",
                 "conclusion": "success"}]}
            with patch.object(sup, "controller", return_value=recorded), \
                    patch.object(sup.queue, "live_snapshot", return_value=self.make_snapshot(
                        ["CLOSED", "CLOSED", "CLOSED"])), \
                    patch.object(sup.queue, "pr_view", side_effect=lambda repo, n:
                                 self.make_pr(n - 3)), \
                    patch.object(sup.queue, "gh_json", side_effect=self.gh_response(incomplete)):
                result = sup.audit_queue(p)
            self.assertEqual("QUEUE_NO_ELIGIBLE_WITH_BLOCKERS", result["status"])
            self.assertEqual(3, len(result["blocked"]))

    def test_waiting_design_is_separate_from_eligible_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = policy(Path(tmp))
            recorded = {"schema": 1, "repo": REPO, "branch": "main",
                        "entries": {"1": {"status": "WAITING_DESIGN"}},
                        "issue_scope": p["issues"], "active": None}
            with patch.object(sup, "controller", return_value=recorded), \
                    patch.object(sup.queue, "live_snapshot", return_value=self.make_snapshot(
                        ["OPEN", "OPEN", "OPEN"])):
                result = sup.audit_queue(p)
            self.assertEqual([1], result["waiting_design"])
            self.assertNotEqual("QUEUE_ALL_VERIFIED", result["status"])


class ActiveReconciliationTests(unittest.TestCase):
    def build(self, temp):
        p = policy(Path(temp))
        root = Path(temp) / "state"
        place = root / "worktrees" / "issue-2"
        place.mkdir(parents=True)
        (place / ".git").write_text("gitdir: synthetic-placeholder\n", encoding="utf-8")
        host = sup.initial_state(p)
        host.update(mode="PAUSED", stage="TURN_DONE", active=2)
        return p, root, place, host

    @staticmethod
    def pr(sha):
        return {"baseRefName": "main",
                "headRefName": "issue-orchestrator/issue-2-supervised",
                "headRepository": {"nameWithOwner": REPO},
                "headRefOid": sha}

    @staticmethod
    def git_fixture(sha, *, branch=None, dirty=False, foreign_common=False):
        def run(args, **_kwargs):
            if args[-2:] == ["branch", "--show-current"]:
                return branch or "issue-orchestrator/issue-2-supervised"
            if args[-2:] == ["rev-parse", "--git-common-dir"]:
                place = Path(args[2])
                if place.name == "checkout":
                    return str(place / ".git")
                return str(place.parents[2] / ("attacker" if foreign_common else "checkout") / ".git")
            if args[-2:] == ["rev-parse", "HEAD"]:
                return sha
            if args[-2:] == ["status", "--porcelain"]:
                return " M README.md" if dirty else ""
            raise AssertionError(args)
        return run

    def test_matching_owned_pr_produces_review_gate_not_auto_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            p, root, _place, host = self.build(temp)
            sha = "a" * 40
            with patch.object(sup, "controller", return_value={"active": 2}), \
                    patch.object(sup.queue, "gh_json", return_value={
                        "number": 2, "state": "OPEN", "labels": []}), \
                    patch.object(sup, "scrubbed_argv", side_effect=self.git_fixture(sha)), \
                    patch.object(sup, "associated_pr", return_value=5), \
                    patch.object(sup.queue, "pr_view", return_value=self.pr(sha)):
                out = sup.reconcile_active(p, root, host)
            self.assertEqual("PR_PRESENT_REVIEW_REQUIRED", out["status"])
            self.assertEqual(sha, out["pr_head"])
            self.assertEqual(2, host["active"])
            self.assertEqual("TURN_DONE", host["stage"])

    def test_foreign_writer_refused_before_git_or_github(self):
        with tempfile.TemporaryDirectory() as temp:
            p, root, _place, host = self.build(temp)
            with patch.object(sup, "controller", return_value={"active": 1}), \
                    patch.object(sup.queue, "gh_json") as gh:
                out = sup.reconcile_active(p, root, host)
                gh.assert_not_called()
            self.assertEqual("NEEDS_HUMAN", out["status"])
            self.assertEqual("QUEUE_ACTIVE_MISMATCH", out["reason"])

    def test_live_closed_or_held_issue_is_never_reclaimed(self):
        with tempfile.TemporaryDirectory() as temp:
            p, root, _place, host = self.build(temp)
            for state, labels, reason in (
                ("CLOSED", [], "ACTIVE_ISSUE_NOT_OPEN"),
                ("OPEN", [{"name": "HOLD"}], "ACTIVE_ISSUE_NOW_HELD"),
            ):
                with self.subTest(state=state), \
                        patch.object(sup, "controller", return_value={"active": 2}), \
                        patch.object(sup.queue, "gh_json", return_value={
                            "number": 2, "state": state, "labels": labels}), \
                        patch.object(sup, "scrubbed_argv") as git:
                    out = sup.reconcile_active(p, root, host)
                    git.assert_not_called()
                self.assertEqual(reason, out["reason"])

    def test_unknown_worker_and_head_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            p, root, _place, host = self.build(temp)
            sha = "a" * 40
            cases = [
                ("b" * 40, False, "TURN_DONE", "WORKTREE_AND_PR_HEAD_DIVERGED"),
                (sha, True, "TURN_DONE", "DIRTY_WORKTREE_WITH_OPEN_PR"),
                (sha, False, "TURN_IN_FLIGHT", "UNVERIFIED_IN_FLIGHT_WORKER"),
            ]
            for local, dirty, stage, reason in cases:
                with self.subTest(reason=reason):
                    host["stage"] = stage
                    with patch.object(sup, "controller", return_value={"active": 2}), \
                            patch.object(sup.queue, "gh_json", return_value={
                                "number": 2, "state": "OPEN", "labels": []}), \
                            patch.object(sup, "scrubbed_argv",
                                         side_effect=self.git_fixture(local, dirty=dirty)), \
                            patch.object(sup, "associated_pr", return_value=5), \
                            patch.object(sup.queue, "pr_view", return_value=self.pr(sha)):
                        out = sup.reconcile_active(p, root, host)
                    self.assertEqual("NEEDS_HUMAN", out["status"])
                    self.assertEqual(reason, out["reason"])

    def test_foreign_worktree_git_directory_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            p, root, _place, host = self.build(temp)
            with patch.object(sup, "controller", return_value={"active": 2}), \
                    patch.object(sup.queue, "gh_json", return_value={
                        "number": 2, "state": "OPEN", "labels": []}), \
                    patch.object(sup, "scrubbed_argv",
                                 side_effect=self.git_fixture("a" * 40,
                                                              foreign_common=True)), \
                    patch.object(sup, "associated_pr") as owned:
                out = sup.reconcile_active(p, root, host)
                owned.assert_not_called()
            self.assertEqual("NEEDS_HUMAN", out["status"])
            self.assertEqual("WORKTREE_GIT_REPOSITORY_CHANGED", out["reason"])

    def test_no_pr_is_not_evidence_of_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            p, root, _place, host = self.build(temp)
            with patch.object(sup, "controller", return_value={"active": 2}), \
                    patch.object(sup.queue, "gh_json", return_value={
                        "number": 2, "state": "OPEN", "labels": []}), \
                    patch.object(sup, "scrubbed_argv",
                                 side_effect=self.git_fixture("a" * 40)), \
                    patch.object(sup, "associated_pr", return_value=None):
                out = sup.reconcile_active(p, root, host)
            self.assertEqual("NEEDS_HUMAN", out["status"])
            self.assertEqual("NO_OWNED_PR", out["reason"])


if __name__ == "__main__":
    unittest.main()
