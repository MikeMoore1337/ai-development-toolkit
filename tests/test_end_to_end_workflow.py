"""Independent offline reference and mutation tests for Issue #67."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_end_to_end_workflow import audit, load, mutate, validate


class EndToEndWorkflowTests(unittest.TestCase):
    def test_reference_is_valid_and_only_synthetic(self):
        case = load("reference.json")
        self.assertEqual([], audit(case))
        self.assertEqual("INCOMPLETE", case["outcome"])
        self.assertFalse(case["actions"]["change"])
        self.assertFalse(case["release"]["deployed"])

    def test_negative_mutations_all_rejected_with_explanation(self):
        good = load("reference.json")
        cases = load("broken_cases.json")["cases"]
        self.assertGreaterEqual(len(cases), 44)
        for item in cases:
            with self.subTest(item=item["id"]):
                bad = mutate(good, item["path"], item["value"])
                self.assertIn(item["expected_error"], audit(bad))
        self.assertEqual([], audit(good))

    def test_quick_and_deep_reference_routes(self):
        quick = load("quick.json")
        deep = load("deep.json")
        self.assertEqual([], audit(quick))
        self.assertEqual([], audit(deep))
        self.assertEqual(["implementation", "qa"],
                         [item["id"] for item in quick["stages"]])
        self.assertEqual("deep", deep["mode"])
        self.assertTrue(deep["gates"]["security_applicable"])

    def test_resume_is_idempotent_no_mutation(self):
        case = load("reference.json")
        before = copy.deepcopy(case)
        for _ in range(3):
            self.assertEqual([], audit(case))
        self.assertEqual(before, case)

    def test_sha_change_requires_revalidation(self):
        case = load("reference.json")
        case["resume"]["current_head"] = "SYNTHETIC-REV-2"
        self.assertIn("STALE_EVIDENCE", audit(case))
        case["resume"]["revalidation"] = True
        self.assertEqual([], audit(case))

    def test_local_blocker_not_global_stop(self):
        case = load("reference.json")
        self.assertEqual("COMPLETE", case["stages"][1]["status"])
        self.assertEqual("PROPOSED", case["stages"][6]["status"])
        self.assertEqual("BLOCKED", case["release"]["state"])
        self.assertEqual([], audit(case))

    def test_cli(self):
        count, invalid = validate()
        self.assertEqual((1, len(load("broken_cases.json")["cases"])), (count, invalid))


if __name__ == "__main__":
    unittest.main()
