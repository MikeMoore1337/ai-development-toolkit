"""Issue #440: deterministic native-plan checks and GitHub Actions-only synthetic Git."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_feature_orchestra as oracle

BASE_SHA = "0123456789abcdef0123456789abcdef01234567"


def candidate():
    return {
        "schema_version": 1, "revision": BASE_SHA,
        "controller": "feature-delivery", "active_controllers": ["feature-delivery"],
        "runtime_state": "CLIENT_RUNTIME_NOT_VERIFIED",
        "tasks": [
            {"id": "api", "base_sha": BASE_SHA, "branch": "feature/api",
             "worktree": "wt-api", "writer": "api_owner",
             "write_paths": ["src/api/"], "shared_contracts": [],
             "depends_on": [], "acceptance": ["API contract tests pass"]},
            {"id": "ui", "base_sha": BASE_SHA, "branch": "feature/ui",
             "worktree": "wt-ui", "writer": "ui_owner",
             "write_paths": ["src/ui/"], "shared_contracts": [],
             "depends_on": [], "acceptance": ["UI interaction tests pass"]},
        ],
    }


class ParallelPlanTests(unittest.TestCase):
    def test_independent_disjoint_tasks_are_only_static_preflight(self):
        self.assertEqual([], oracle.validate_parallel_plan(candidate()))

    def test_legacy_feature_orchestra_schema_is_unchanged(self):
        fixture = ROOT / "fixtures" / "feature_orchestra_valid.json"
        self.assertEqual([], oracle.validate(json.loads(fixture.read_text(encoding="utf-8"))))

    def test_writer_scope_overlap_exact_case_and_ancestor(self):
        for a, b in (("MANIFEST.json", "MANIFEST.json"),
                     ("src/api/", "src/api/client.py"),
                     ("src/API/foo.py", "src/api/Foo.py"),
                     ("docs/e\u0301.txt", "docs/\u00e9.txt")):
            with self.subTest(a=a, b=b):
                trial = candidate()
                trial["tasks"][0]["write_paths"] = [a]
                trial["tasks"][1]["write_paths"] = [b]
                self.assertIn("OVERLAPPING_WRITE_SCOPE", oracle.validate_parallel_plan(trial))

    def test_lookalike_but_distinct_paths_are_not_false_positive(self):
        for a, b in (("src/api.py", "src/api_client.py"),
                     ("src/app/", "src/application/"),
                     ("a.py", "a.py.backup")):
            with self.subTest(a=a, b=b):
                trial = candidate()
                trial["tasks"][0]["write_paths"] = [a]
                trial["tasks"][1]["write_paths"] = [b]
                self.assertEqual([], oracle.validate_parallel_plan(trial))

    def test_shared_contract_requires_an_order_even_if_files_are_disjoint(self):
        trial = candidate()
        for task in trial["tasks"]:
            task["shared_contracts"] = ["api_v1"]
        self.assertIn("UNORDERED_SHARED_CONTRACT", oracle.validate_parallel_plan(trial))
        trial["tasks"][1]["depends_on"] = ["api"]
        self.assertEqual([], oracle.validate_parallel_plan(trial))

    def test_dependency_error_cycle_and_transitive_order(self):
        trial = candidate()
        trial["tasks"][1]["depends_on"] = ["does_not_exist"]
        self.assertIn("INVALID_DEPENDENCY", oracle.validate_parallel_plan(trial))
        trial["tasks"][0]["depends_on"] = ["ui"]
        trial["tasks"][1]["depends_on"] = ["api"]
        self.assertIn("DEPENDENCY_CYCLE", oracle.validate_parallel_plan(trial))

    def test_base_sha_and_runtime_forgery_rejected(self):
        trial = candidate()
        trial["tasks"][1]["base_sha"] = "f" * 40
        self.assertIn("STALE_TASK_SHA", oracle.validate_parallel_plan(trial))
        trial = candidate()
        trial["runtime_state"] = "NATIVE_SUBAGENTS_EXECUTED"
        self.assertIn("UNVERIFIED_RUNTIME_CLAIM", oracle.validate_parallel_plan(trial))

    def test_no_second_controller(self):
        trial = candidate()
        trial["active_controllers"].append("make-feature")
        self.assertIn("DUPLICATE_CONTROLLER", oracle.validate_parallel_plan(trial))

    def test_windows_git_path_separator_alias(self):
        # Git commonly lists D:/... while Windows Path.resolve uses D:\...
        self.assertEqual(oracle._path_key(r"D:\Checkout\worktree".replace(chr(92), "/")),
                         oracle._path_key("d:/checkout/worktree"))

    def test_nested_worktree_paths_and_protected_branches_rejected(self):
        for child in ("wt-api/child", "WT-API/nested"):
            with self.subTest(child=child):
                trial = candidate()
                trial["tasks"][1]["worktree"] = child
                self.assertIn("WORKTREE_COLLISION", oracle.validate_parallel_plan(trial))
        for unsafe in ("main", "master", "HEAD", "refs/heads/work", "feature..bad"):
            with self.subTest(branch=unsafe):
                trial = candidate()
                trial["tasks"][1]["branch"] = unsafe
                self.assertIn("UNSAFE_BRANCH", oracle.validate_parallel_plan(trial))

    def test_duplicate_ids_writers_branches_and_workspaces(self):
        for key, value, code in (
            ("id", "api", "PARALLEL_TASK_ID"),
            ("writer", "api_owner", "WRITER_REUSED"),
            ("branch", "FEATURE/API", "DUPLICATE_BRANCH"),
            ("worktree", "WT-API", "WORKTREE_COLLISION"),
        ):
            with self.subTest(field=key):
                trial = candidate()
                trial["tasks"][1][key] = value
                self.assertIn(code, oracle.validate_parallel_plan(trial))
        trial = candidate()
        trial["tasks"][1]["writer"] = "api_owner"
        trial["tasks"][1]["depends_on"] = ["api"]
        self.assertEqual([], oracle.validate_parallel_plan(trial))

    def test_reject_unsafe_paths_windows_aliases_and_traversal(self):
        for path in ("../secrets", "/abs", "C:/users/test", "a\\b", "a//b",
                     "x/./file", "a/../b", "CON.txt", "a/.git/config",
                     "x:stream", "file*", "x. "):
            with self.subTest(path=path):
                trial = candidate()
                trial["tasks"][0]["write_paths"] = [path]
                self.assertIn("WRITE_SCOPE", oracle.validate_parallel_plan(trial))
        for worktree in ("../outside", "AUX", "C:/wt", "/tmp/wt", "foo\\bar"):
            with self.subTest(worktree=worktree):
                trial = candidate()
                trial["tasks"][1]["worktree"] = worktree
                self.assertIn("UNSAFE_WORKTREE_PATH", oracle.validate_parallel_plan(trial))

    def test_bad_branch_and_acceptance_are_blocked(self):
        trial = candidate()
        trial["tasks"][0]["branch"] = "feature/api.lock"
        self.assertIn("UNSAFE_BRANCH", oracle.validate_parallel_plan(trial))
        trial = candidate()
        trial["tasks"][0]["acceptance"] = []
        self.assertIn("ACCEPTANCE", oracle.validate_parallel_plan(trial))

    def test_malformed_nested_shapes_are_fail_closed(self):
        for value in (None, [], "x", {}, {**candidate(), "tasks": [None, None]},
                      {**candidate(), "tasks": [[], []]},
                      {**candidate(), "tasks": "bad"},
                      {**candidate(), "extra": "ignore"}):
            with self.subTest(value=repr(value)[:100]):
                self.assertNotEqual([], oracle.validate_parallel_plan(value))

    def test_cli_static_mode_never_claims_native_agent_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            plan = Path(temp) / "plan.json"
            plan.write_text(json.dumps(candidate()), encoding="utf-8")
            before = plan.read_bytes()
            cp = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_feature_orchestra.py"),
                 "--parallel-plan", str(plan)],
                text=True, capture_output=True, timeout=10)
            self.assertEqual(0, cp.returncode, cp.stderr)
            self.assertIn("STATIC_PLAN_VALIDATED", cp.stdout)
            self.assertIn("CLIENT_RUNTIME_NOT_VERIFIED", cp.stdout)
            self.assertEqual(before, plan.read_bytes())


@unittest.skipUnless(os.environ.get("GITHUB_ACTIONS") == "true",
                     "Synthetic Git worktree tests run only in GitHub Actions")
class SyntheticWorktreeTests(unittest.TestCase):
    def setUp(self):
        # Resolve the macOS /var -> /private/var alias before root-link checks.
        self.temp = tempfile.TemporaryDirectory(
            prefix="adt440-owned-", dir=Path(tempfile.gettempdir()).resolve())
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.repo = self.parent / "original"
        self.repo.mkdir()
        self.git(self.repo, "init", "-b", "main")
        self.git(self.repo, "config", "user.name", "Synthetic QA")
        self.git(self.repo, "config", "user.email", "synthetic@example.invalid")
        (self.repo / "shared.txt").write_text("baseline\n", encoding="utf-8")
        self.git(self.repo, "add", "shared.txt")
        self.git(self.repo, "commit", "-m", "synthetic baseline")
        self.sha = self.git(self.repo, "rev-parse", "HEAD").stdout.strip()
        self.plan = candidate()
        self.plan["revision"] = self.sha
        for task in self.plan["tasks"]:
            task["base_sha"] = self.sha

    def git(self, at, *args, check=True):
        # Git is invoked ONLY inside paths created by this test in TemporaryDirectory.
        self.assertTrue(Path(at).resolve().is_relative_to(self.parent.resolve()))
        result = subprocess.run(["git", "-C", str(at), *args], text=True,
                                capture_output=True, timeout=12, check=False)
        if check and result.returncode:
            self.fail(f"Synthetic Git failed: {args} {result.stderr}")
        return result

    def test_git_root_common_dir_clean_preflight_and_stale_head(self):
        git_root = self.git(self.repo, "rev-parse", "--show-toplevel").stdout.strip()
        self.assertEqual(self.repo.resolve(), Path(git_root).resolve())
        self.assertTrue(self.git(self.repo, "rev-parse", "--git-common-dir").stdout.strip())
        self.assertEqual([], oracle.validate_parallel_plan(self.plan, git_root=self.repo))
        (self.repo / "new.txt").write_text("untracked", encoding="utf-8")
        self.assertIn("DIRTY_GIT_STATE", oracle.validate_parallel_plan(self.plan, git_root=self.repo))
        self.git(self.repo, "add", "new.txt")
        self.git(self.repo, "commit", "-m", "new head")
        self.assertIn("STALE_GIT_HEAD", oracle.validate_parallel_plan(self.plan, git_root=self.repo))

    def test_existing_worktrees_and_branch_ownership_are_detected(self):
        for task in self.plan["tasks"]:
            self.git(self.repo, "worktree", "add", "-b", task["branch"],
                     str(self.parent / task["worktree"]), self.sha)
        result = oracle.validate_parallel_plan(self.plan, git_root=self.repo)
        self.assertIn("BRANCH_ALREADY_CHECKED_OUT", result)
        self.assertIn("WORKTREE_PATH_OCCUPIED", result)
        self.assertIn("WORKTREE_ALREADY_REGISTERED", result)
        self.assertEqual(3, len([line for line in self.git(
            self.repo, "worktree", "list", "--porcelain").stdout.splitlines()
            if line.startswith("worktree ")]))

    def test_real_git_merge_conflict_in_synthetic_worktrees_only(self):
        a, b = self.parent / "wt-api", self.parent / "wt-ui"
        self.git(self.repo, "worktree", "add", "-b", "feature/api", str(a), self.sha)
        self.git(self.repo, "worktree", "add", "-b", "feature/ui", str(b), self.sha)
        for wt, content in ((a, "change from API\n"), (b, "change from UI\n")):
            (wt / "shared.txt").write_text(content, encoding="utf-8")
            self.git(wt, "add", "shared.txt")
            self.git(wt, "commit", "-m", "intentional conflict")
        merger = self.git(b, "merge", "--no-edit", "feature/api", check=False)
        self.assertNotEqual(0, merger.returncode)
        self.assertEqual("shared.txt", self.git(
            b, "diff", "--name-only", "--diff-filter=U").stdout.strip())

    def test_existing_file_or_symlink_path_prevents_reuse(self):
        (self.parent / "wt-api").mkdir()
        self.assertIn("WORKTREE_PATH_OCCUPIED", oracle.validate_parallel_plan(
            self.plan, git_root=self.repo))
        (self.parent / "wt-api").rmdir()
        target = self.parent / "existing-dir"
        target.mkdir()
        try:
            (self.parent / "wt-api").symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links not allowed on runner")
        self.assertIn("WORKTREE_PATH_LINKED", oracle.validate_parallel_plan(
            self.plan, git_root=self.repo))

    def test_no_project_root_or_symlink_root_is_allowed(self):
        self.assertIn("GIT_ROOT_INVALID", oracle.validate_parallel_plan(
            self.plan, git_root=self.repo / "missing"))
        linked = self.parent / "repo-alias"
        try:
            linked.symlink_to(self.repo, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks not available")
        self.assertIn("GIT_PATH_LINKED", oracle.validate_parallel_plan(
            self.plan, git_root=linked))


if __name__ == "__main__":
    unittest.main()
