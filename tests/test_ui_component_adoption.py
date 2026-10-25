"""Synthetic safety regression gates for generic UI component adoption (#408)."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_ui_component_adoption as gate  # noqa: E402


def candidate() -> dict:
    return {
        "schema_version": 1, "candidate": "Example button", "source": "shadcn-ui/ui",
        "decision": "PROPOSAL_ONLY", "consumer_revision": "UNKNOWN",
        "observed_problem": "Synthetic focus order is unclear.",
        "reuse_evidence": "The existing button was reviewed in synthetic context.",
        "license": "MIT_REVIEWED", "source_revision": "a" * 40,
        "new_dependencies": [], "performance": {"status": "NOT_MEASURED",
                                                    "before_bytes": None, "after_bytes": None},
        "accessibility": "NOT_TESTED", "reduced_motion": "NOT_TESTED",
        "visual_evidence": [], "owner_approval": {"status": "PENDING", "evidence_ref": None},
        "tests": "NOT_EXECUTED", "remote_services": [],
    }


class UIComponentAdoptionTests(unittest.TestCase):
    def test_proposal_is_not_implementation(self):
        self.assertEqual([], gate.validate(candidate()))

    def test_no_unknown_sources_or_write_services(self):
        value = candidate()
        value["source"] = "unverified-framework"
        value["remote_services"] = ["remote"]
        issues = gate.validate(value)
        self.assertIn("INVALID_DECISION_OR_SOURCE", issues)
        self.assertIn("NO_REMOTE_SERVICES_ALLOWED", issues)

    def test_external_code_requires_pinned_upstream_and_license(self):
        value = candidate()
        value["source_revision"] = None
        value["license"] = "ASSUMED_MIT"
        issues = gate.validate(value)
        self.assertIn("UPSTREAM_PIN_REQUIRED", issues)
        self.assertIn("LICENSE_NOT_REVIEWED", issues)

    def test_implementation_fails_without_real_approval_and_checks(self):
        value = candidate()
        value["decision"] = "IMPLEMENT_APPROVED"
        errors = gate.validate(value)
        for code in ("EXACT_CONSUMER_SHA_REQUIRED", "ACCESSIBILITY_NOT_TESTED",
                     "MOTION_NOT_TESTED", "VISUAL_EVIDENCE_MISSING",
                     "OWNER_VISUAL_GATE_MISSING", "ACTUAL_TEST_EVIDENCE_REQUIRED"):
            self.assertIn(code, errors)

    def test_dependency_addition_requires_measured_cost(self):
        value = candidate()
        value.update(decision="IMPLEMENT_APPROVED", consumer_revision="b" * 40,
                     new_dependencies=["motion"])
        value["owner_approval"] = {"status": "OWNER_ACCEPTED", "evidence_ref": "issue:123"}
        value["visual_evidence"] = ["screenshot:demo"]
        value["accessibility"] = value["reduced_motion"] = "TESTED"
        value["tests"] = "PASS_EXACT_SHA"
        self.assertIn("MEASURED_BUNDLE_COST_REQUIRED", gate.validate(value))
        value["performance"] = {"status": "MEASURED", "before_bytes": 1000, "after_bytes": 1010}
        self.assertEqual([], gate.validate(value))

    def test_boolean_byte_counts_not_accepted(self):
        value = candidate()
        value.update(decision="IMPLEMENT_APPROVED", consumer_revision="b" * 40,
                     new_dependencies=["motion"])
        value["owner_approval"] = {"status": "OWNER_ACCEPTED", "evidence_ref": "issue:123"}
        value["visual_evidence"] = ["screenshot:demo"]
        value["accessibility"] = value["reduced_motion"] = "TESTED"
        value["tests"] = "PASS_EXACT_SHA"
        value["performance"] = {"status": "MEASURED", "before_bytes": True, "after_bytes": 1}
        self.assertIn("MEASURED_BUNDLE_COST_REQUIRED", gate.validate(value))

    def test_proposal_cannot_claim_exact_sha_tests(self):
        value = candidate()
        value["tests"] = "PASS_EXACT_SHA"
        self.assertIn("PREMATURE_IMPLEMENTATION_CLAIM", gate.validate(value))

    def test_main_reads_local_only_and_no_writes(self):
        value = candidate()
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "packet.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            before = path.read_bytes()
            self.assertEqual(0, gate.main([str(path)]))
            self.assertEqual(before, path.read_bytes())

    def test_docs_and_existing_skill_references(self):
        en = (ROOT / "docs/en/UI_COMPONENT_SELECTION.md").read_text(encoding="utf-8")
        ru = (ROOT / "docs/ru/UI_COMPONENT_SELECTION.md").read_text(encoding="utf-8")
        for doc in (en, ru):
            for v in ("shadcn-ui/ui", "magicuidesign/magicui", "reduced-motion",
                      "OWNER_ACCEPTED", "REUSE_EXISTING", "PROPOSAL_ONLY"):
                self.assertIn(v, doc)
        paths = ("extensions/frontend/skills/component-architecture/SKILL.md",
                 ".agents/skills/motion-quality/SKILL.md",
                 ".agents/skills/ux-ui-design-orchestra/references/SPECIALISTS.md")
        for path in paths:
            self.assertIn("UI_COMPONENT_SELECTION.md", (ROOT / path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
