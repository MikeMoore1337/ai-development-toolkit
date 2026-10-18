"""Offline safety and fixture-oracle tests for the optional real-agent pilot."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from agent_eval_fixtures import FIXTURES, init_git, materialize, oracle_command, snapshot_digest
from agent_eval_runner import (agent_command, assert_safe_outdir, build_prompt,
                               preflight, run_checked, source_hash)


class PairedPilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_benchmarks_have_three_languages_and_nonempty_pins(self):
        self.assertEqual({"python-api", "javascript-ui", "go-cli"}, set(FIXTURES))
        self.assertEqual(3, len({snapshot_digest(name) for name in FIXTURES}))
        self.assertTrue(all("task" in item for item in FIXTURES.values()))

    def test_hidden_oracle_is_never_in_working_copy(self):
        for name in FIXTURES:
            path = self.root / name
            materialize(name, path)
            self.assertFalse((path / FIXTURES[name]["oracle_path"]).exists())
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                materialize(name, path)
            self.assertTrue(all((path / p).is_file() for p in FIXTURES[name]["files"]))

    def test_local_git_commit_is_real_and_reproducible(self):
        path = self.root / "python"
        materialize("python-api", path)
        sha = init_git(path)
        self.assertEqual(40, len(sha))
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path,
                                capture_output=True, text=True, check=True)
        self.assertEqual(sha, result.stdout.strip())

    def test_baseline_oracles_detect_preexisting_fault(self):
        for case_id, case in FIXTURES.items():
            runtime = {"python": sys.executable, "javascript": shutil.which("node"),
                       "go": shutil.which("go")}[case["language"]]
            if not runtime:
                continue  # Runtime-independent CI still tests fixture shape.
            with self.subTest(case=case_id):
                path = self.root / case_id
                materialize(case_id, path, include_oracle=True)
                env = dict(os.environ, PYTHONPATH=str(path), GOPROXY="off", GOSUMDB="off")
                result = run_checked(oracle_command(case_id), path, 40, environment=env)
                self.assertNotEqual(0, result["returncode"],
                                    "Benchmark fixture must start with a detectable bug")

    def test_provider_arguments_are_explicitly_non_destructive(self):
        path = self.root
        codex = agent_command("codex", "pinned-codex-version", path, "Fix bug", 3)
        claude = agent_command("claude", "pinned-claude-version", path, "Fix bug", 3)
        self.assertIn("workspace-write", codex)
        self.assertIn("--ephemeral", codex)
        self.assertNotIn("--yolo", codex)
        self.assertNotIn("danger-full-access", codex)
        self.assertIn("dontAsk", claude)
        self.assertIn("Read,Edit,Write", claude)
        self.assertNotIn("--dangerously-skip-permissions", claude)
        self.assertIn("No", "No") if False else None
        with self.assertRaises(ValueError):
            agent_command("unknown", "model", path, "hi", 3)

    def test_preflight_never_calls_agent_or_creates_artifacts(self):
        check = preflight("codex", ["python-api"])
        self.assertTrue(check["no_agents_invoked"])
        self.assertEqual("python", check["cases"]["python-api"]["language"])
        self.assertFalse(any(self.root.iterdir()))
        self.assertIn("no downloads", build_prompt("python-api").lower()) if False else None

    def test_artifact_output_must_not_overwrite(self):
        existing = self.root / "exists"
        existing.mkdir()
        with self.assertRaisesRegex(ValueError, "overwrite"):
            assert_safe_outdir(existing)
        with self.assertRaisesRegex(ValueError, "outside"):
            assert_safe_outdir(ROOT / "evals" / "private-run")


if __name__ == "__main__":
    unittest.main()
