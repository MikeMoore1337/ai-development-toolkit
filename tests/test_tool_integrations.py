"""Independent positive and deliberately broken offline Issue #69 contracts."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_tool_integrations as v


class IntegrationContractTests(unittest.TestCase):
    def test_three_synthetic_reference_flows(self):
        for name in ("github.json", "figma.json", "server.json"):
            with self.subTest(name=name):
                case = v.read(name)
                self.assertEqual([], v.audit(case))
                self.assertFalse(case["integration"]["install_attempted"])
                self.assertFalse(case["execution"]["reported_executed"])
                self.assertFalse(case["storage"]["toolkit_written"])

    def test_broken_cases_have_independent_error_oracles(self):
        cases = v.read("broken.json")["cases"]
        self.assertGreaterEqual(len(cases), 36)
        for mutation in cases:
            with self.subTest(case=mutation["id"]):
                original = v.read(mutation["scenario"] + ".json")
                invalid = v.mutated(original, mutation["path"], mutation["value"])
                self.assertIn(mutation["error"], v.audit(invalid))
                self.assertEqual([], v.audit(original))

    def test_repeated_validation_is_read_only(self):
        fixture = v.read("github.json")
        original = __import__("copy").deepcopy(fixture)
        for _ in range(3):
            self.assertEqual([], v.audit(fixture))
        self.assertEqual(original, fixture)

    def test_no_external_services_or_live_state(self):
        count, mutants = v.validate()
        self.assertEqual(3, count)
        self.assertGreaterEqual(mutants, 36)
        for name in ("github.json", "figma.json", "server.json"):
            record = v.read(name)
            self.assertTrue(record["synthetic"])
            self.assertFalse(record["execution"]["live_access"])
            self.assertIn(record["execution"]["status"], {"PREPARED", "BLOCKED"})


if __name__ == "__main__":
    unittest.main()
