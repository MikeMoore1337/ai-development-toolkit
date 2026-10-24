"""Offline rejection tests for the opt-in Task Observer -> Toolkit handoff."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import skill_observation_review as gate


GOOD = {
    "schema_version": 1,
    "observations": [{
        "observation_id": "obs-1",
        "skill_id": "qa-strategy",
        "category": "missing-evidence",
        "source_url": "https://github.com/example/repo/issues/123",
    }],
}


class ObservationReviewTest(unittest.TestCase):
    def packet(self):
        return json.loads(json.dumps(GOOD))

    def rejects(self, packet, reason):
        with self.assertRaisesRegex(ValueError, reason):
            gate.review_packet(packet)

    def test_valid_requires_independent_review(self):
        report = gate.review_packet(self.packet())
        self.assertEqual("REVIEW_ONLY", report["decision"])
        self.assertFalse(report["curator_executed"])
        self.assertFalse(report["client_activation_verified"])
        self.assertFalse(report["items"][0]["evidence_verified"])
        self.assertEqual("MANUAL_REVIEW_REQUIRED", report["items"][0]["disposition"])

    def test_rejects_raw_chat_or_secret_fields(self):
        p = self.packet()
        p["observations"][0]["raw_prompt"] = "PRIVATE CONTENT"
        self.rejects(p, "INVALID_FIELDS")

    def test_rejects_token_in_url(self):
        p = self.packet()
        p["observations"][0]["source_url"] += "?token=secret"
        self.rejects(p, "INVALID_SOURCE")

    def test_rejects_non_github_source(self):
        p = self.packet()
        p["observations"][0]["source_url"] = "http://localhost/admin"
        self.rejects(p, "INVALID_SOURCE")

    def test_rejects_unbounded_identifiers(self):
        p = self.packet()
        p["observations"][0]["skill_id"] = "../.ssh/id_rsa"
        self.rejects(p, "INVALID_IDENTIFIER")

    def test_rejects_duplicate_observations(self):
        p = self.packet()
        p["observations"].append(dict(p["observations"][0]))
        self.rejects(p, "DUPLICATE_ID")

    def test_rejects_invalid_category(self):
        p = self.packet()
        p["observations"][0]["category"] = "auto-approve"
        self.rejects(p, "INVALID_CATEGORY")

    def test_rejects_boolean_schema_version(self):
        p = self.packet()
        p["schema_version"] = True
        self.rejects(p, "INVALID_VERSION")

    def test_rejects_empty_or_too_many(self):
        p = self.packet()
        p["observations"] = []
        self.rejects(p, "INVALID_COUNT")
        p["observations"] = [self.packet()["observations"][0]] * 21
        self.rejects(p, "INVALID_COUNT")

    def test_rejects_privacy_fields_at_top_level(self):
        p = self.packet()
        p["session_transcript"] = []
        self.rejects(p, "INVALID_SCHEMA")

    def test_main_smoke_no_writes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "packet.json"
            p.write_text(json.dumps(self.packet()), encoding="utf-8")
            old = p.read_bytes()
            self.assertEqual(0, gate.main(["--input", str(p)]))
            self.assertEqual(old, p.read_bytes())

    def test_main_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "valid.json"
            target.write_text(json.dumps(self.packet()), encoding="utf-8")
            link = Path(d) / "link.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks unavailable on this runner")
            self.assertEqual(2, gate.main(["--input", str(link)]))


if __name__ == "__main__":
    unittest.main()
