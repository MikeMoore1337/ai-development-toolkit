"""Independent synthetic oracle and mutation regressions for #64 (offline)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_dependency_maintenance import FIXTURES, affected, graph_diff, graph_index, inspect, load, patch


class DependencyMaintenanceContracts(unittest.TestCase):
    def test_good_reference_cases(self):
        for name in ("ordinary", "security"):
            with self.subTest(name=name):
                self.assertEqual([], inspect(load(name)))

    def test_mutations_are_rejected_by_same_oracle(self):
        cases = json.loads((FIXTURES / "broken_cases.json").read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len(cases), 20)
        for case in cases:
            with self.subTest(case=case["id"]):
                baseline = load(case["base"])
                self.assertEqual([], inspect(baseline))
                violations = inspect(patch(baseline, case["changes"]))
                self.assertIn(case["expected_error"], violations)

    def test_transitive_change_not_hidden_by_single_direct_upgrade(self):
        source = load("ordinary")
        diff = graph_diff(graph_index(source["old_graph"]), graph_index(source["new_graph"]))
        self.assertIn("alpha-core", diff)
        self.assertIn("gamma-lib", diff)
        self.assertFalse(diff["gamma-lib"]["direct"])
        self.assertEqual(2, len(diff))

    def test_advisory_outside_range_not_assumed_vulnerable(self):
        source = load("security")
        self.assertEqual([], inspect(source))
        wrong = patch(source, [{"path": "advisory.applicability",
                                "value": "NOT_AFFECTED_BY_RANGE"}])
        self.assertIn("AFFECTED_RANGE", inspect(wrong))

    def test_security_affected_range_boundaries(self):
        self.assertTrue(affected("1.4.0", "1.0.0", "1.5.0"))
        self.assertFalse(affected("1.5.0", "1.0.0", "1.5.0"))
        self.assertFalse(affected("0.9.0", "1.0.0", "1.5.0"))

    def test_no_implicit_runtime_or_lockfile_parser_claims(self):
        sample = load("ordinary")
        self.assertFalse(sample["claims"]["real_lockfile_parser"])
        self.assertEqual("SYNTHETIC", sample["origin"])
        self.assertEqual("COMPLETE_SYNTHETIC_GRAPH", sample["transitive_status"])
        self.assertIn("ECOSYSTEM_CLAIM", inspect(patch(sample, [
            {"path": "claims.real_lockfile_parser", "value": True}])))


if __name__ == "__main__":
    unittest.main()
