"""Static contract for published-release archive verification workflow."""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release-archive.yml"


class ReleaseArchiveWorkflowTests(unittest.TestCase):
    def test_publication_event_and_manual_tag_are_declared(self):
        config = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        self.assertEqual(["published"], config["on"]["release"]["types"])
        self.assertEqual("true", config["on"]["workflow_dispatch"]["inputs"]["tag"]["required"])
        self.assertEqual("read", config["permissions"]["contents"])
        self.assertEqual("ubuntu-latest", config["jobs"]["release-archive"]["runs-on"])

    def test_new_tag_fail_closed_when_registry_validator_is_absent(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('if [[ "${GITHUB_EVENT_NAME}" == "push" ]]; then', text)
        self.assertIn("BLOCKED: refusing a new release tag", text)
        self.assertIn('python "$archive_root/scripts/validate_provenance.py"', text)
        self.assertIn("--mode release", text)

    def test_archive_rejects_tag_manifest_version_mismatch(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('RELEASE_TAG: ${{', text)
        self.assertIn('"MANIFEST.json"', text)
        self.assertIn('manifest.get("version")', text)
        self.assertIn('"BLOCKED: release tag and MANIFEST.json.version disagree"', text)

    def test_published_release_checks_live_main_documentation(self):
        config = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        job = config["jobs"]["published-documentation"]
        self.assertIn("release", job["if"])
        self.assertIn("published", job["if"])
        self.assertEqual("main", job["steps"][0]["with"]["ref"])
        script = job["steps"][1]["run"]
        self.assertIn("PUBLICATION_DOCS_STALE", script)
        for path in ("README.md", "README.ru.md", "CHANGELOG.md",
                     "docs/RELEASE_PROCESS.md", "docs/ru/RELEASE_PROCESS.md"):
            self.assertIn(path, script)

    def test_release_docs_keep_archive_and_documentation_status_separate(self):
        en = (ROOT / "docs/RELEASE_PROCESS.md").read_text(encoding="utf-8")
        ru = (ROOT / "docs/ru/RELEASE_PROCESS.md").read_text(encoding="utf-8")
        config = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        self.assertIn("release-archive", config["jobs"])
        self.assertIn("published-documentation", config["jobs"])
        for page in (en, ru):
            self.assertIn("PUBLICATION_DOCS_STALE", page)
            self.assertIn("release-archive=SUCCESS", page)
            self.assertIn("published-documentation", page)
            self.assertIn("LOCAL_PRETAG_BLOCKED", page)

    def test_macos_gate_is_a_dependency_of_required_checks(self):
        """macOS ARM/Intel failure prevents required Linux/Windows jobs from passing."""
        workflow = ROOT / ".github" / "workflows" / "validate.yml"
        config = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        jobs = config["jobs"]
        self.assertEqual("macos-portability", jobs["tests"]["needs"])
        self.assertNotIn("if", jobs["macos-portability"])
        self.assertEqual(
            ["macos-15", "macos-15-intel"],
            jobs["macos-portability"]["strategy"]["matrix"]["os"],
        )
        self.assertIn("tests", jobs["integration-source-candidates"]["needs"])
        self.assertIn("macos-portability", jobs["integration-source-candidates"]["needs"])

    def test_required_matrix_enforces_release_snapshot(self):
        workflow = ROOT / ".github" / "workflows" / "validate.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("Confirm exact owner-reviewed release source snapshot", text)
        self.assertIn("scripts/validate_provenance.py --mode release", text)
        self.assertIn("provenance-release-preflight.json", text)
        self.assertIn("git archive --format=zip", text)
        self.assertIn("scripts/verify_checksums.py --archive-root", text)
        self.assertIn("provenance-archive-preflight.json", text)

    def test_verification_uses_source_archive_and_no_privileged_token(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("/archive/refs/tags/", text)
        self.assertIn("python scripts/verify_checksums.py --archive-root", text)
        self.assertIn("persist-credentials: false", text)
        self.assertNotIn("secrets.", text)
        self.assertNotIn("pull_request_target", text)


if __name__ == "__main__":
    unittest.main()
