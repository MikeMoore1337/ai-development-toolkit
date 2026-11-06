"""#434: real-Git native observability boundary and read-only regressions."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import toolkit_mcp as mcp  # noqa: E402


class NativeObservability434Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="adt-observe-434-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.repo = self.folder / "source-repo"
        self.repo.mkdir()
        self._git("init", "-q", "-b", "main")
        (self.repo / "tracked.txt").write_text("SENSITIVE_OBSERVER_FIXTURE\n", encoding="utf-8")
        self._git("add", "tracked.txt")
        self._git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                  "commit", "-qm", "initial")

    def _git(self, *args, repo=None):
        # Test setup itself must be independent of caller-provided Git overrides.
        env = {key: value for key, value in os.environ.items()
               if not key.upper().startswith("GIT_")}
        return subprocess.run(["git", "-C", str(repo or self.repo), *args],
                              check=True, capture_output=True, env=env)

    def _call(self, project=None, client="codex", **extra):
        return mcp.handle({
            "jsonrpc": "2.0", "id": 434, "method": "tools/call",
            "params": {"name": "toolkit_observe_project", "arguments": {
                "project": str(project if project is not None else self.repo),
                "client": client, **extra,
            }},
        })["result"]

    def _data(self, **kwargs):
        answer = self._call(**kwargs)
        self.assertFalse(answer.get("isError"), answer)
        return answer["structuredContent"]

    def test_clean_untracked_dirty_and_evidence_boundaries(self):
        first = self._data()
        project = first["project"]
        self.assertEqual(project["branch"], "main")
        self.assertEqual(project["worktree_count"], 1)
        self.assertFalse(project["tracked_dirty"])
        self.assertEqual(project["tracked_status_sha256"],
                         hashlib.sha256(b"").hexdigest())
        self.assertEqual(first["source"], "TOOLKIT_LOCAL_GIT_METADATA")
        self.assertEqual(first["status"], "LOCAL_SOURCE_ONLY")
        self.assertEqual(first["session_adapter"], "NOT_CONNECTED")
        self.assertEqual(first["session_active"], "NOT_OBSERVED")
        self.assertEqual(first["L4_discovery"], "NOT_VERIFIED")
        self.assertEqual(first["L5_invocation"], "NOT_VERIFIED")
        self.assertEqual(first["L6_effectiveness"], "NOT_MEASURED")
        self.assertEqual(first["runtime_enforcement"], "NOT_VERIFIED")
        self.assertEqual(first["execution"], "NOT_RUN")
        self.assertEqual(first["authorization"], "NOT_GRANTED")
        self.assertEqual(first["network"], "NOT_USED")
        (self.repo / "ignored-untracked-secret.txt").write_text("untracked only")
        self.assertEqual(self._data()["project"], project)
        (self.repo / "tracked.txt").write_text("edited, but no agent evidence\n")
        updated = self._data()
        self.assertTrue(updated["project"]["tracked_dirty"])
        self.assertNotEqual(updated["project"]["tracked_status_sha256"],
                            project["tracked_status_sha256"])
        self.assertEqual(updated["project"]["commit"], project["commit"])
        self.assertEqual(updated["L5_invocation"], "NOT_VERIFIED")
        serialized = json.dumps(updated)
        for sensitive in (str(self.repo), "tracked.txt", "ignored-untracked",
                          "SENSITIVE_OBSERVER_FIXTURE", "edited, but"):
            self.assertNotIn(sensitive, serialized)

    def test_detached_head_is_a_valid_observation(self):
        expected_commit = self._data()["project"]["commit"]
        self._git("checkout", "-q", "--detach", "HEAD")
        observed = self._data()
        self.assertEqual(observed["project"]["branch"], "DETACHED")
        self.assertEqual(observed["project"]["commit"], expected_commit)
        self.assertEqual(observed["session_active"], "NOT_OBSERVED")

    def test_multiple_worktrees_including_dot_git_file(self):
        linked = self.folder / "linked-worktree"
        self._git("worktree", "add", "-q", "--detach", str(linked), "HEAD")
        self.assertTrue((linked / ".git").is_file())
        primary = self._data()
        secondary = self._data(project=linked, client="hermes")
        self.assertEqual(primary["project"]["worktree_count"], 2)
        self.assertEqual(secondary["project"]["worktree_count"], 2)
        self.assertEqual(secondary["project"]["branch"], "DETACHED")
        self.assertNotEqual(primary["project"]["repo_id"],
                            secondary["project"]["repo_id"])
        self.assertNotIn(str(linked), json.dumps(secondary))
        self.assertEqual(secondary["L4_discovery"], "NOT_VERIFIED")

    def test_no_index_client_config_or_tracked_content_mutation(self):
        codex = self.repo / ".codex" / "config.toml"
        claude = self.repo / ".claude" / "settings.json"
        codex.parent.mkdir()
        claude.parent.mkdir()
        codex.write_text("[mcp_servers]\n", encoding="utf-8")
        claude.write_text('{"mcpServers":{}}', encoding="utf-8")
        tracked = self.repo / "tracked.txt"
        protected = (self.repo / ".git" / "index",
                     self.repo / ".git" / "config", codex, claude, tracked)
        before = {str(p): p.read_bytes() for p in protected}
        self._data(client="codex")
        self._data(client="claude-code")
        self._data(client="hermes")
        self.assertEqual(before, {str(p): p.read_bytes() for p in protected})
        self.assertFalse((self.repo / ".adt").exists())
        self.assertFalse(list(self.repo.rglob("*.lock")))

    def test_inherited_git_overrides_cannot_forge_observations_or_write_trace(self):
        baseline = self._data()["project"]
        rogue = self.folder / "rogue-git"
        rogue.mkdir()
        self._git("init", "-q", "-b", "other", repo=rogue)
        foreign_index = self.folder / "foreign-index"
        trace = self.folder / "external-git-trace.json"
        injections = (
            {"GIT_INDEX_FILE": str(foreign_index),
             "GIT_TRACE2_EVENT": str(trace)},
            {"GIT_DIR": str(rogue / ".git"),
             "GIT_WORK_TREE": str(self.repo),
             "GIT_INDEX_FILE": str(foreign_index),
             "GIT_TRACE2_EVENT": str(trace),
             "GIT_CONFIG_COUNT": "1",
             "GIT_CONFIG_KEY_0": "core.fsmonitor",
             "GIT_CONFIG_VALUE_0": "true"},
        )
        for override in injections:
            with self.subTest(override=tuple(sorted(override))):
                with patch.dict(os.environ, override):
                    observed = self._data()
                self.assertEqual(observed["project"], baseline)
        self.assertFalse(foreign_index.exists())
        self.assertFalse(trace.exists())

    def test_invalid_roots_and_arguments_fail_closed_without_path_leaks(self):
        nested = self.repo / "nested"
        nested.mkdir()
        unrelated = self.folder / "not-a-repo"
        unrelated.mkdir()
        for kwargs in (
            {"project": nested},
            {"project": unrelated},
            {"project": "relative/path"},
            {"client": "unsupported"},
            {"unexpected": "true"},
        ):
            with self.subTest(kwargs=kwargs):
                result = self._call(**kwargs)
                self.assertTrue(result.get("isError"), result)
                self.assertNotIn(str(self.folder), json.dumps(result))
                self.assertNotIn("SENSITIVE_OBSERVER_FIXTURE", json.dumps(result))

    def test_linked_project_root_fails_without_exposing_private_path(self):
        alias = self.folder / "root-symlink"
        try:
            alias.symlink_to(self.repo, target_is_directory=True)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"Symlink creation not permitted: {type(exc).__name__}")
        observed = self._call(project=alias)
        self.assertTrue(observed.get("isError"), observed)
        self.assertNotIn(str(alias), json.dumps(observed))

    def test_linked_git_metadata_fails_without_exposing_private_path(self):
        git_dir = self.repo / ".git"
        actual = self.folder / "actual-git-directory"
        git_dir.rename(actual)
        try:
            git_dir.symlink_to(actual, target_is_directory=True)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"Symlink creation not permitted: {type(exc).__name__}")
        observed = self._call()
        self.assertTrue(observed.get("isError"), observed)
        self.assertNotIn(str(self.repo), json.dumps(observed))

    @unittest.skipUnless(os.name == "nt", "Windows junction-specific regression")
    def test_windows_junction_project_root_denied(self):
        alias = self.folder / "root-junction"
        proc = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(self.repo)],
                              capture_output=True)
        if proc.returncode:
            self.skipTest("Windows junction creation is unavailable")
        observed = self._call(project=alias)
        self.assertTrue(observed.get("isError"), observed)
        self.assertNotIn(str(alias), json.dumps(observed))

    def test_access_denial_fails_closed_and_exposes_no_exception_path(self):
        with patch.object(mcp, "_handoff_module") as module:
            module.return_value._git.side_effect = PermissionError(
                "SENSITIVE_OBSERVER_FIXTURE /private/access-denied")
            observed = self._call()
        self.assertTrue(observed.get("isError"), observed)
        self.assertNotIn("SENSITIVE_OBSERVER_FIXTURE", json.dumps(observed))
        self.assertNotIn("/private/access-denied", json.dumps(observed))


if __name__ == "__main__":
    unittest.main()
