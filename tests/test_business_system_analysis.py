"""Issue #55 - deterministic structural tests; real AI-client activation NOT_MEASURED."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install import skill_sources
from skill_manager import operate, read_state
from validate_system_spec import validate

SKILL = ROOT / "extensions/analysis/skills/business-system-analysis"
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
CONTRACT = json.loads((SKILL / "references/SYSTEM_SPEC_CONTRACT.json").read_text(encoding="utf-8"))
EXAMPLE = json.loads((SKILL / "references/EXAMPLE_EXPENSES.json").read_text(encoding="utf-8"))


class BusinessSystemAnalysisTests(unittest.TestCase):
    def sample(self):
        return copy.deepcopy(EXAMPLE)

    def test_manifest_profile_reuse_and_no_second_controller(self):
        self.assertEqual(SKILL, skill_sources(MANIFEST)["business-system-analysis"])
        self.assertEqual(["business-system-analysis"],
                         MANIFEST["extension_packs"]["analysis"]["skills"])
        chosen = MANIFEST["profiles"]["business-system-analysis"]
        self.assertEqual(["business-system-analysis", "task-scoping",
                          "requirement-analysis", "requirements-traceability"], chosen)
        self.assertNotIn("business-system-analysis", MANIFEST["profiles"]["general"])
        for forbidden in ("feature-delivery", "make-feature", "adaptive-delivery", "qa-all"):
            self.assertNotIn(forbidden, chosen)

    def test_skill_portable_boundaries_and_refs(self):
        content = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for token in ("Positive triggers:", "Negative triggers:", "read-only",
                      "in chat by default", "CONTRACT_PENDING", "UNVERIFIED_DEPENDENCY",
                      "NOT_MEASURED", "architecture-decisions", "api-design"):
            self.assertIn(token, content)
        for ref in ("WORKFLOW.md", "EXAMPLES.md", "EXAMPLE_EXPENSES.json",
                    "SYSTEM_SPEC_CONTRACT.json", "MANUAL_ACCEPTANCE.md"):
            self.assertTrue((SKILL / "references" / ref).is_file())

    def test_example_preserves_source_ids_trace_and_is_read_only(self):
        self.assertEqual([], validate(self.sample()))
        self.assertEqual({"R1", "R2", "R3"},
                         {x["id"] for x in EXAMPLE["source_requirements"]})
        self.assertEqual({"AC1", "AC2", "AC3", "AC4"},
                         {x["id"] for x in EXAMPLE["acceptance_criteria"]})
        self.assertEqual({"NOT_WRITTEN"}, {x["test_status"] for x in EXAMPLE["traceability"]})

    def test_preview_does_not_write_and_explicit_install_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for layout in ("codex", "claude"):
                before = sorted(target.rglob("*"))
                preview = operate("install", target, names=["business-system-analysis"],
                                  layout=layout, apply=False)
                self.assertFalse(preview["applied"])
                self.assertEqual(before, sorted(target.rglob("*")))
                installed = operate("install", target, names=["business-system-analysis"],
                                    layout=layout, apply=True)
                self.assertTrue(installed["applied"])
                self.assertIn("business-system-analysis", read_state(target, layout)["skills"])
            for unexpected in ("reports", "specs", "logs", "tmp"):
                self.assertFalse((target / unexpected).exists())

    def test_source_absence_duplicate_and_semantics(self):
        p = self.sample()
        p["source_requirements"][0].pop("source")
        self.assertTrue(any("missing" in x for x in validate(p)))
        p = self.sample()
        p["source_requirements"][1]["id"] = "R1"
        self.assertTrue(any("duplicate ID" in x for x in validate(p)))
        p = self.sample()
        p["source_requirements"][1]["behavior"] = p["source_requirements"][0]["behavior"]
        self.assertTrue(any("duplicate requirement behavior" in x for x in validate(p)))

    def test_lost_ac_and_bad_references(self):
        p = self.sample()
        p["acceptance_criteria"].pop()
        self.assertTrue(any("invalid acceptance_ids" in x for x in validate(p)))
        p = self.sample()
        p["system_requirements"][0]["parent_requirement_id"] = "R404"
        self.assertTrue(any("unknown parent R-ID" in x for x in validate(p)))
        p = self.sample()
        p["traceability"][0]["acceptance_id"] = "AC4"
        self.assertTrue(any("broken R->SR->AC" in x for x in validate(p)))

    def test_rule_truth_and_structured_contradiction(self):
        p = self.sample()
        p["business_rules"][0]["source"] = "ASSUMPTION"
        self.assertTrue(any("unverified business rule" in x for x in validate(p)))
        p = self.sample()
        other = copy.deepcopy(p["business_rules"][0])
        other.update(id="BR3", polarity="ALLOW")
        p["business_rules"].append(other)
        self.assertTrue(any("UNRESOLVED_CONFLICT" in x for x in validate(p)))

    def test_use_case_must_have_error_path_and_check(self):
        p = self.sample()
        p["use_cases"][0]["alternative_or_error_path"] = []
        self.assertTrue(any("alternative_or_error_path" in x for x in validate(p)))
        p = self.sample()
        p["use_cases"][0]["verification"] = ""
        self.assertTrue(any("missing verification" in x for x in validate(p)))

    def test_nfr_measurement_or_unknown(self):
        p = self.sample()
        p["nonfunctional_requirements"][0]["verification"] = "UNKNOWN"
        self.assertTrue(any("untestable NFR" in x for x in validate(p)))
        p = self.sample()
        p["nonfunctional_requirements"][0]["status"] = "CONFIRMED"
        self.assertTrue(any("invented confirmed NFR" in x for x in validate(p)))

    def test_integration_missing_contract(self):
        p = self.sample()
        p["integrations"].append({"id": "I1", "provider": "external", "consumer": "journal",
                                  "purpose": "sync", "data": "expenses",
                                  "contract": "CONTRACT_PENDING", "status": "KNOWN",
                                  "error_handling": "UNKNOWN", "security": "UNKNOWN",
                                  "compatibility": "UNKNOWN", "open_questions": []})
        self.assertTrue(any("CONTRACT_PENDING" in x for x in validate(p)))
        p["integrations"][0]["status"] = "CONTRACT_PENDING"
        self.assertEqual([], validate(p))

    def test_unapproved_decision_and_scope_creep(self):
        p = self.sample()
        p["decisions"][0]["status"] = "APPROVED"
        self.assertTrue(any("without evidence" in x for x in validate(p)))
        p = self.sample()
        p["system_requirements"][0]["scope"] = "OUT"
        self.assertTrue(any("PROPOSED_OUT_OF_SCOPE" in x for x in validate(p)))

    def test_no_fake_pass_or_bpmn_and_unknown_status(self):
        p = self.sample()
        p["traceability"][0]["test_status"] = "PASS"
        self.assertTrue(any("test claimed" in x for x in validate(p)))
        self.assertTrue(any("unexecuted test" in x for x in validate(p)))
        p = self.sample()
        p["processes"][0]["notation"] = "BPMN_2_0_VERIFIED"
        self.assertTrue(any("BPMN" in x for x in validate(p)))
        p = self.sample()
        p["business_rules"][0]["status"] = "MADE_UP"
        self.assertTrue(any("invalid rule status" in x for x in validate(p)))

    def test_empty_incomplete_input(self):
        self.assertTrue(validate({}))
        self.assertTrue(validate({"schema_version": 1}))
        self.assertTrue(validate(None))

    def test_contract_handoff_and_source_parity(self):
        self.assertEqual("PROPOSED_NOT_IMPLEMENTED", CONTRACT["artifact_status"])
        self.assertEqual(["ux_ui", "backend", "frontend", "qa"], CONTRACT["handoff_targets"])
        self.assertEqual({"USER_PROVIDED", "SOURCE_BACKED", "OBSERVED", "ASSUMPTION", "UNKNOWN"},
                         set(CONTRACT["source_labels"]))
        for path in ("docs/BUSINESS_SYSTEM_ANALYSIS.md", "docs/ru/BUSINESS_SYSTEM_ANALYSIS.md"):
            self.assertTrue((ROOT / path).is_file())


if __name__ == "__main__":
    unittest.main()
