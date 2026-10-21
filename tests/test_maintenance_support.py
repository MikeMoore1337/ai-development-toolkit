"""Offline regressions for support contracts, evidence and release mapping."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_maintenance_support import audit, load, mutate, validate


class MaintenanceSupportTests(unittest.TestCase):
    def test_reference_models(self):
        for name in ("reference", "pre_release", "unreproduced", "rollback", "user_verified"):
            with self.subTest(name=name):
                self.assertEqual([], audit(load(name + ".json")))

    def test_all_broken_cases_rejected_by_independent_oracle(self):
        baseline = load("reference.json")
        cases = load("broken_cases.json")["cases"]
        self.assertGreaterEqual(len(cases), 24)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertIn(case["expected_error"],
                              audit(mutate(baseline, case["path"], case["value"])))
        self.assertEqual([], audit(baseline))

    def test_rollback_invalidates_old_customer_delivery_claim(self):
        case = load("rollback.json")
        case["message"]["claim"] = "CHANNEL_DEPLOYED"
        self.assertIn("CUSTOMER_CLAIM_UNSUPPORTED", audit(case))

    def test_user_confirmation_requires_correct_environment(self):
        case = load("user_verified.json")
        case["delivery"]["user_environment"] = "production"
        self.assertIn("USER_NOT_VERIFIED", audit(case))

    def test_unconfirmed_duplicate_cannot_close_report(self):
        case = load("reference.json")
        case["closure"]["status"] = "CLOSED"
        case["closure"]["reason"] = "CONFIRMED_DUPLICATE"
        self.assertIn("FALSE_CLOSURE", audit(case))

    def test_full_cli(self):
        self.assertEqual((5, len(load("broken_cases.json")["cases"])), validate())


if __name__ == "__main__":
    unittest.main()
