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

    def test_verification_uses_source_archive_and_no_privileged_token(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("/archive/refs/tags/", text)
        self.assertIn("python scripts/verify_checksums.py --archive-root", text)
        self.assertIn("persist-credentials: false", text)
        self.assertNotIn("secrets.", text)
        self.assertNotIn("pull_request_target", text)


if __name__ == "__main__":
    unittest.main()
