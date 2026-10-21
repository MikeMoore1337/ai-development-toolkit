"""Offline negative oracles for Feature Delivery Orchestra (no live agent/API)."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_feature_orchestra as delivery


class DeliveryOrchestraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads((ROOT / "fixtures/feature_orchestra_valid.json").read_text(encoding="utf-8"))

    def trial(self):
        return copy.deepcopy(self.base)

    def rejects(self, code, trial):
        self.assertIn(code, delivery.validate(trial))

    def test_unhashable_risk_is_rejected(self):
        report = self.trial()
        report["risk_flags"] = [["privacy"]]
        self.rejects("INVALID_INPUT_SHAPE", report)

    def test_unhashable_write_scope_is_rejected(self):
        report = self.trial()
        report["units"][1]["write_paths"] = [{"path": "src/x.py"}]
        self.rejects("INVALID_INPUT_SHAPE", report)

    def test_unhashable_evidence_id_is_rejected(self):
        report = self.trial()
        report["checks"][0]["evidence_ids"] = [{"fake": "evidence"}]
        self.rejects("INVALID_INPUT_SHAPE", report)

    def test_more_than_three_sequential_steps_are_supported(self):
        report = self.trial()
        report["units"].append({
            "id": "security", "purpose": "Risk review on approved source",
            "role": "security-reviewer", "status": "PLANNED",
            "execution": "SEQUENTIAL", "trace": None,
            "write_paths": [], "depends_on": ["verify"]
        })
        self.assertEqual([], delivery.validate(report))

    def test_parallel_readers_and_one_sequential_writer(self):
        report = self.trial()
        report["execution"] = {"mode": "SUBAGENTS", "peak": 2}
        for index in [0, 2]:
            unit = report["units"][index]
            unit["execution"] = "GENERIC_SUBAGENT"
            unit["status"] = "EXECUTED"
            unit["trace"] = f"actual-delegation-receipt-{index}"
        report["units"][2]["depends_on"] = ["research"]
        self.assertEqual([], delivery.validate(report))

    def test_subagent_may_not_write_shared_branch(self):
        report = self.trial()
        report["execution"] = {"mode": "SUBAGENTS", "peak": 1}
        report["units"][0]["status"] = "EXECUTED"
        report["units"][0]["execution"] = "GENERIC_SUBAGENT"
        report["units"][0]["trace"] = "real-tool-receipt"
        report["units"][0]["role"] = "implementer"
        report["units"][0]["write_paths"] = ["src/unowned.py"]
        self.rejects("SUBAGENT_WRITE", report)

    def test_synthetic_plan_passes_but_not_executed(self):
        self.assertEqual([], delivery.validate(self.trial()))

    def test_multiple_controllers(self):
        report = self.trial()
        report["active_controllers"].append("make-feature")
        self.rejects("DUPLICATE_CONTROLLER", report)

    def test_high_risk_cannot_downgrade(self):
        report = self.trial()
        report["risk_flags"] = ["migration"]
        self.rejects("RISK_DOWNGRADE", report)

    def test_missing_human_approval(self):
        report = self.trial()
        report["risk_flags"] = ["visual"]
        self.rejects("MISSING_GATE", report)

    def test_unverified_approval(self):
        report = self.trial()
        report["risk_flags"] = ["visual"]
        report["approvals"] = [{"gate": "visual", "status": "ACCEPTED", "reference": None}]
        self.rejects("UNVERIFIED_APPROVAL", report)

    def test_only_one_writer(self):
        report = self.trial()
        report["units"][0]["role"] = "implementer"
        report["units"][0]["write_paths"] = ["src/other.py"]
        self.rejects("CONCURRENT_WRITERS", report)

    def test_no_write_by_reviewer(self):
        report = self.trial()
        report["units"][2]["write_paths"] = ["src/tasks.py"]
        self.rejects("WRITE_OWNER", report)

    def test_no_parent_escape(self):
        report = self.trial()
        report["units"][1]["write_paths"] = ["../vault/secrets"]
        self.rejects("WRITE_SCOPE", report)

    def test_bounded_workers(self):
        report = self.trial()
        report["execution"]["peak"] = 4
        self.rejects("EXECUTION", report)

    def test_sequential_cannot_fake_parallel(self):
        report = self.trial()
        report["execution"]["peak"] = 2
        self.rejects("FAKE_PARALLELISM", report)

    def test_actual_subagent_needs_trace(self):
        report = self.trial()
        report["units"][0]["execution"] = "GENERIC_SUBAGENT"
        report["units"][0]["status"] = "EXECUTED"
        self.rejects("FAKE_SUBAGENT", report)
        self.rejects("MISSING_TRACE", report)

    def test_missing_dependency(self):
        report = self.trial()
        report["units"][1]["depends_on"] = ["imaginary"]
        self.rejects("INVALID_DEPENDENCY", report)

    def test_dependency_cycle(self):
        report = self.trial()
        report["units"][0]["depends_on"] = ["verify"]
        self.rejects("DEPENDENCY_CYCLE", report)

    def test_dependency_cannot_skip_pending_work(self):
        report = self.trial()
        report["units"][1]["status"] = "EXECUTED"
        self.rejects("DEPENDENCY_NOT_COMPLETE", report)

    def test_acceptance_oracle_cannot_disappear(self):
        report = self.trial()
        report["acceptance"][0]["check_ids"] = ["T2"]
        self.rejects("MISSING_AC_CHECK", report)

    def test_unknown_evidence(self):
        report = self.trial()
        report["checks"][0]["evidence_ids"] = ["imaginary"]
        self.rejects("EVIDENCE_LOOKUP", report)

    def test_stale_evidence(self):
        report = self.trial()
        report["evidence"][0]["revision"] = "f" * 40
        self.rejects("STALE_EVIDENCE", report)

    def test_source_inspection_is_not_test_execution(self):
        report = self.trial()
        report["checks"][0]["status"] = "PASS"
        self.rejects("FALSE_EXECUTION", report)

    def test_premature_review_readiness(self):
        report = self.trial()
        report["outcome"] = "READY_FOR_REVIEW"
        self.rejects("PREMATURE_READY", report)

    def test_plan_cannot_claim_green(self):
        report = self.trial()
        report["checks"][0]["status"] = "PASS"
        self.rejects("PLAN_CANNOT_PASS", report)

    def test_clean_recorded_execution_can_claim_ready_for_review_only(self):
        report = self.trial()
        for unit in report["units"]:
            unit["status"] = "EXECUTED"
        report["checks"][0]["status"] = "PASS"
        report["checks"][0]["evidence_ids"] = ["real"]
        report["evidence"].append({
            "id": "real", "kind": "TEST_RUN", "revision": report["revision"],
            "reference": "SYNTHETIC TEST RECEIPT, example only; not real evidence"
        })
        report["outcome"] = "READY_FOR_REVIEW"
        self.assertEqual([], delivery.validate(report))
        self.assertNotIn("RELEASED", delivery.validate(report))


if __name__ == "__main__":
    unittest.main()
