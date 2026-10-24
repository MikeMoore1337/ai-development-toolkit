"""Five synthetic project portability classes, without private project access."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import project_portability_matrix as matrix


class ProjectPortabilityMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = matrix.load()

    def test_five_distinct_generic_classes_and_freeze(self):
        self.assertEqual(5, len(self.fixture["cases"]))
        self.assertEqual(list(matrix.IDS), [x["id"] for x in self.fixture["cases"]])
        self.assertEqual("3fb90c41162da1cb4f0fb58c15dc72729feb5703",
                         self.fixture["baseline_sha"])
        self.assertEqual("AI_ASSISTED_UNREVIEWED_SCENARIOS", self.fixture["author"])

    def test_readonly_qa_preflight_and_visual_gate(self):
        report = matrix.inspect()
        self.assertEqual(5, report["scenario_count"])
        self.assertEqual("NOT_RUN", report["real_client_L4_L5"])
        self.assertEqual("NOT_MEASURED", report["real_task_quality_L6"])
        self.assertFalse(report["mutations_to_real_projects"])
        expected = {
            "python-backend": "qa-python",
            "frontend-ui": "qa-ui",
            "fullstack": "qa-fullstack",
            "agent-service": "qa-python",
            "docs-heavy": "qa-core",
        }
        for case in report["cases"]:
            self.assertEqual(expected[case["project_class"]], case["selected_qa_profile"])
            self.assertTrue(case["required_expected_checks_present"])
            self.assertFalse(case["target_project_changed"])
            self.assertFalse(case["source_contents_read"])
            self.assertEqual("NOT_RUN", case["test_execution"])
            self.assertEqual("NOT_OBSERVED", case["human_visual_approval"])
            if case["visual_scenario"]:
                self.assertEqual("HUMAN_VISUAL_REVIEW_REQUIRED", case["visual_gate"])
                self.assertEqual(3, case["required_design_directions"])
                self.assertEqual("NOT_PRODUCED", case["rendered_visual_assets"])
            else:
                self.assertEqual("NOT_APPLICABLE", case["visual_gate"])

    def test_no_runnable_tests_claimed_for_docs_only(self):
        report = matrix.inspect()
        docs = next(x for x in report["cases"]
                    if x["project_class"] == "docs-heavy")
        self.assertIn("documentation-review", docs["risk_check_ids"])
        self.assertNotIn("targeted-unit", docs["risk_check_ids"])
        self.assertEqual([], docs["critical_check_ids"])

    def test_critical_risks_not_dropped(self):
        report = matrix.inspect()
        backend = next(x for x in report["cases"]
                       if x["project_class"] == "python-backend")
        agent = next(x for x in report["cases"]
                     if x["project_class"] == "agent-service")
        fullstack = next(x for x in report["cases"]
                         if x["project_class"] == "fullstack")
        for cid in ("db-migration", "db-rollback"):
            self.assertIn(cid, backend["critical_check_ids"])
            self.assertIn(cid, fullstack["critical_check_ids"])
        self.assertIn("auth-boundary", agent["critical_check_ids"])
        self.assertIn("cross-layer", fullstack["risk_check_ids"])

    def test_untrusted_path_and_wrong_profile_are_rejected(self):
        for change in (
            lambda data: data["cases"][0]["changed_paths"].append("../secret"),
            lambda data: data["cases"][0]["markers"].append("../private"),
            lambda data: data["cases"][0].update(qa_profile="unverified"),
            lambda data: data["cases"][1].update(visual_scenario="approved"),
            lambda data: data.update(author="INDEPENDENTLY_VALIDATED"),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                bad = copy.deepcopy(self.fixture)
                change(bad)
                file = Path(tmp) / "fixture.json"
                file.write_text(json.dumps(bad), encoding="utf-8")
                with self.assertRaises((matrix.PortabilityError, matrix.impact.ImpactInputError)):
                    matrix.load(file)

    def test_removed_qa_check_fails_closed(self):
        original = matrix.impact.plan

        def tampered(*args, **kwargs):
            result = original(*args, **kwargs)
            result["recommendations"] = [x for x in result["recommendations"]
                                         if x["id"] != "db-rollback"]
            return result

        with patch.object(matrix.impact, "plan", tampered):
            with self.assertRaisesRegex(matrix.PortabilityError,
                                        "QA risk selection lost"):
                matrix.inspect()

    def test_false_human_gate_fails_closed(self):
        original = matrix.ux_ui_evals.catalog

        def fake(root):
            result = copy.deepcopy(original(root))
            result["new-site"]["needs_three"] = False
            return result

        with patch.object(matrix.ux_ui_evals, "catalog", fake):
            with self.assertRaisesRegex(matrix.PortabilityError,
                                        "Visual approval gate missing"):
                matrix.inspect()


if __name__ == "__main__":
    unittest.main()
