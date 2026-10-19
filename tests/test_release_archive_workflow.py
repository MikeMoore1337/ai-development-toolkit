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
