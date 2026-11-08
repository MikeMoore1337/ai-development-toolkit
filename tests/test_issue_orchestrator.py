"""Offline regression and negative tests for the opt-in Issue Orchestrator (#565)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "issue_orchestrator", ROOT / "scripts" / "issue_orchestrator.py")
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SHA = "b" * 40
MERGE = "c" * 40
REPO = "example/toolkit"


def issue(number, *, state="OPEN", label=None, body="", title=None):
    return {"number": number, "title": title or f"Task {number}", "body": body,
            "state": state, "labels": [{"name": n} for n in (label or [])]}


def snapshot(issues, prs=None):
    return {"issues": issues, "pull_requests": prs or []}


def state(entries=None, active=None):
    return {"schema": 1, "repo": REPO, "branch": "main",
            "active": active, "entries": entries or {}}


def pr(number=10, *, merge=False, checks=None, review=None, branch="main"):
    result = {"number": number, "headRepository": {"nameWithOwner": REPO},
              "headRefName": "issue-orchestrator/issue-2-fix",
              "headRefOid": SHA, "baseRefName": branch, "isDraft": False,
              "body": "Closes #2", "mergeStateStatus": "CLEAN",
              "mergedAt": "2026-11-08T10:00:00Z" if merge else None,
              "mergeCommit": {"oid": MERGE} if merge else None,
              "reviewDecision": review,
              "statusCheckRollup": checks if checks is not None else [
                  {"status": "COMPLETED", "conclusion": "SUCCESS"}]}
    return result


class PlannerTests(unittest.TestCase):
    def test_priority_stable_and_closed_dependencies(self):
        data = snapshot([issue(1, state="CLOSED"), issue(2, body="Depends on #1",
                             label=["P1"]), issue(3, label=["P0"]),
                         issue(4, label=["P1"])])
        result = mod.plan(data, state(), "main")
        self.assertEqual([3, 2, 4], [x["number"] for x in result["available"]])
        self.assertIsNone(result["active"])
        self.assertEqual("NOT_RUN", result["execution"])

    def test_priority_from_title_only_when_no_label_exists(self):
        data = snapshot([issue(2, title="[P0] Emergency"),
                         issue(3, title="[P2] Routine"),
                         issue(4, label=["P1"], title="[P0] Label wins")])
        result = mod.plan(data, state(), "main")
        self.assertEqual([2, 4, 3], [x["number"] for x in result["available"]])

    def test_open_or_unknown_dependencies_and_self_loop(self):
        data = snapshot([issue(1), issue(2, body="- Blocked by: #1"),
                         issue(3, body="requires #999"), issue(4, body="Depends on #4")])
        result = mod.plan(data, state(), "main")
        statuses = {x["number"]: x["reasons"] for x in result["excluded"]}
        self.assertIn("OPEN_DEPENDENCY", statuses[2])
        self.assertIn("UNKNOWN_DEPENDENCY", statuses[3])
        self.assertIn("SELF_DEPENDENCY", statuses[4])
        self.assertEqual([1], [x["number"] for x in result["available"]])

    def test_dependency_cycle_is_diagnosed_not_treated_as_finished(self):
        data = snapshot([issue(1, body="Depends on #2"),
                         issue(2, body="Blocked by #1"),
                         issue(3, body="Requires #2")])
        result = mod.plan(data, state(), "main")
        reasons = {x["number"]: x["reasons"] for x in result["excluded"]}
        self.assertIn("DEPENDENCY_CYCLE", reasons[1])
        self.assertIn("DEPENDENCY_CYCLE", reasons[2])
        self.assertNotIn("DEPENDENCY_CYCLE", reasons[3])
        self.assertIn("OPEN_DEPENDENCY", reasons[3])

    def test_unrelated_issue_links_not_dependencies(self):
        x = issue(2, body="See #1 for context.\n- Related to #1")
        self.assertEqual(set(), mod.dependencies(x))

    def test_hold_and_design_exclusions_and_owner_approval(self):
        data = snapshot([issue(1, label=["HOLD"]), issue(2, label=["approval:design"]),
                         issue(3, label=["do-not-automate"])])
        result = mod.plan(data, state(), "main")
        self.assertEqual([2], [x["number"] for x in result["available"]])
        self.assertEqual("DESIGN_PREVIEW", result["available"][0]["phase"])
        self.assertEqual([1, 3], [x["number"] for x in result["excluded"]])
        approved = state({"2": {"status": "READY", "design_approved": True}})
        self.assertEqual("IMPLEMENTATION", mod.plan(data, approved, "main")["available"][0]["phase"])

    def test_existing_pr_no_double_work(self):
        data = snapshot([issue(2), issue(3)], [
            {"number": 14, "body": "Fixes #2", "headRefName": "feature/x"}])
        result = mod.plan(data, state(), "main")
        self.assertEqual([3], [x["number"] for x in result["available"]])
        self.assertIn("EXISTING_OPEN_PR", result["excluded"][0]["reasons"])

    def test_branch_association_and_no_false_positive(self):
        self.assertEqual({5}, mod.pr_issue_numbers({
            "headRefName": "issue-orchestrator/issue-5-a", "body": ""}))
        self.assertNotIn(5, mod.pr_issue_numbers({
            "headRefName": "issue-orchestrator/issue-55-a", "body": "See #5"}))

    def test_state_and_snapshot_must_be_valid(self):
        with self.assertRaisesRegex(ValueError, "INVALID_REPOSITORY"):
            mod.validate_repo("../something")
        with self.assertRaisesRegex(ValueError, "INVALID_SNAPSHOT"):
            mod.plan({}, state(), "main")
        with self.assertRaisesRegex(ValueError, "INVALID_ISSUE_STATE"):
            mod.plan(snapshot([issue(1), issue(1)]), state(), "main")
        with self.assertRaisesRegex(ValueError, "INVALID_TASK_STATE"):
            mod.plan(snapshot([issue(1)]), state({"1": 5}), "main")


class DesignApprovalTests(unittest.TestCase):
    def test_owner_exact_revision_and_temporal_order_required(self):
        now = datetime.now(timezone.utc)
        stamp = now.isoformat()
        old = (now - timedelta(hours=1)).isoformat()
        expected = f"/approve-design #2 {SHA}"
        comments = [
            {"author": {"login": "example"}, "body": expected, "createdAt": old},
            {"author": {"login": "visitor"}, "body": expected, "createdAt": stamp},
            {"author": {"login": "example"}, "body": expected + " extra", "createdAt": stamp},
        ]
        self.assertFalse(mod.approval_found(comments, "example", 2, SHA, stamp))
        comments.append({"author": {"login": "example"}, "body": expected,
                         "createdAt": (now + timedelta(seconds=1)).isoformat()})
        self.assertTrue(mod.approval_found(comments, "example", 2, SHA, stamp))
        comments.append({"author": {"login": "example"},
                         "body": f"/reject-design #2 {SHA}",
                         "createdAt": (now + timedelta(seconds=2)).isoformat()})
        self.assertFalse(mod.approval_found(comments, "example", 2, SHA, stamp))

    def test_different_revision_never_approves(self):
        now = datetime.now(timezone.utc).isoformat()
        comments = [{"author": {"login": "example"},
                     "body": f"/approve-design #2 {'a' * 40}", "createdAt": now}]
        self.assertFalse(mod.approval_found(comments, "example", 2, SHA, now))


class MergeGateTests(unittest.TestCase):
    def test_clean_exact_ci_and_merge_evidence(self):
        self.assertEqual(SHA, mod.check_pr(pr(), 2, "main", merged=False, repo=REPO))
        self.assertEqual(SHA, mod.check_pr(pr(merge=True), 2, "main", merged=True, repo=REPO))
        with self.assertRaisesRegex(ValueError, "PR_NOT_MERGED"):
            mod.check_pr(pr(), 2, "main", merged=True, repo=REPO)

    def test_negative_cases_fail_closed(self):
        mutations = [
            ({"baseRefName": "prod"}, "PR_BASE_BRANCH_MISMATCH"),
            ({"headRepository": {"nameWithOwner": "attacker/fork"}}, "CROSS_REPOSITORY_PR_REFUSED"),
            ({"headRefOid": "bad"}, "PR_HEAD_SHA_NOT_VERIFIED"),
            ({"body": ""}, "PR_NOT_ASSOCIATED_WITH_ISSUE"),
            ({"body": "", "headRefName": "feature/x"}, "PR_NOT_ASSOCIATED_WITH_ISSUE"),
            ({"isDraft": True}, "DRAFT_PR"),
            ({"mergeStateStatus": "BLOCKED"}, "PR_NOT_MERGEABLE"),
            ({"statusCheckRollup": []}, "CI_EVIDENCE_MISSING"),
            ({"statusCheckRollup": [{"status": "IN_PROGRESS"}]}, "CI_NOT_COMPLETE"),
            ({"statusCheckRollup": [{"status": "COMPLETED", "conclusion": "FAILURE"}]}, "CI_NOT_SUCCESS"),
            ({"statusCheckRollup": [{"state": "PENDING"}]}, "CI_NOT_SUCCESS"),
            ({"reviewDecision": "CHANGES_REQUESTED"}, "CHANGES_REQUESTED"),
            ({"reviewDecision": "REVIEW_REQUIRED"}, "REVIEW_REQUIRED"),
        ]
        for patch_data, expected in mutations:
            with self.subTest(patch_data=patch_data), self.assertRaisesRegex(
                    ValueError, expected):
                mod.check_pr({**pr(), **patch_data}, 2, "main", merged=False, repo=REPO)


class DurableStateTests(unittest.TestCase):
    def test_atomic_round_trip_and_fail_closed_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = mod.state_directory(REPO, temp)
            s = mod.read_state(root, REPO, "main")
            self.assertIsNone(s["active"])
            s["active"] = 12
            s["entries"]["12"] = {"status": "IN_PROGRESS"}
            mod.write_state(root, s)
            self.assertEqual(12, mod.read_state(root, REPO, "main")["active"])
            with self.assertRaisesRegex(ValueError, "STATE_CONTEXT_MISMATCH"):
                mod.read_state(root, REPO, "dev")

    def test_read_only_planning_does_not_create_state_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "missing-state-dir"
            planned = mod.state_directory(REPO, str(root))
            self.assertFalse(planned.exists())
            self.assertIsNone(mod.read_state(planned, REPO, "main")["active"])

    def test_corrupted_state_refuses_new_task(self):
        with tempfile.TemporaryDirectory() as temp:
            root = mod.state_directory(REPO, temp)
            bad = state({"7": {"status": "BOGUS"}})
            mod.write_state(root, bad)
            with self.assertRaisesRegex(ValueError, "INVALID_STATE_ENTRY"):
                mod.read_state(root, REPO, "main")
            bad = state({"7": {"status": "READY"}}, active=7)
            mod.write_state(root, bad)
            with self.assertRaisesRegex(ValueError, "INCONSISTENT_ACTIVE_ISSUE"):
                mod.read_state(root, REPO, "main")

    def test_design_claim_wait_and_next_task(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp:
            fixture = snapshot([issue(2, label=["P0", "approval:design"]),
                                issue(3)])
            def arg(action, **changes):
                base = dict(action=action, repo=REPO, branch="main", state_dir=temp,
                            issue=2, pr=10, revision=SHA,
                            preview_url="https://example.org/mock", reason="blocked",
                            merge=False, close_issue=False)
                return SimpleNamespace(**{**base, **changes})
            with patch.object(mod, "live_snapshot", return_value=fixture):
                claimed = mod.execute(arg("start"))
                self.assertEqual(2, claimed["issue"])
                self.assertEqual("DESIGN_PREVIEW", claimed["phase"])
                with patch.object(mod, "pr_view", return_value=pr(merge=True)):
                    with self.assertRaisesRegex(ValueError, "DESIGN_APPROVAL_REQUIRED"):
                        mod.execute(arg("finish"))
                waiting = mod.execute(arg("design-request"))
                self.assertEqual("WAITING_DESIGN", waiting["status"])
                self.assertIsNone(mod.execute(arg("status"))["active"])
                self.assertEqual(3, mod.execute(arg("start"))["issue"])
                mod.execute(arg("block", issue=3))
                self.assertEqual("BLOCKED", mod.execute(arg("status"))["entries"]["3"]["status"])

    def test_authenticated_design_approval_then_verified_merge(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp:
            fixture = snapshot([issue(2, label=["P0", "approval:design"])])
            def arg(action):
                return SimpleNamespace(action=action, repo=REPO, branch="main",
                                       state_dir=temp, issue=2, pr=10,
                                       revision=SHA, preview_url="https://example.org/mock",
                                       reason="", merge=False, close_issue=False)
            with patch.object(mod, "live_snapshot", return_value=fixture):
                mod.execute(arg("start"))
                mod.execute(arg("design-request"))
                with patch.object(mod, "live_design_approved", return_value=False):
                    self.assertEqual("WAITING_DESIGN", mod.execute(arg("approve"))["status"])
                with patch.object(mod, "live_design_approved", return_value=True):
                    self.assertEqual("DESIGN_APPROVED", mod.execute(arg("approve"))["status"])
                claimed = mod.execute(arg("start"))
                self.assertEqual("IMPLEMENTATION", claimed["phase"])
                self.assertEqual(SHA, mod.execute(arg("status"))["entries"]["2"]["preview_revision"])
                with patch.object(mod, "live_design_approved", return_value=False), patch.object(
                        mod, "gh_json", return_value={"labels": [{"name": "approval:design"}]}):
                    with self.assertRaisesRegex(ValueError, "DESIGN_APPROVAL_MISSING_OR_REVOKED"):
                        mod.execute(arg("finish"))
                with patch.object(mod, "live_design_approved", return_value=True), patch.object(
                        mod, "gh_json", return_value={"labels": [{"name": "approval:design"}]}), patch.object(
                        mod, "pr_view", return_value=pr(merge=True)):
                    finished = mod.execute(arg("finish"))
                self.assertEqual("DONE", finished["status"])
                self.assertEqual(MERGE, finished["merge_sha"])
                self.assertIsNone(mod.execute(arg("status"))["active"])

    def test_exclusive_lock_refuses_second_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = mod.state_directory(REPO, temp)
            with mod.exclusive(root):
                with self.assertRaisesRegex(ValueError, "QUEUE_LOCK_EXISTS"):
                    with mod.exclusive(root):
                        pass
            self.assertFalse((root / "queue.lock").exists())

    def test_start_resume_after_restart_never_claims_another(self):
        args = type("Args", (), {"repo": REPO, "branch": "main", "action": "start",
                                  "state_dir": None})
        with tempfile.TemporaryDirectory() as temp:
            args.state_dir = temp
            with patch.object(mod, "live_snapshot",
                              return_value=snapshot([issue(7, label=["P0"]), issue(8)])):
                claimed = mod.execute(args)
                self.assertEqual(7, claimed["issue"])
                with self.assertRaisesRegex(ValueError, "ONE_WRITER_ALREADY_ACTIVE"):
                    mod.execute(args)
                self.assertEqual(7, mod.read_state(Path(temp), REPO, "main")["active"])


class SafePilotScopeTests(unittest.TestCase):
    def test_hold_in_title_is_excluded_even_without_labels(self):
        data = snapshot([issue(344, title="[P2][HOLD] L6 experiment"),
                         issue(401, title="[P0] Ordinary work")])
        result = mod.plan(data, state(), "main")
        self.assertEqual([401], [i["number"] for i in result["available"]])
        self.assertIn("EXCLUDED_TITLE", result["excluded"][0]["reasons"])

    def test_blocking_title_marker_variants(self):
        for marker in ("HOLD", "BLOCKED", "DRAFT", "PAUSED", "BACKLOG", "NO_GO"):
            with self.subTest(marker=marker):
                candidate = issue(7, title=f"[P0][{marker}] sensitive task")
                result = mod.plan(snapshot([candidate]), state(), "main")
                self.assertEqual([], result["available"])
                self.assertIn("EXCLUDED_TITLE", result["excluded"][0]["reasons"])

    def test_open_pr_title_blocks_duplicate_work(self):
        data = snapshot([issue(401), issue(437), issue(449)],
                        [{"number": 568, "title": "fix(#401): advisor",
                          "body": "Independent review of model advice", "headRefName": "other-branch"},
                         {"number": 571, "title": "chore(release): v5.5.10 (#437)",
                          "body": "Source packaging only", "headRefName": "release-branch"}])
        result = mod.plan(data, state(), "main")
        self.assertEqual([449], [i["number"] for i in result["available"]])
        self.assertEqual({401, 437}, {i["number"] for i in result["excluded"]})
        self.assertTrue(all("EXISTING_OPEN_PR" in i["reasons"]
                            for i in result["excluded"]))

    def test_unrelated_pr_body_references_are_not_ownership(self):
        data = snapshot([issue(10), issue(11)],
                        [{"number": 42, "title": "fix: separate issue",
                          "body": "See #10 and #11 for background",
                          "headRefName": "unrelated"}])
        self.assertEqual([10, 11], [i["number"] for i in
                                    mod.plan(data, state(), "main")["available"]])

    def test_scope_parsing_and_missing_issues(self):
        self.assertEqual([1, 3, 5], mod.parse_issue_scope("5,1,3"))
        for raw in ("", "0", "-1", "1,1", "1, 2", "x", "1,", "1;2", "1,2,2"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                mod.parse_issue_scope(raw)
        with self.assertRaisesRegex(ValueError, "SELECTED_ISSUE_NOT_FOUND"):
            mod.plan(snapshot([issue(1)]), state(), "main", requested_scope=[1, 999])

    def test_plan_scope_is_read_only_and_filters_other_tasks(self):
        data = snapshot([issue(2, label=["P0"]), issue(3), issue(4)])
        result = mod.plan(data, state(), "main", requested_scope=[3, 4])
        self.assertEqual([3, 4], [i["number"] for i in result["available"]])
        self.assertEqual([3, 4], result["issue_scope"])
        self.assertEqual("NOT_RUN", result["execution"])
        self.assertIsNone(state().get("issue_scope"))

    def test_scope_persists_and_cannot_expand_after_restart(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp:
            data = snapshot([issue(1, label=["P0"]), issue(2), issue(3)])
            args = SimpleNamespace(action="start", repo=REPO, branch="main",
                                   state_dir=temp, issues="3,2", issue=2,
                                   reason="Synthetic block")
            with patch.object(mod, "live_snapshot", return_value=data):
                claim = mod.execute(args)
                self.assertEqual(2, claim["issue"])
                saved = mod.read_state(Path(temp), REPO, "main")
                self.assertEqual([2, 3], saved["issue_scope"])
                args.action = "block"
                mod.execute(args)
                args.action = "start"
                args.issues = "1"
                with self.assertRaisesRegex(ValueError, "ISSUE_SCOPE_CHANGE_REFUSED"):
                    mod.execute(args)
                args.issues = None
                self.assertEqual(3, mod.execute(args)["issue"])
                saved = mod.read_state(Path(temp), REPO, "main")
                self.assertEqual([2, 3], saved["issue_scope"])
                with self.assertRaisesRegex(ValueError, "ISSUE_SCOPE_CHANGE_REFUSED"):
                    mod.plan(data, saved, "main", requested_scope=[1, 2])

    def test_corrupted_scope_refused_without_reset(self):
        with tempfile.TemporaryDirectory() as temp:
            root = mod.state_directory(REPO, temp)
            s = state()
            s["issue_scope"] = [2, 2]
            mod.write_state(root, s)
            with self.assertRaisesRegex(ValueError, "INVALID_PERSISTED_ISSUE_SCOPE"):
                mod.read_state(root, REPO, "main")


if __name__ == "__main__":
    unittest.main()
