"""Offline review contracts for selective Spec Kit methods; no agent runtime."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "integrations" / "spec-kit" / "method_cases.json"


def verdict(case):
    kind = case["kind"]
    if kind == "quick":
        return "QUICK_EXISTING" if case["reversible"] else "CLARIFY"
    if kind == "bug":
        if not case["reproduced"]:
            return "NOT_REPRODUCED"
        return "READY_TO_VERIFY" if case["test_executed"] else "NOT_VERIFIED"
    if kind == "idea":
        if not case["needed"]:
            return "STOP"
        return "GO" if case["evidence_verified"] and case["owner_gate_clear"] else "CLARIFY"
    raise ValueError("unknown kind")


class SpecKitSelectiveMethodTests(unittest.TestCase):
    def test_pinned_cases(self):
        data = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], 1)
        self.assertRegex(data["upstream_sha"], r"^[0-9a-f]{40}$")
        ids = [c["id"] for c in data["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({c["language"] for c in data["cases"]}, {"ru", "en"})
        self.assertEqual({c["kind"] for c in data["cases"]}, {"bug", "idea", "quick"})
        for case in data["cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(verdict(case), case["expected"])

    def test_no_unverified_bug_pass(self):
        for reproduced in (True, False):
            for executed in (True, False):
                result = verdict({"kind": "bug", "reproduced": reproduced, "test_executed": executed})
                if not reproduced or not executed:
                    self.assertNotEqual(result, "READY_TO_VERIFY")

    def test_idea_requires_verified_evidence_and_permissions(self):
        for verified in (True, False):
            for permitted in (True, False):
                for needed in (True, False):
                    result = verdict({"kind": "idea", "evidence_verified": verified, "owner_gate_clear": permitted, "needed": needed})
                    if result == "GO":
                        self.assertTrue(verified and permitted and needed)

    def test_unknown_kind_fails(self):
        with self.assertRaises(ValueError):
            verdict({"kind": "auto_deploy"})


if __name__ == "__main__":
    unittest.main()
