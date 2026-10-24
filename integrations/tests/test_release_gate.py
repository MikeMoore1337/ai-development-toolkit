"""Offline acceptance and negative fixtures for opt-in permanent release gate."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from integrations.release_gate import (
    EXPECTED_JOBS, ReleaseBlocked, select_run, validate_sha, verify_bundles,
    verify_jobs,
)

SHA = "a" * 40
RUN = {"id": 123, "event": "push", "head_branch": "main",
       "head_sha": SHA, "status": "completed", "conclusion": "success"}


class ReleaseGateTests(unittest.TestCase):
    def test_workflow_is_manual_sha_gated_and_never_replaces_toolkit_latest(self):
        root = Path(__file__).resolve().parents[2]
        text = (root / ".github/workflows/publish-integration-sources.yml").read_text()
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("  push:", text)
        self.assertIn("if: github.ref == 'refs/heads/main'", text)
        self.assertIn("git merge-base --is-ancestor", text)
        self.assertIn("python scripts/validate_provenance.py --mode release", text)
        self.assertIn("integrations/release_gate.py", text)
        self.assertIn("gh release create", text)
        self.assertIn("--latest=false --draft", text)
        # Regression: GitHub's /releases/latest can change despite --latest=false.
        self.assertIn('stable_latest="$(gh api --method GET', text)
        self.assertIn('if [[ ! "$stable_latest" =~ ^v[0-9]+', text)
        self.assertIn('if [[ "$latest_after" != "$stable_latest" ]]', text)
        self.assertIn('gh release edit "$stable_latest" --latest', text)
        self.assertIn('if [[ "$latest_final" != "$stable_latest" ]]', text)
        self.assertIn("gh release download", text)
        self.assertIn("gh release edit", text)
        text = (root / ".github/workflows/release-archive.yml").read_text(encoding="utf-8")
        self.assertIn("github.event_name != 'release' || startsWith", text)

    def test_exact_main_successful_run_only(self):
        self.assertEqual(select_run(SHA, {"workflow_runs": [RUN]}), 123)
        bad = [
            {**RUN, "event": "pull_request"},
            {**RUN, "head_branch": "feature"},
            {**RUN, "head_sha": "b" * 40},
            {**RUN, "conclusion": "failure"},
            {**RUN, "status": "in_progress"},
            {**RUN, "id": True},
        ]
        for fixture in bad:
            with self.subTest(fixture=fixture):
                with self.assertRaises(ReleaseBlocked):
                    select_run(SHA, {"workflow_runs": [fixture]})
        for sha in ("", "a" * 39, "A" * 40, "main", "a" * 40 + "\n"):
            with self.subTest(sha=sha), self.assertRaises(ReleaseBlocked):
                validate_sha(sha)

    def test_all_six_jobs_must_pass(self):
        jobs = [{"name": n, "status": "completed", "conclusion": "success"}
                for n in EXPECTED_JOBS]
        verify_jobs({"jobs": jobs})
        with self.assertRaises(ReleaseBlocked):
            verify_jobs({"jobs": jobs[:-1]})
        with self.assertRaises(ReleaseBlocked):
            verify_jobs({"jobs": jobs + jobs[:1]})
        for conclusion in ("skipped", "failure", None):
            with self.subTest(conclusion=conclusion), self.assertRaises(ReleaseBlocked):
                verify_jobs({"jobs": [{**x, "conclusion": conclusion} if i == 0 else x
                                      for i, x in enumerate(jobs)]})

    def test_source_zip_and_pair_integrity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            specs = [
                ("AI-Development-Toolkit-Personal-MCP-0.1.10.zip",
                 ["adt-personal/mcp/adt_mcp.py", "adt-personal/mcp/adt_discovery.py"]),
                ("AI-Development-Toolkit-ChatGPT-Plugin-0.1.2.zip",
                 ["ai-development-toolkit/plugin.json"]),
            ]
            results = []
            for name, members in specs:
                with ZipFile(root / name, "w") as archive:
                    for m in members:
                        archive.writestr(m, "source")
                results.append({"path": str(root / name),
                                "members": len(members),
                                "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()})
            build = {"status": "SOURCE_ARCHIVES_BUILT_NOT_INSTALLED",
                     "results": results, "mcp_source_version": "0.1.10",
                     "plugin_package_version": "0.1.2"}
            hashes, details = verify_bundles(build, root)
            self.assertEqual(len(hashes), 2)
            self.assertEqual(details["chatgpt_installed_plugin"], "NOT_VERIFIED")
            with self.assertRaises(ReleaseBlocked):
                verify_bundles({**build, "results": [{**results[0], "sha256": "0" * 64}, results[1]]}, root)
            with self.assertRaises(ReleaseBlocked):
                verify_bundles({**build, "results": [results[0], results[0]]}, root)
            with self.assertRaises(ReleaseBlocked):
                verify_bundles({**build, "results": results[:-1]}, root)


if __name__ == "__main__":
    unittest.main()
