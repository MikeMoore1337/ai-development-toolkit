"""No observations become validated scores without explicit independent review."""
from __future__ import annotations

import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from agent_eval_review import build_reports
from skill_eval import EvalInputError


class ReviewGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        records, decisions = [], []
        for variant in ("baseline", "candidate"):
            name = f"python-api-t1-{variant}"
            evidence = self.root / name / "oracle.stdout.txt"
            evidence.parent.mkdir()
            evidence.write_text("Synthetic-only fixture proof\n", encoding="utf-8")
            records.append({
                "case_id": "python-api", "trial": 1, "variant": variant,
                "fixture_commit_sha": "a" * 40, "cli": {
                    "returncode": 0, "timed_out": False, "duration_seconds": 13.5
                }, "oracle": {"returncode": 0, "timed_out": False},
                "evidence": [f"{name}/oracle.stdout.txt"],
                "evidence_sha256": {
                    f"{name}/oracle.stdout.txt": hashlib.sha256(evidence.read_bytes()).hexdigest()
                },
            })
            decisions.append({
                "case_id": "python-api", "trial": 1, "variant": variant,
                "accepted": variant == "candidate",
                "unsafe_actions": 0, "regressions": 0,
                "skill_activation_observed": variant == "candidate",
                "notes": "Reviewed synthetic fixture checks and model changes.",
            })
        self.observations = {
            "schema_version": 1, "executed": True, "dataset": "synthetic-only",
            "provider": "codex", "model": "synthetic-model", "records": records,
        }
        self.reviews = {
            "reviewer": "Independent Example Reviewer", "independent_review_attested": True,
            "decisions": decisions,
        }

    def build(self):
        return build_reports(self.observations, self.reviews, self.root)

    def test_explicit_review_produces_exploratory_scores_only(self):
        summary = self.build()["python-api"]["summary"]
        self.assertEqual(1, summary["pairs"])
        self.assertEqual("exploratory", summary["classification"])
        self.assertEqual(100.0, summary["acceptance_delta_percentage_points"])
        self.assertIsNone(summary["candidate"]["mean_tokens"])
        self.assertEqual(1, summary["skill_activation_observed"]["candidate_trials"])
        self.assertTrue(summary["independent_review_required"])

    def test_no_unreviewed_run_can_be_reported(self):
        self.reviews["decisions"].pop()
        with self.assertRaisesRegex(EvalInputError, "Missing reviewer verdicts"):
            self.build()

    def test_requires_attested_named_reviewer(self):
        self.reviews["independent_review_attested"] = False
        with self.assertRaisesRegex(EvalInputError, "independence"):
            self.build()

    def test_hidden_oracle_must_pass_for_acceptance(self):
        self.observations["records"][1]["oracle"]["returncode"] = 1
        with self.assertRaisesRegex(EvalInputError, "Cannot accept"):
            self.build()

    def test_agent_failure_cannot_be_accepted(self):
        self.observations["records"][1]["cli"]["timed_out"] = True
        with self.assertRaisesRegex(EvalInputError, "Cannot accept"):
            self.build()

    def test_missing_safety_verdict_fails_closed(self):
        del self.reviews["decisions"][0]["unsafe_actions"]
        with self.assertRaisesRegex(EvalInputError, "unsafe_actions"):
            self.build()

    def test_activation_cannot_be_assumed(self):
        self.reviews["decisions"][0]["skill_activation_observed"] = True
        with self.assertRaisesRegex(EvalInputError, "Baseline"):
            self.build()

    def test_tampered_evidence_is_rejected(self):
        p = self.root / "python-api-t1-candidate" / "oracle.stdout.txt"
        p.write_text("Changed after run", encoding="utf-8")
        with self.assertRaisesRegex(EvalInputError, "Evidence altered"):
            self.build()

    def test_missing_evidence_is_rejected(self):
        (self.root / "python-api-t1-baseline" / "oracle.stdout.txt").unlink()
        with self.assertRaisesRegex(EvalInputError, "missing or linked evidence"):
            self.build()


if __name__ == "__main__":
    unittest.main()
