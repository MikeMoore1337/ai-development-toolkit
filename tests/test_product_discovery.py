"""Offline Product Discovery contract, safe profile and synthetic evidence checks.

These are structural/deterministic checks, not real model or market evaluations.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install import skill_sources
from skill_manager import operate, read_state

SKILL = ROOT / "extensions/product/skills/product-discovery"
CONTRACT = json.loads((SKILL / "references/PRD_CONTRACT.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))


class ProductDiscoveryTests(unittest.TestCase):
    def test_unique_skill_and_optional_profile(self):
        self.assertEqual("extensions/product/skills", MANIFEST["extension_packs"]["product"]["skill_root"])
        self.assertEqual(["product-discovery"], MANIFEST["extension_packs"]["product"]["skills"])
        self.assertEqual(
            ["product-discovery", "task-scoping", "research-verification"],
            MANIFEST["profiles"]["product-discovery"],
        )
        self.assertEqual(SKILL, skill_sources(MANIFEST)["product-discovery"])
        self.assertNotIn("product-discovery", MANIFEST["profiles"]["general"])

    def test_skill_has_real_boundary_and_no_side_effect(self):
        content = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: product-discovery", content)
        self.assertIn("Positive triggers:", content)
        self.assertIn("Negative triggers:", content)
        self.assertIn("read-only", content)
        self.assertIn("in chat by default", content)
        self.assertIn("without explicit permission", content)
        self.assertIn("NOT_MEASURED", content)
        for reference in ("WORKFLOW.md", "PRD_CONTRACT.json", "EXAMPLES.md", "MANUAL_ACCEPTANCE.md"):
            self.assertTrue((SKILL / "references" / reference).is_file())

    def test_prd_contract_covers_traceable_requirements_and_missing_metrics(self):
        self.assertEqual("PROPOSED_NOT_IMPLEMENTED", CONTRACT["artifact_status"])
        sections = CONTRACT["required_sections"]
        self.assertEqual(14, len(sections))
        self.assertEqual(14, len(set(sections)))
        for item in ("evidence", "mvp_in", "mvp_out", "functional_requirements",
                     "acceptance_criteria", "metrics", "next_action"):
            self.assertIn(item, sections)
        self.assertIn("falsifier", CONTRACT["hypothesis_fields"])
        self.assertIn("acceptance_id", CONTRACT["requirement_fields"])
        for item in ("definition", "unit", "event_or_source", "period",
                     "verification", "data_limitations"):
            self.assertIn(item, CONTRACT["metric_fields"])
        self.assertEqual(
            {"baseline": "UNKNOWN", "target": "PROPOSED", "actual": "NOT_MEASURED"},
            CONTRACT["missing_data"],
        )
        self.assertEqual({"54", "55", "56"}, set(CONTRACT["handoff_targets"]))

    def test_synthetic_examples_are_not_offered_as_observations(self):
        content = (SKILL / "references/EXAMPLES.md").read_text(encoding="utf-8")
        for item in ("ASSUMPTION", "UNKNOWN", "UNTESTED", "falsifier",
                     "AC1", "AC2", "AC3", "AC4", "NOT_MEASURED",
                     "No interviews", "Synthetic", "negative"):
            self.assertIn(item.lower(), content.lower())
        self.assertIn("not empirically verified", content)
        self.assertIn("no real expense data", content.lower()) if "no real expense data" in content.lower() else self.assertIn("no real personal data", content.lower())

    def test_both_layouts_preview_then_apply_with_ownership(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for layout in ("codex", "claude"):
                before = sorted(target.rglob("*"))
                preview = operate("install", target, names=["product-discovery"], layout=layout, apply=False)
                self.assertFalse(preview["applied"])
                self.assertEqual(before, sorted(target.rglob("*")))
                result = operate("install", target, names=["product-discovery"], layout=layout, apply=True)
                self.assertTrue(result["applied"])
                self.assertIn("product-discovery", read_state(target, layout)["skills"])
                self.assertTrue((target / (".agents" if layout == "codex" else ".claude")
                                 / "skills/product-discovery/SKILL.md").is_file())
            self.assertFalse((target / "reports").exists())
            self.assertFalse((target / "prd").exists())
            self.assertFalse((target / "research").exists())


if __name__ == "__main__":
    unittest.main()
