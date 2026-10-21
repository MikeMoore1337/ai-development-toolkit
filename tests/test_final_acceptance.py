"""Issue #70: independent regression assertions for offline acceptance evidence."""
from __future__ import annotations

import copy
import unittest

from scripts.validate_end_to_end_workflow import audit as existing_oracle
from scripts.validate_final_acceptance import (
    PHASES, STAGES, audit, load, mutate, report, workflow_fixture,
)


class FinalAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = load()
        cls.negatives = load("broken_cases.json")["cases"]

    def test_reference_is_valid(self) -> None:
        self.assertEqual(audit(self.reference), [])

    def test_novice_and_expert_reuse_existing_oracle(self) -> None:
        for journey in self.reference["journeys"]:
            with self.subTest(journey=journey["id"]):
                workflow = workflow_fixture(journey)
                self.assertEqual(existing_oracle(workflow), [])
                self.assertEqual([s["id"] for s in workflow["stages"]], list(PHASES))
                self.assertEqual(set(workflow["original_r_ids"]),
                                 set(journey["original_r_ids"]))
                self.assertEqual(set(workflow["original_ac_ids"]),
                                 set(journey["original_ac_ids"]))
                self.assertFalse(workflow["actions"]["paid_api"])
                self.assertFalse(workflow["release"]["deployed"])
                self.assertEqual(workflow["acceptance_claim"], "NOT_TESTED")

    def test_negative_mutations_fail_deterministically(self) -> None:
        ids = [case["id"] for case in self.negatives]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 35)
        for case in self.negatives:
            with self.subTest(case=case["id"]):
                data = copy.deepcopy(self.reference)
                for patch in case.get("patches", [case]):
                    data = mutate(data, patch["path"], patch.get("value"),
                                  delete=patch.get("delete", False))
                once = audit(data)
                self.assertIn(case["expected_error"], once)
                self.assertEqual(once, audit(data))

    def test_source_coverage_keeps_live_checks_separate(self) -> None:
        result = report(self.reference)
        coverage = result["coverage_source_presence_only"]
        self.assertEqual(set(coverage), set(STAGES))
        for stage, counts in coverage.items():
            self.assertGreater(counts["total"], 0, stage)
            self.assertEqual(
                counts["total"], sum(counts[s] for s in (
                    "PASS", "FAIL", "BLOCKED", "NOT_TESTED",
                    "NOT_APPLICABLE", "INCONCLUSIVE")))
        self.assertEqual(result["independent_novice_usability"], "NOT_TESTED")
        self.assertEqual(result["live_skill_evals"], "BLOCKED")
        self.assertEqual(result["real_model_effectiveness"], "NOT_MEASURED")
        self.assertEqual(result["release_readiness"], "READY_FOR_REVIEW")
        self.assertEqual(result["actual_live_runs"], 0)
        self.assertEqual(result["negative_mutations_detected"], len(self.negatives))

    def test_no_actual_project_result_is_fabricated(self) -> None:
        for journey in self.reference["journeys"]:
            with self.subTest(id=journey["id"]):
                self.assertTrue(journey["synthetic"])
                self.assertEqual(journey["claims"]["implemented"], False)
                self.assertEqual(journey["claims"]["skill_invoked"], False)
                self.assertEqual(journey["experiment"]["status"], "BLOCKED")
                self.assertEqual(journey["independent_usability"]["status"], "NOT_TESTED")
                self.assertTrue(all(ac["status"] == "NOT_TESTED"
                                    for ac in journey["acceptance"]))
                self.assertTrue(all(not t["executed"] for t in journey["qa_tests"]))

    def test_prohibited_write_and_model_gate_remain_closed(self) -> None:
        self.assertFalse(any(self.reference["owner_actions"].values()))
        self.assertEqual(self.reference["skill_eval_gate"]["status"], "BLOCKED")
        self.assertFalse(self.reference["skill_eval_gate"]["owner_approval"])
        for journey in self.reference["journeys"]:
            self.assertFalse(journey["permissions"]["toolkit_write"])
            self.assertFalse(journey["permissions"]["paid_api"])
            self.assertFalse(journey["permissions"]["deploy"])


if __name__ == "__main__":
    unittest.main()
