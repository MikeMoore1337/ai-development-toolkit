"""Read-only negative and positive pre-tag scenarios, without GitHub calls."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pretag_under_test", ROOT / "scripts/pre_tag_preflight.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

SHA = "1" * 40
TAG = "v9.8.7"


class PreTagGateTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "MANIFEST.json").write_text(json.dumps({"version": "9.8.7"}), encoding="utf-8")

    def local_git(self, *, dirty: bool = False, tag_exists: bool = False):
        outputs = {
            "rev-parse --show-toplevel": str(self.root),
            "rev-parse HEAD": SHA,
            "status --porcelain --untracked-files=normal": " M docs/file.md" if dirty else "",
            "tag --list v9.8.7": TAG if tag_exists else "",
        }

        def invoke(argv, **kwargs):
            key = " ".join(argv[3:])
            if key not in outputs:
                raise AssertionError("unexpected git command: " + key)
            return SimpleNamespace(returncode=0, stdout=outputs[key] + "\n")
        return invoke

    def test_local_preflight_clean_exact_revision(self) -> None:
        with patch.object(gate.subprocess, "run", side_effect=self.local_git()):
            gate.local_preflight(self.root, TAG, SHA)

    def test_local_preflight_blocks_dirty_worktree(self) -> None:
        with patch.object(gate.subprocess, "run", side_effect=self.local_git(dirty=True)):
            with self.assertRaisesRegex(gate.GateBlocked, "WORKTREE_NOT_CLEAN"):
                gate.local_preflight(self.root, TAG, SHA)

    def test_local_preflight_blocks_existing_tag(self) -> None:
        with patch.object(gate.subprocess, "run", side_effect=self.local_git(tag_exists=True)):
            with self.assertRaisesRegex(gate.GateBlocked, "TAG_EXISTS_LOCALLY"):
                gate.local_preflight(self.root, TAG, SHA)

    def test_local_preflight_blocks_manifest_mismatch(self) -> None:
        with self.assertRaisesRegex(gate.GateBlocked, "TAG_MANIFEST_VERSION_MISMATCH"):
            gate.local_preflight(self.root, "v9.8.6", SHA)

    def test_local_preflight_blocks_invalid_sha(self) -> None:
        with self.assertRaises(gate.GateBlocked):
            gate.local_preflight(self.root, TAG, "not-a-sha")

    def responses(self, *, tag_found: bool = False, wrong_branch: bool = False,
                  failed_ci: bool = False):
        checks = [{"name": name, "status": "completed", "conclusion": "success"}
                  for name in sorted(gate.REQUIRED)]
        if failed_ci:
            checks[0]["conclusion"] = "failure"
        return {
            "git/ref/tags/" + TAG: (200, {"ref": TAG}) if tag_found else (404, {}),
            "branches/main": (200, {"commit": {"sha": "0" * 40 if wrong_branch else SHA}}),
            "commits/" + SHA + "/check-runs?per_page=100": (
                200, {"total_count": len(checks), "check_runs": checks}),
        }

    def test_remote_preflight_green(self) -> None:
        responses = self.responses()
        with patch.object(gate, "github_get", side_effect=lambda path, token=None: responses[path]):
            gate.remote_preflight(TAG, SHA)

    def test_remote_blocks_existing_tag(self) -> None:
        responses = self.responses(tag_found=True)
        with patch.object(gate, "github_get", side_effect=lambda path, token=None: responses[path]):
            with self.assertRaisesRegex(gate.GateBlocked, "TAG_ALREADY_EXISTS"):
                gate.remote_preflight(TAG, SHA)

    def test_remote_blocks_wrong_main(self) -> None:
        responses = self.responses(wrong_branch=True)
        with patch.object(gate, "github_get", side_effect=lambda path, token=None: responses[path]):
            with self.assertRaisesRegex(gate.GateBlocked, "REMOTE_MAIN_SHA_MISMATCH"):
                gate.remote_preflight(TAG, SHA)

    def test_remote_blocks_failed_ci(self) -> None:
        responses = self.responses(failed_ci=True)
        with patch.object(gate, "github_get", side_effect=lambda path, token=None: responses[path]):
            with self.assertRaisesRegex(gate.GateBlocked, "REQUIRED_CI_NOT_GREEN"):
                gate.remote_preflight(TAG, SHA)

    def test_remote_blocks_unavailable_api(self) -> None:
        with patch.object(gate, "github_get", side_effect=gate.GateBlocked("GitHub unavailable")):
            with self.assertRaises(gate.GateBlocked):
                gate.remote_preflight(TAG, SHA)


if __name__ == "__main__":
    unittest.main()
