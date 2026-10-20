"""Issue #58: independent expected states and known-bad negative implementations."""
from __future__ import annotations

import ast
import copy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install import skill_sources
from skill_manager import operate, read_state
from validate_reliability import (
    CASES, CASE_IDS, MUTANTS, load_cases, run_case, simulate, validate_case,
)


class ReliabilityTests(unittest.TestCase):
    def test_fixture_contract_complete_and_versioned(self):
        cases = load_cases()
        self.assertEqual(len(CASE_IDS), len(cases))
        self.assertEqual(set(CASE_IDS), {case["case_id"] for case in cases})
        for case in cases:
            with self.subTest(case=case["case_id"]):
                self.assertFalse(validate_case(case))
                self.assertIsInstance(case["expected_persistent_state"], dict)

    def test_reference_passes_same_oracles_as_mutants(self):
        for case in load_cases():
            with self.subTest(case=case["case_id"]):
                good = run_case(case)
                bad = run_case(case, mutant=True)
                self.assertEqual("PASS", good["oracle_outcome"])
                self.assertEqual("FAIL", bad["oracle_outcome"])
                self.assertNotEqual(good["observed_state"], bad["observed_state"])
                self.assertEqual(case["business_invariant"], good["tested_invariant"])
                self.assertEqual(len(good["input_sha256"]), 64)

    def test_recovery_status_is_not_invented_for_other_cases(self):
        records = {case["case_id"]: run_case(case) for case in load_cases()}
        self.assertEqual("RECOVERED", records["restart-recovery"]["recovery_outcome"])
        self.assertEqual("NOT_APPLICABLE",
                         records["duplicate-delivery"]["recovery_outcome"])
        self.assertEqual("STATE_UNKNOWN",
                         run_case(load_cases()[0], mutant=True)["recovery_outcome"])

    def test_every_known_mutation_has_a_case(self):
        self.assertEqual(set(CASE_IDS), set(MUTANTS))
        self.assertEqual(len(MUTANTS), len(set(MUTANTS.values())))

    def test_missing_invariant_is_rejected(self):
        case = copy.deepcopy(load_cases()[0])
        case["business_invariant"] = ""
        self.assertIn("missing business invariant", validate_case(case))

    def test_false_execution_claim_rejected(self):
        case = copy.deepcopy(load_cases()[0])
        case["actual_evidence"] = "production PASS"
        self.assertIn("fixture must not claim execution evidence", validate_case(case))

    def test_unbounded_case_rejected(self):
        case = copy.deepcopy(load_cases()[0])
        case["execution_bound"] = 0
        self.assertIn("unsafe execution bound", validate_case(case))

    def test_unknown_status_rejected(self):
        case = copy.deepcopy(load_cases()[0])
        case["result_status"] = "EXACTLY_ONCE"
        self.assertIn("unknown result status", validate_case(case))

    def test_recovery_reopens_sqlite_connection(self):
        observed = simulate("restart-recovery")
        self.assertEqual({"count": 6, "unique_events": 1}, observed)
        self.assertEqual({"count": 12, "unique_events": 1},
                         simulate("restart-recovery", mutant=True))

    def test_timeout_after_effect_does_not_duplicate(self):
        self.assertEqual({"count": 9, "unique_events": 1},
                         simulate("timeout-after-effect"))

    def test_lost_update_under_forced_schedule(self):
        self.assertEqual({"count": 11}, simulate("lost-update"))
        self.assertEqual({"count": 7}, simulate("lost-update", mutant=True))

    def test_retry_bounded_without_real_delay(self):
        good = simulate("retry-budget")
        self.assertEqual(3, good["attempts"])
        self.assertEqual([1, 2], good["delays"])
        self.assertEqual(4, simulate("retry-budget", mutant=True)["attempts"])

    def test_ack_does_not_precede_durable_effect(self):
        self.assertEqual({"acknowledged": False, "count": 0},
                         simulate("ack-before-commit"))
        self.assertEqual({"acknowledged": True, "count": 0},
                         simulate("ack-before-commit", mutant=True))

    def test_no_external_network_or_subprocess_imports(self):
        source = (ROOT / "scripts/validate_reliability.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        modules = {alias.name.split(".")[0] for node in ast.walk(tree)
                   if isinstance(node, ast.Import) for alias in node.names}
        modules |= {node.module.split(".")[0] for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) and node.module}
        self.assertFalse(modules & {"socket", "subprocess", "requests", "urllib",
                                    "http", "openai", "anthropic"})

    def test_profile_preview_and_apply_through_existing_manager(self):
        import json
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        path = ROOT / "extensions/reliability/skills/reliability-testing"
        self.assertEqual(path, skill_sources(manifest)["reliability-testing"])
        chosen = manifest["profiles"]["reliability-testing"]
        self.assertEqual(["reliability-testing", "background-processing",
                          "integration-testing", "failure-triage"], chosen)
        self.assertNotIn("reliability-testing", manifest["profiles"]["general"])
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)
            for layout in ("codex", "claude"):
                preview = operate("install", dest, names=chosen, layout=layout)
                self.assertFalse(preview["applied"])
                parent = ".agents" if layout == "codex" else ".claude"
                self.assertFalse((dest / parent).exists())
                installed = operate("install", dest, names=chosen,
                                    layout=layout, apply=True)
                self.assertTrue(installed["applied"])
                self.assertIn("reliability-testing", read_state(dest, layout)["skills"])


if __name__ == "__main__":
    unittest.main()
