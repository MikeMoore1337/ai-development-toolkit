"""Skill Quality v2 evidence regressions; synthetic offline fixtures only."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts import validate_quality
from scripts.validate_pack import validate_skill

ROOT = Path(__file__).resolve().parents[1]
LEVELS = validate_quality.EVIDENCE_LEVELS


class EvidenceContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.artifact = self.root / "evidence.txt"
        self.artifact.write_text("synthetic only\n", encoding="utf-8")
        self.path = self.root / "quality/evidence/alpha.json"
        self.path.parent.mkdir(parents=True)
        registry = self.root / "compatibility/clients.json"
        registry.parent.mkdir(parents=True)
        registry.write_text(json.dumps({"clients": [{"client_id": "codex"}]}), encoding="utf-8")

    def record(self):
        return {"schema_version": 1, "skill_id": "alpha", "source_revision": "a" * 40,
                "levels": {name: {"status": "NOT_MEASURED"} for name in LEVELS}}

    def artifact_ref(self):
        return {"path": "evidence.txt", "sha256": hashlib.sha256(self.artifact.read_bytes()).hexdigest()}

    def check(self, rec):
        if rec is not None:
            self.path.write_text(json.dumps(rec), encoding="utf-8")
        findings = []
        validate_quality.check_evidence(self.root, {"alpha"}, findings)
        return findings

    def bad(self, rec):
        self.assertTrue(any(f.rule_id == "EVIDENCE001" for f in self.check(rec)))

    def test_legacy_without_evidence(self):
        self.assertEqual([], self.check(None))

    def test_valid_unmeasured_repeat(self):
        rec = self.record()
        self.assertEqual([], self.check(rec))
        self.assertEqual(self.check(rec), self.check(rec))

    def test_valid_source_with_pinned_artifact(self):
        rec = self.record()
        rec["levels"]["source_validated"] = {"status": "PASS", "method": "offline fixture",
            "artifacts": [self.artifact_ref()]}
        self.assertEqual([], self.check(rec))

    def test_fake_success_missing_artifacts(self):
        rec = self.record()
        rec["levels"]["source_validated"] = {"status": "PASS", "method": "trust me"}
        self.bad(rec)

    def test_skipped_stage_not_promoted(self):
        rec = self.record()
        rec["levels"]["effective"] = {"status": "PASS", "method": "test",
            "artifacts": [self.artifact_ref()], "comparison": {}}
        self.bad(rec)

    def test_not_measured_cannot_claim_activation(self):
        rec = self.record()
        rec["levels"]["activated"]["client_id"] = "codex"
        self.bad(rec)

    def test_bad_revision_and_skill(self):
        rec = self.record()
        rec["source_revision"] = "main"
        self.bad(rec)
        rec = self.record()
        rec["skill_id"] = "ghost"
        self.bad(rec)

    def test_bad_hash_and_escape(self):
        rec = self.record()
        rec["levels"]["source_validated"] = {"status": "PASS", "method": "offline",
            "artifacts": [{"path": "evidence.txt", "sha256": "b" * 64}]}
        self.bad(rec)
        rec["levels"]["source_validated"]["artifacts"][0]["path"] = "../evidence.txt"
        self.bad(rec)

    def test_runtime_requires_review_and_known_client(self):
        rec = self.record()
        for level in LEVELS[:4]:
            rec["levels"][level] = {"status": "PASS", "method": "synthetic",
                "artifacts": [self.artifact_ref()]}
        self.bad(rec)
        for level in LEVELS[2:4]:
            rec["levels"][level].update(environment="test machine", reviewed_by="fixture reviewer",
                observed_at="2026-10-19T12:00:00Z")
        rec["levels"]["discovered"]["client_id"] = "unknown-client"
        self.bad(rec)

    def test_conflicting_fail_status(self):
        rec = self.record()
        rec["levels"]["activated"] = {"status": "FAIL"}
        self.bad(rec)

    def test_legacy_skill_metadata_still_valid(self):
        self.assertEqual([], validate_skill(ROOT / ".agents/skills/implementation"))

    def test_positive_template_metadata_and_links(self):
        folder = ROOT / "templates/skill-quality-v2/example-skill"
        self.assertEqual([], validate_skill(folder))
        failures = []
        validate_quality.check_markdown(ROOT, sorted(folder.rglob("*.md")), failures)
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
