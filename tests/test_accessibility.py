"""Issue #62: independent offline accessibility and evidence regressions."""
from __future__ import annotations

import ast
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install import skill_sources  # noqa: E402
from skill_manager import operate, read_state  # noqa: E402
import validate_accessibility as a11y  # noqa: E402


class AccessibilityTests(unittest.TestCase):
    def test_known_good_and_bad_markup(self):
        root = ROOT / "fixtures/accessibility"
        good = a11y.audit_fixture((root / "accessible.html").read_text(encoding="utf-8"))
        bad = a11y.audit_fixture((root / "inaccessible.html").read_text(encoding="utf-8"))
        self.assertEqual([], good)
        self.assertTrue({"MISSING_FORM_LABEL", "MISSING_ACCESSIBLE_NAME",
                         "INVALID_ARIA_REFERENCE", "UNLINKED_FORM_ERROR",
                         "MISSING_MAIN_LANDMARK"} <= set(bad))
        self.assertEqual("PASS", a11y.run_cases()["result"])
        self.assertEqual("NOT_TESTED", a11y.run_cases()["browser"])
        self.assertEqual("NOT_ASSESSED", a11y.run_cases()["wcag_conformance"])

    def test_structural_negative_mutations(self):
        html = (ROOT / "fixtures/accessibility/accessible.html").read_text(encoding="utf-8")
        variants = {
            "MISSING_FORM_LABEL": html.replace('for="amount"', 'for="other"'),
            "INVALID_ARIA_REFERENCE": html.replace('amount-help amount-error', 'ghost amount-error'),
            "UNLINKED_FORM_ERROR": html.replace('amount-help amount-error', 'amount-help'),
            "MISSING_ACCESSIBLE_NAME": html.replace('Сохранить запись</button>', '</button>'),
            "DUPLICATE_ID": html.replace('<h1>', '<p id="amount"></p><h1>'),
            "MISSING_MAIN_LANDMARK": html.replace('<main>', '<div>').replace('</main>', '</div>'),
        }
        for expected, mutant in variants.items():
            with self.subTest(expected=expected):
                self.assertIn(expected, a11y.audit_fixture(mutant))
        self.assertEqual([], a11y.audit_fixture(html))

    def test_contrast_formula_and_boundary_without_rounding(self):
        self.assertAlmostEqual(21.0, a11y.contrast_ratio("#000000", "#FFFFFF"))
        self.assertAlmostEqual(1.0, a11y.contrast_ratio("#123456", "#123456"))
        self.assertEqual("FAIL", a11y.check_contrast("#777777", "#ffffff", "normal_text")["status"])
        self.assertEqual("PASS", a11y.check_contrast("#767676", "#ffffff", "normal_text")["status"])
        self.assertEqual("PASS", a11y.check_contrast("#777777", "#ffffff", "large_text")["status"])
        self.assertEqual("PASS", a11y.check_contrast("#777777", "#ffffff", "ui_component")["status"])
        for invalid in ("transparent", "#abc", "#000000aa", "var(--color)", "", None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    a11y.contrast_ratio(invalid, "#ffffff")
        self.assertEqual("NOT_APPLICABLE",
                         a11y.check_contrast("#fff000", "#ffffff", "normal_text",
                                             "logo")["status"])
        with self.assertRaises(ValueError):
            a11y.check_contrast("#ffffff", "#ffffff", "normal_text", "spacing")
        with self.assertRaises(ValueError):
            a11y.check_contrast("#ffffff", "#ffffff", "unknown")

    def test_contract_statuses_and_criteria(self):
        base = a11y.reference_test()
        self.assertEqual([], a11y.validate_test(base))
        self.assertEqual("A", a11y.WCAG_LEVELS["2.4.3"])
        self.assertEqual("AA", a11y.WCAG_LEVELS["2.4.11"])
        self.assertEqual("AAA", a11y.WCAG_LEVELS["2.4.12"])
        for field in a11y.TEST_FIELDS:
            with self.subTest(field=field):
                mutant = copy.deepcopy(base)
                del mutant[field]
                self.assertIn("INVALID_TEST_CONTRACT", a11y.validate_test(mutant))
        for criterion, wrong_level in (("2.5.8", "A"), ("2.4.12", "AA"),
                                       ("2.4.3", "AA")):
            bad = copy.deepcopy(base)
            bad["criterion"], bad["level"] = criterion, wrong_level
            self.assertIn("WRONG_CRITERION_LEVEL", a11y.validate_test(bad))

    def test_unexecuted_checks_never_pass(self):
        base = a11y.reference_test()
        base["status"] = "PASS"
        self.assertIn("PASS_WITHOUT_EXECUTION", a11y.validate_test(base))
        base["evidence"] = {"executed": True, "observation": "can tab", "method": "STATIC"}
        self.assertIn("EVIDENCE_METHOD_MISMATCH", a11y.validate_test(base))
        self.assertIn("RUNTIME_NOT_VERIFIED", a11y.validate_test(base))
        base["evidence"]["method"] = "KEYBOARD"
        self.assertIn("RUNTIME_NOT_VERIFIED", a11y.validate_test(base))
        base["evidence"].update(operator="QA", environment="Firefox actual run")
        self.assertEqual([], a11y.validate_test(base))
        base["method"] = "ASSISTIVE_TECH"
        base["evidence"]["method"] = "ASSISTIVE_TECH"
        self.assertIn("ASSISTIVE_TECH_NOT_IDENTIFIED", a11y.validate_test(base))
        base["technology"] = "NVDA 2026"
        base["evidence"]["technology"] = "NVDA 2026"
        self.assertEqual([], a11y.validate_test(base))

    def test_coverage_and_false_conformance(self):
        test = a11y.reference_test()
        report = {"tests": [test], "required_criteria": ["2.1.1"],
                  "assessment": {"status": "NOT_ASSESSED"}}
        self.assertEqual([], a11y.validate_report(report))
        report["required_criteria"].append("1.4.3")
        self.assertIn("MISSING_REQUIRED_CRITERION", a11y.validate_report(report))
        report["required_criteria"].pop()
        for status in ("PASS", "CONFORMANT", "WCAG_2_2_AA"):
            report["assessment"] = {"status": status}
            self.assertIn("FALSE_WCAG_CONFORMANCE", a11y.validate_report(report))
        report["assessment"] = {"status": "NOT_ASSESSED"}
        test["status"] = "PASS"
        self.assertIn("PASS_WITHOUT_EXECUTION", a11y.validate_report(report))
        test["status"] = "NOT_APPLICABLE"
        test["limitations"] = ""
        self.assertIn("MISSING_APPLICABILITY_REASON", a11y.validate_report(report))

    def test_finding_priority_remediation_and_retest(self):
        self.assertEqual("BLOCKER", a11y.priority(True, False))
        self.assertEqual("HIGH", a11y.priority(True, True))
        self.assertEqual("LOW", a11y.priority(False, True))
        base = {k: "sample" for k in a11y.FINDING_FIELDS}
        base.update(status="POTENTIAL", severity="MEDIUM", evidence=None)
        self.assertEqual([], a11y.validate_finding(base))
        base["remediation"] = ""
        self.assertIn("MISSING_REMEDIATION", a11y.validate_finding(base))
        base["remediation"] = "Add label"
        base["status"] = "CONFIRMED"
        self.assertIn("UNSUPPORTED_FINDING_STATUS", a11y.validate_finding(base))
        base["evidence"] = {"observation": "label missing"}
        base["status"] = "RETEST_PASS"
        self.assertIn("RETEST_NOT_EXECUTED", a11y.validate_finding(base))
        base["evidence"]["retest_executed"] = True
        self.assertEqual([], a11y.validate_finding(base))

    def test_opt_in_profile_preview_apply_and_source_boundary(self):
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        names = manifest["profiles"]["accessibility-qa"]
        self.assertEqual(["accessibility-testing", "test-analysis-design",
                          "playwright-testing", "quality-gate-assessment"], names)
        self.assertNotIn("accessibility-testing", manifest["profiles"]["general"])
        source = skill_sources(manifest)["accessibility-testing"]
        self.assertEqual(ROOT / "extensions/accessibility/skills/accessibility-testing",
                         source)
        previous = (source / "SKILL.md").read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            for layout in ("codex", "claude"):
                destination = Path(temporary) / layout
                destination.mkdir()
                marker = destination / "AGENTS.md"
                marker.write_text("unmanaged\n", encoding="utf-8")
                preview = operate("install", destination, names=names, layout=layout)
                self.assertFalse(preview["applied"])
                self.assertEqual("unmanaged\n", marker.read_text(encoding="utf-8"))
                result = operate("install", destination, names=names,
                                 layout=layout, apply=True)
                self.assertTrue(result["applied"])
                self.assertEqual(set(names), set(read_state(destination, layout)["skills"]))
        self.assertEqual(previous, (source / "SKILL.md").read_bytes())

    def test_offline_validator_has_no_network_process_or_browser_imports(self):
        module = ast.parse((ROOT / "scripts/validate_accessibility.py").read_text(encoding="utf-8"))
        imported = {node.name.split(".")[0] for entry in ast.walk(module)
                    if isinstance(entry, ast.Import) for node in entry.names}
        imported |= {entry.module.split(".")[0] for entry in ast.walk(module)
                     if isinstance(entry, ast.ImportFrom) and entry.module}
        self.assertFalse(imported & {"socket", "urllib", "requests", "http",
                                     "subprocess", "playwright", "selenium", "os"})
        self.assertEqual("NOT_TESTED", a11y.run_cases()["assistive_technology"])


if __name__ == "__main__":
    unittest.main()

