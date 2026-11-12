"""Cloudflare-inspired optional coverage ledger: synthetic, source-only tests."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_security as security  # noqa: E402


def sample():
    return {
        "scope": "fictional-notes/authz-only", "source_sha": "a" * 40,
        "units": [
            {"id": "u1", "boundary": "client-to-service", "attack_class": "IDOR",
             "source_location": "fixture/notes.py:12", "status": "covered",
             "evidence": "synthetic allow/deny oracle", "evidence_level": "SYNTHETIC_TESTED"},
            {"id": "u2", "boundary": "client-to-service", "attack_class": "expired-session",
             "source_location": "fixture/notes.py:20", "status": "planned"},
        ],
        "findings": [
            {"id": "F1", "unit_id": "u2", "source_sha": "a" * 40,
             "source_location": "fixture/notes.py:20",
             "verdict": "needs_validation", "blocker": "No expiry test evidence"},
        ],
    }


def confirmed():
    record = sample()
    record["units"][1].update(status="covered", evidence="synthetic expiry oracle",
                               evidence_level="SYNTHETIC_TESTED")
    record["findings"][0].update(
        unit_id="u1", verdict="confirmed", evidence="in-memory hypothetical result",
        evidence_level="SYNTHETIC_TESTED", reproduction="fixture owner-A reads owner-B note",
        observed_result="synthetic forbidden result", impact="fictional disclosure",
        severity="medium", hunter_id="synthetic-hunter", verifier_id="synthetic-verifier")
    del record["findings"][0]["blocker"]
    return record


class CoverageEvidenceTests(unittest.TestCase):
    def test_baseline_does_not_ensure_attack_surface_coverage(self):
        security.validate_packet(security.sample_packet())
        result = security.validate_audit_coverage(sample())
        self.assertEqual((2, 1, 1), (result["in_scope"], result["covered"],
                                     result["unresolved_findings"]))
        self.assertFalse(result["coverage_plan_complete"])
        with self.assertRaises(ValueError):
            security.validate_audit_coverage(sample(), require_complete=True)

    def test_structurally_complete_synthetic_does_not_claim_real_audit(self):
        result = security.validate_audit_coverage(confirmed(), require_complete=True)
        self.assertTrue(result["coverage_plan_complete"])
        self.assertEqual(result["evidence_class"], "STRUCTURE_VALIDATED")
        self.assertEqual(result["runtime_audit"], "NOT_RUN")

    def test_fake_confirmations_are_rejected(self):
        mutations = (
            lambda r: r["findings"][0].update(verifier_id="synthetic-hunter"),
            lambda r: r["findings"][0].update(evidence_level="SOURCE_ONLY"),
            lambda r: r["findings"][0].update(source_sha="b" * 40),
            lambda r: r["findings"][0].update(unit_id="unknown"),
            lambda r: r["findings"][0].update(evidence=""),
            lambda r: r["units"][0].update(status="planned"),
            lambda r: r["units"][0].update(evidence_level="invented"),
            lambda r: r["units"][1].update(id="u1"),
            lambda r: r.update(source_sha="not-a-SHA"),
        )
        for mutation in mutations:
            record = confirmed()
            mutation(record)
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    security.validate_audit_coverage(record)

    def test_deferred_and_unconfirmed_findings(self):
        for state in ("deferred", "out_of_scope"):
            record = sample()
            record["units"][1].update(status=state, reason="not currently authorized")
            record["findings"] = []
            self.assertEqual(
                security.validate_audit_coverage(record)["coverage_plan_complete"],
                state == "out_of_scope")
        for verdict, addition in (("needs_validation", {"severity": "high"}),
                                  ("rejected", {"disproof": ""})):
            record = sample()
            record["findings"][0].update(verdict=verdict, **addition)
            with self.assertRaises(ValueError):
                security.validate_audit_coverage(record)

    def test_cli_read_only_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "coverage.json"
            path.write_text(json.dumps(sample()), encoding="utf-8")
            cmd = [sys.executable, str(ROOT / "scripts/validate_security.py"),
                   "--coverage-json", str(path)]
            ok = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertFalse(json.loads(ok.stdout)["coverage_plan_complete"])
            blocked = subprocess.run(cmd + ["--require-complete"],
                                     capture_output=True, text=True, check=False)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertEqual(json.loads(blocked.stdout)["status"], "INVALID_COVERAGE_RECORD")
            path.write_text("invalid-json PRIVATE_FIXTURE", encoding="utf-8")
            invalid = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertNotIn("PRIVATE_FIXTURE", invalid.stdout)


if __name__ == "__main__":
    unittest.main()
