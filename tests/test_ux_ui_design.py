"""Issue #56: positive/negative structural tests; client activation NOT_MEASURED."""
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
from validate_ux_ui_spec import validate

SKILL = ROOT / "extensions/design/skills/ux-design-process"
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
EXPENSES = json.loads((SKILL / "references/EXAMPLE_EXPENSES.json").read_text(encoding="utf-8"))
PRO = json.loads((SKILL / "references/EXAMPLE_WORKFLOWS.json").read_text(encoding="utf-8"))


class UXUIDesignTests(unittest.TestCase):
    def sample(self):
        return copy.deepcopy(EXPENSES)

    def test_both_examples_and_preserved_ids(self):
        self.assertEqual([], validate(self.sample()))
        self.assertEqual([], validate(PRO))
        self.assertEqual({"R1", "R2", "R3"}, {r["id"] for r in EXPENSES["source_requirements"]})
        self.assertEqual({"AC1", "AC2", "AC3", "AC4"}, {r["id"] for r in EXPENSES["acceptance_criteria"]})
        self.assertEqual({"UC1", "UC2", "UC3"}, {r["id"] for r in EXPENSES["use_cases"]})

    def test_profile_reuses_existing_without_controller(self):
        self.assertEqual(SKILL, skill_sources(MANIFEST)["ux-design-process"])
        self.assertEqual(["ux-design-process"], MANIFEST["extension_packs"]["design"]["skills"])
        p = MANIFEST["profiles"]["ux-design"]
        self.assertEqual(["ux-design-process", "design-system-consistency",
                          "component-architecture", "task-scoping"], p)
        self.assertNotIn("ux-design-process", MANIFEST["profiles"]["general"])
        for disallowed in ("make-feature", "feature-delivery", "adaptive-delivery",
                           "qa-all", "screenshot-fidelity", "motion-quality"):
            self.assertNotIn(disallowed, p)

    def test_skill_bounded_and_refs(self):
        content = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for required in ("Positive triggers:", "Negative triggers:",
                         "read-only", "in chat by default", "NOT_MEASURED",
                         "screenshot-fidelity", "component-architecture"):
            self.assertIn(required, content)
        for ref in ("WORKFLOW.md", "UX_UI_CONTRACT.json", "MANUAL_ACCEPTANCE.md",
                    "INSPIRATION_REVIEW.md", "REVIEW_AND_STRESS.md",
                    "EXAMPLE_EXPENSES.json", "EXAMPLE_WORKFLOWS.json"):
            self.assertTrue((SKILL / "references" / ref).is_file())

    def test_manager_previews_no_write_and_explicit_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for layout in ("codex", "claude"):
                before = sorted(target.rglob("*"))
                self.assertFalse(operate("install", target, names=["ux-design-process"],
                                         layout=layout, apply=False)["applied"])
                self.assertEqual(before, sorted(target.rglob("*")))
                self.assertTrue(operate("install", target, names=["ux-design-process"],
                                        layout=layout, apply=True)["applied"])
                self.assertIn("ux-design-process", read_state(target, layout)["skills"])
            self.assertFalse((target / "reports").exists())

    def test_missing_input_and_duplicate_screen(self):
        self.assertTrue(validate({}))
        p = self.sample()
        p.pop("source_requirements")
        self.assertTrue(validate(p))
        p = self.sample()
        p["screens"].append(copy.deepcopy(p["screens"][0]))
        self.assertTrue(any("duplicate ID" in x for x in validate(p)))

    def test_unreachable_end_and_broken_transition(self):
        p = self.sample()
        p["flows"][0]["nodes"][0]["next"] = []
        self.assertTrue(any("unreachable end state" in x for x in validate(p)))
        p = self.sample()
        p["flows"][0]["nodes"][0]["next"] = ["not_a_node"]
        self.assertTrue(any("dangling transition" in x for x in validate(p)))

    def test_orphan_screen_and_missing_error_path(self):
        p = self.sample()
        p["screens"][1]["flow_ids"] = ["not_a_flow"]
        self.assertTrue(any("invalid flow_ids" in x for x in validate(p)))
        p = self.sample()
        p["flows"][0]["error_nodes"] = ["missing"]
        self.assertTrue(any("invalid error_nodes" in x for x in validate(p)))

    def test_button_action_without_outcome(self):
        p = self.sample()
        p["components"][0]["outputs"] = []
        self.assertTrue(any("missing outputs" in x for x in validate(p)))

    def test_lost_requirement_and_ac_links(self):
        p = self.sample()
        p["traceability"][0]["requirement_id"] = "R404"
        self.assertTrue(any("unknown requirement" in x for x in validate(p)))
        p = self.sample()
        p["traceability"][0]["acceptance_ids"] = ["AC3"]
        self.assertTrue(any("broken R-to-acceptance_ids" in x for x in validate(p)))
        p = self.sample()
        p["traceability"][0]["flow_ids"] = ["FLOW-2"]
        self.assertTrue(any("broken R-to-flow_ids" in x for x in validate(p)))

    def test_no_claimed_fake_render_or_interactivity(self):
        p = self.sample()
        p["prototype"]["status"] = "RENDERED"
        self.assertTrue(any("without artifact/evidence" in x for x in validate(p)))
        p = self.sample()
        p["prototype"].update(status="INTERACTIVE_VERIFIED", artifact_ref="x.png", evidence="x")
        self.assertTrue(any("static PNG/text claimed interactive" in x for x in validate(p)))

    def test_no_claimed_unchecked_responsive_wcag(self):
        p = self.sample()
        p["responsive"][0]["viewports"][0]["tested"] = True
        self.assertTrue(any("unverified responsive" in x for x in validate(p)))
        p = self.sample()
        p["accessibility"][0]["status"] = "AUTO_CHECKED"
        self.assertTrue(any("without evidence" in x for x in validate(p)))

    def test_no_fake_observation_and_usability(self):
        p = self.sample()
        p["research"]["sources"][0]["type"] = "OBSERVED"
        self.assertTrue(any("invented observed" in x for x in validate(p)))
        p = self.sample()
        p["research"]["hypotheses"][0]["status"] = "TESTED"
        self.assertTrue(any("unverified usability" in x for x in validate(p)))

    def test_no_fake_approval_or_implemented_ui(self):
        p = self.sample()
        p["visual_design"]["approval"] = "OWNER_ACCEPTED"
        self.assertTrue(any("acceptance unverified" in x for x in validate(p)))
        p = self.sample()
        p["handoff"]["implementation_status"] = "IMPLEMENTED_VERIFIED"
        self.assertTrue(any("without code evidence" in x for x in validate(p)))

    def test_external_source_evaluation_is_not_vendoring(self):
        review = (SKILL / "references/INSPIRATION_REVIEW.md").read_text(encoding="utf-8")
        stress = (SKILL / "references/REVIEW_AND_STRESS.md").read_text(encoding="utf-8")
        for source in ("pbakaus/impeccable", "emilkowalski/skills",
                       "nextlevelbuilder/ui-ux-pro-max-skill"):
            self.assertIn(source, review)
        for key in ("NOT_TESTED", "permission", "same actual data boundary",
                    "genuinely", "evidence"):
            # The checklist is a plan, not a claim of runtime verification.
            self.assertIn(key.lower(), stress.lower())
        self.assertIn("not copied", review)
        self.assertIn("No third-party code", review)

    def test_fallback_and_bilingual_docs(self):
        for path in ("docs/UX_UI_DESIGN.md", "docs/ru/UX_UI_DESIGN.md"):
            self.assertTrue((ROOT / path).is_file())
        self.assertEqual("TEXT_SPEC", EXPENSES["prototype"]["artifact_kind"])
        self.assertIsNone(EXPENSES["prototype"]["artifact_ref"])
        self.assertIn("NOT_TESTED", {x["status"] for x in PRO["accessibility"]})


    def test_bilingual_ux_docs_distinguish_visual_design_and_preview(self):
        import re

        for path, visual_phrase in (
            ("docs/UX_UI_DESIGN.md", "follow the available original tool workflows"),
            ("docs/ru/UX_UI_DESIGN.md", "выполняйте оригинальные методы"),
        ):
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                first_section = text[:2200]
                self.assertIn("ui-orchestra", first_section)
                self.assertIn("ux-design", first_section)
                self.assertIn(visual_phrase, first_section)
                blocks = re.findall(r"```bash\n(.*?)\n```", text, re.S)
                self.assertEqual(2, len(blocks))
                self.assertNotIn("--apply", blocks[0])
                self.assertIn("--apply", blocks[1])

if __name__ == "__main__":
    unittest.main()
