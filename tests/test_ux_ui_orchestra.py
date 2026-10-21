"""Offline behavioral gates for UX/UI Design Orchestra; no external agents called."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("design_orchestra", ROOT / "scripts/validate_ux_ui_orchestra.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class DesignOrchestraTests(unittest.TestCase):
    def setUp(self):
        self.good = json.loads((ROOT / "fixtures/ux_ui_orchestra_valid.json").read_text(encoding="utf-8"))

    def assert_bad(self, fragment, item):
        self.assertTrue(any(fragment in err for err in checker.validate(item)), checker.validate(item))

    def test_valid_read_only_default(self):
        self.assertEqual([], checker.validate(self.good))
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertIn("ux-ui-design-orchestra", manifest["extension_skills"])
        self.assertEqual("ux-ui-design-orchestra", manifest["profiles"]["ui-orchestra"][0])
        self.assertNotIn("ux-ui-design-orchestra", manifest["profiles"]["general"])

    def test_new_design_must_have_art_direction_and_non_template_critique(self):
        payload = json.loads((ROOT / "fixtures/ux_ui_orchestra_create_design_valid.json").read_text(encoding="utf-8"))
        self.assertEqual([], checker.validate(payload))
        del payload["design_quality"]
        self.assert_bad("requires design_quality", payload)

    def test_missing_template_risks_rejects_generic_design(self):
        payload = json.loads((ROOT / "fixtures/ux_ui_orchestra_create_design_valid.json").read_text(encoding="utf-8"))
        payload["design_quality"]["generic_template_risks"] = ["neon glow", "neon glow", "generic pricing"]
        self.assert_bad("three distinct generic template risks", payload)
        payload["design_quality"]["generic_template_risks"] = ["card grid"]
        self.assert_bad("three distinct generic template risks", payload)

    def test_unrevised_design_cannot_request_approval(self):
        payload = json.loads((ROOT / "fixtures/ux_ui_orchestra_create_design_valid.json").read_text(encoding="utf-8"))
        payload["proposal"].update(visual_status="RENDERED", artifact_refs=["demo:desktop", "demo:mobile"])
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        payload["design_quality"]["quality_status"] = "NEEDS_DESIGN_REVISION"
        self.assert_bad("before design quality revision", payload)

    def test_mandatory_orchestra_before_generic_frontend_in_source(self):
        skill = (ROOT / ".agents/skills/ux-ui-design-orchestra/SKILL.md").read_text(encoding="utf-8")
        workflow = (ROOT / ".agents/skills/ux-ui-design-orchestra/references/WORKFLOW.md").read_text(encoding="utf-8")
        for doc in (ROOT / "AGENT_START.md", ROOT / "AGENT_START.ru.md"):
            text = doc.read_text(encoding="utf-8")
            self.assertIn("ORCHESTRA_SOURCE_UNAVAILABLE", text)
            self.assertIn("ux-ui-design-orchestra", text)
        self.assertIn("primary coordinator", skill)
        self.assertIn("Mandatory routing precedence", workflow)
        self.assertIn("generic-template risks", skill)
        self.assertIn("create-design", workflow)

    def test_domain_first_instructions_do_not_default_to_saas_template(self):
        # Regression guard for both client entrypoints, both guides and the actual skill.
        required = {
            ".agents/skills/ux-ui-design-orchestra/SKILL.md": "Domain-first, not SaaS-first",
            ".agents/skills/ux-ui-design-orchestra/references/CREATE_DESIGN.md": "Do not make a SaaS website unless",
            ".agents/skills/ux-ui-design-orchestra/references/WORKFLOW.md": "Never use SaaS as the default style",
            ".agents/skills/ux-ui-design-orchestra/references/SPECIALISTS.md": "Do not convert anti-SaaS examples",
            "AGENT_START.md": "SaaS is not the default design style",
            "AGENT_START.ru.md": "SaaS-структура не является вариантом по умолчанию",
            "docs/UX_UI_DESIGN.md": "A SaaS layout is not the default",
            "docs/ru/UX_UI_DESIGN.md": "SaaS-макет не является вариантом по умолчанию",
        }
        for path, expectation in required.items():
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                self.assertIn(expectation, text)

    def load_three_directions(self):
        return json.loads((ROOT / "fixtures/ux_ui_orchestra_create_design_valid.json").read_text(encoding="utf-8"))

    def with_rendered_comparison(self, payload):
        """Synthetic declaration only: reference strings are not real rendered images."""
        directions = payload["design_exploration"]["directions"]
        layouts = (
            ["immersive_training", "class_index", "coach_story"],
            ["location_map", "visitor_guide", "first_class_picker"],
            ["equipment_spec", "session_filter", "coach_credentials"],
        )
        payload["design_exploration"]["visual_comparison"] = {
            "status": "RENDERED",
            "frames": [
                {"direction_id": direction["id"], "evidence_id": f"W{i}",
                 "layout_signature": layouts[i]}
                for i, direction in enumerate(directions)
            ],
        }
        payload["evidence"] = [
            {"id": f"W{i}", "status": "RENDERED",
             "artifact_ref": f"synthetic:frame-{i}.svg",
             "route": "SYNTHETIC_WIREFRAME",
             "viewport": "420x700",
             "provenance": "synthetic declaration for structural testing; no real rendering"}
            for i in range(3)
        ]
        payload["proposal"].update(visual_status="RENDERED", artifact_refs=[
            "synthetic:winner-desktop.png", "synthetic:winner-mobile.png"])
        return payload

    def test_visual_comparison_is_required_before_winner_approval(self):
        payload = self.load_three_directions()
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        payload["proposal"].update(visual_status="RENDERED", artifact_refs=["desktop.png", "mobile.png"])
        self.assert_bad("before three rendered visual sketches", payload)
        self.assertEqual([], checker.validate(self.with_rendered_comparison(payload)))

    def test_missing_visual_comparison_status_cannot_be_passed_off_as_rendered(self):
        payload = self.load_three_directions()
        del payload["design_exploration"]["visual_comparison"]
        self.assert_bad("honest visual comparison status", payload)
        payload = self.load_three_directions()
        payload["design_exploration"]["visual_comparison"]["frames"] = [
            {"direction_id": "training-editorial", "evidence_id": "fake"}]
        self.assert_bad("missing visual comparison cannot claim frame artifacts", payload)

    def test_three_real_evidence_declarations_are_required(self):
        payload = self.with_rendered_comparison(self.load_three_directions())
        self.assertEqual([], checker.validate(payload))
        payload["evidence"][0]["status"] = "SOURCE_ONLY"
        self.assert_bad("missing rendered evidence", payload)

    def test_mismatched_visual_frames_and_repeated_layouts_fail(self):
        payload = self.with_rendered_comparison(self.load_three_directions())
        payload["design_exploration"]["visual_comparison"]["frames"].pop()
        self.assert_bad("exactly three rendered frames", payload)
        payload = self.with_rendered_comparison(self.load_three_directions())
        frames = payload["design_exploration"]["visual_comparison"]["frames"]
        frames[1]["layout_signature"] = frames[0]["layout_signature"]
        self.assert_bad("repeats same composition signature", payload)
        payload = self.with_rendered_comparison(self.load_three_directions())
        payload["design_exploration"]["visual_comparison"]["frames"][1]["direction_id"] = "training-editorial"
        self.assert_bad("unknown or duplicate direction", payload)

    def test_visual_comparison_cannot_reuse_unsegmented_capture_or_inconsistent_scale(self):
        payload = self.with_rendered_comparison(self.load_three_directions())
        payload["evidence"][1]["artifact_ref"] = payload["evidence"][0]["artifact_ref"]
        self.assert_bad("reuses same unsegmented artifact", payload)
        payload = self.with_rendered_comparison(self.load_three_directions())
        payload["evidence"][2]["viewport"] = "960x1200"
        self.assert_bad("matching viewport scale", payload)

    def test_winner_requires_both_desktop_and_mobile_at_approval(self):
        payload = self.with_rendered_comparison(self.load_three_directions())
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        payload["proposal"]["artifact_refs"] = ["only-desktop.png"]
        self.assert_bad("winner desktop and mobile previews", payload)

    def test_three_distinct_concepts_are_required_for_create_design(self):
        payload = self.load_three_directions()
        self.assertEqual([], checker.validate(payload))
        del payload["design_exploration"]
        self.assert_bad("requires three-direction exploration", payload)
        payload = self.load_three_directions()
        payload["design_exploration"]["directions"].pop()
        self.assert_bad("requires exactly three directions", payload)

    def test_palette_only_direction_variants_are_rejected(self):
        payload = self.load_three_directions()
        concepts = payload["design_exploration"]["directions"]
        concepts[1]["composition"] = concepts[0]["composition"]
        self.assert_bad("repeated composition", payload)
        payload = self.load_three_directions()
        concepts = payload["design_exploration"]["directions"]
        concepts[2]["information_architecture"] = concepts[0]["information_architecture"]
        self.assert_bad("repeated information_architecture", payload)

    def test_selected_direction_and_rejections_are_consistent(self):
        payload = self.load_three_directions()
        payload["design_exploration"]["selected_id"] = "does-not-exist"
        self.assert_bad("selected direction missing", payload)
        payload = self.load_three_directions()
        payload["design_exploration"]["rejections"][0]["id"] = "training-editorial"
        self.assert_bad("rejected IDs must match", payload)

    def test_invalid_selected_id_fails_closed_without_exception(self):
        payload = self.load_three_directions()
        for malformed in ([], {}, 42, None):
            with self.subTest(malformed=malformed):
                payload["design_exploration"]["selected_id"] = malformed
                self.assert_bad("selected direction missing", payload)

    def test_swap_test_blocks_approval_when_generic(self):
        payload = self.load_three_directions()
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        payload["proposal"].update(visual_status="RENDERED", artifact_refs=["desktop.png", "mobile.png"])
        self.assertEqual([], checker.validate(self.with_rendered_comparison(payload)))
        payload["design_exploration"]["cross_domain_swap_test"]["would_require_structural_redesign"] = False
        self.assert_bad("passing swap test", payload)

    def test_superficial_exploration_not_ready_for_visual_review(self):
        payload = self.load_three_directions()
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        payload["proposal"].update(visual_status="RENDERED", artifact_refs=["desktop.png", "mobile.png"])
        payload["design_exploration"]["status"] = "NEEDS_REVISION"
        self.assert_bad("distinct compared directions", payload)

    def test_substantial_existing_redesign_uses_same_exploration_contract(self):
        payload = copy.deepcopy(self.good)
        payload["design_exploration_required"] = True
        self.assert_bad("requires three-direction exploration", payload)
        payload["design_exploration"] = self.load_three_directions()["design_exploration"]
        self.assertEqual([], checker.validate(payload))

    def test_unrelated_approved_small_fix_remains_exempt(self):
        payload = copy.deepcopy(self.good)
        self.assertEqual([], checker.validate(payload))

    def test_new_design_text_only_requires_visual_package(self):
        payload = json.loads((ROOT / "fixtures/ux_ui_orchestra_create_design_valid.json").read_text(encoding="utf-8"))
        self.assertEqual([], checker.validate(payload))
        payload["changed_ui"] = True
        self.assert_bad("no UI changes", payload)

    def test_new_design_cannot_claim_visual_approval_without_render(self):
        payload = json.loads((ROOT / "fixtures/ux_ui_orchestra_create_design_valid.json").read_text(encoding="utf-8"))
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        self.assert_bad("without rendered visuals", payload)
        payload["proposal"]["visual_status"] = "RENDERED"
        payload["proposal"]["artifact_refs"] = ["artifact:desktop", "artifact:mobile"]
        self.assert_bad("before three rendered visual sketches", payload)
        self.assertEqual([], checker.validate(self.with_rendered_comparison(payload)))

    def test_new_design_cannot_claim_existing_ui_audit(self):
        payload = json.loads((ROOT / "fixtures/ux_ui_orchestra_create_design_valid.json").read_text(encoding="utf-8"))
        payload["gate"] = "AUDIT_COMPLETE"
        self.assert_bad("cannot claim completed UI audit", payload)

    def test_no_more_than_three_workstreams(self):
        payload = copy.deepcopy(self.good)
        payload["workers"] = [{"name": str(i), "execution": "SEQUENTIAL", "source_status": "REFERENCE_ONLY"} for i in range(4)]
        self.assert_bad("too many workstreams", payload)

    def test_existing_audit_flow_is_preserved(self):
        self.assertEqual([], checker.validate(self.good))

    def test_claimed_edit_in_audit_is_rejected(self):
        p = copy.deepcopy(self.good)
        p["changed_ui"] = True
        self.assert_bad("no UI changes", p)

    def test_premature_implementation_is_rejected(self):
        p = copy.deepcopy(self.good)
        p["implementation"]["status"] = "IMPLEMENTED"
        self.assert_bad("must not claim implementation", p)

    def test_forged_owner_acceptance_is_rejected(self):
        p = copy.deepcopy(self.good)
        p["gate"] = "OWNER_ACCEPTED"
        self.assert_bad("cannot claim owner acceptance", p)

    def test_untraced_fake_agent_is_rejected(self):
        p = copy.deepcopy(self.good)
        p["workers"][0]["execution"] = "ACTUAL_SUBAGENT"
        self.assert_bad("missing actual trace", p)

    def test_sequential_is_not_concurrent(self):
        p = copy.deepcopy(self.good)
        p["observed_peak_workers"] = 3
        self.assert_bad("parallel claim without subagents", p)

    def test_rendered_claim_requires_artifact(self):
        p = copy.deepcopy(self.good)
        p["evidence"][0]["status"] = "RENDERED"
        self.assert_bad("rendered claim lacks proof details", p)

    def test_observed_defect_needs_evidence(self):
        p = copy.deepcopy(self.good)
        p["findings"][0]["status"] = "OBSERVED"
        self.assert_bad("observed without evidence", p)

    def test_unknown_evidence_rejected(self):
        p = copy.deepcopy(self.good)
        p["findings"][0]["evidence_ids"] = ["E-does-not-exist"]
        self.assert_bad("invalid evidence refs", p)

    def test_rendered_proposal_requires_file(self):
        p = copy.deepcopy(self.good)
        p["proposal"]["visual_status"] = "RENDERED"
        self.assert_bad("rendered visuals without artifacts", p)

    def test_implementation_needs_explicit_owner_record(self):
        p = copy.deepcopy(self.good)
        p["mode"] = "implement-approved"
        p["gate"] = "IMPLEMENTED_NOT_RELEASED"
        self.assert_bad("owner approval evidence", p)

    def test_inactive_skill_cannot_masquerade_as_agent(self):
        p = copy.deepcopy(self.good)
        p["workers"][0].update(execution="GENERIC_SUBAGENT", source_status="UNAVAILABLE", trace="spawn 1")
        self.assert_bad("unavailable skill", p)


if __name__ == "__main__":
    unittest.main()
