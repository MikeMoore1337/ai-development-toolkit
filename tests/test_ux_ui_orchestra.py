"""Offline behavioral gates for UX/UI Design Orchestra; no external agents called."""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
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

    def test_original_three_skill_invocation_gates(self):
        good = self.with_rendered_comparison(self.load_three_directions())
        good["gate"] = "AWAITING_VISUAL_APPROVAL"
        good["proposal"].update(visual_status="RENDERED",
                                artifact_refs=["desktop.png", "mobile.png"])
        good["original_design_skills"] = {"mode": "ALL_THREE", "invocations": []}
        self.assert_bad("exactly three receipts", good)
        good["original_design_skills"]["invocations"] = [
            {"name": name, "status": "NOT_VERIFIED", "loaded": False}
            for name in checker.ORIGINALS
        ]
        self.assert_bad("all-three approval requires", good)
        for item in good["original_design_skills"]["invocations"]:
            item.update(status="INVOKED", loaded=True,
                        source_revision="a" * 40,
                        invocation_evidence="observed client trace")
        self.assertEqual([], checker.validate(good))
        good["original_design_skills"]["invocations"][0]["invocation_evidence"] = ""
        self.assert_bad("invocation lacks", good)
        good["original_design_skills"]["invocations"][0]["invocation_evidence"] = "observed"
        good["original_design_skills"]["invocations"][2]["name"] = "impeccable"
        self.assert_bad("unknown or duplicate", good)

    def native_scope_exclusion_report(self):
        """Synthetic claims for validation only; no original skill is run."""
        report = copy.deepcopy(self.good)
        report["original_design_skills"] = {
            "mode": "ALL_THREE",
            "invocations": [
                {"name": name, "status": "INVOKED", "loaded": True,
                 "source_revision": "a" * 40,
                 "invocation_evidence": "synthetic invocation claim for structural testing"}
                for name in checker.ORIGINALS
            ],
        }
        report["original_design_skills"]["invocations"][1] = {
            "name": "design-taste-frontend",
            "status": "NOT_APPLICABLE_NATIVE_SCOPE",
            "loaded": True,
            "source_revision": "a" * 40,
            "applicability_reason": "Native scope excludes app dashboards; this target is a dashboard.",
            "applicability_source": "skills/taste-skill/SKILL.md",
        }
        return report

    def test_original_native_scope_exclusion_allows_nonapproval_receipt(self):
        for gate in ("VISUAL_PACKAGE_MISSING", "NEEDS_DESIGN_REVISION", "AUDIT_COMPLETE"):
            with self.subTest(gate=gate):
                report = self.native_scope_exclusion_report()
                report["gate"] = gate
                self.assertEqual([], checker.validate(report))
                row = report["original_design_skills"]["invocations"][1]
                for empty_evidence in (None, ""):
                    row["invocation_evidence"] = empty_evidence
                    self.assertEqual([], checker.validate(report))

    def test_original_native_scope_exclusion_requires_loaded_source_and_details(self):
        invalid_values = {
            "loaded": (None, False, 0, 1, "true", [], {}),
            "source_revision": (None, False, 40, [], {}, "", " ",
                                "a" * 39, "a" * 41, "g" * 40),
            "applicability_reason": (None, False, 1, [], {}, "", " \t\n"),
            "applicability_source": (None, False, 1, [], {}, "", " \t\n"),
        }
        for field, values in invalid_values.items():
            with self.subTest(field=field, missing=True):
                report = self.native_scope_exclusion_report()
                del report["original_design_skills"]["invocations"][1][field]
                self.assert_bad("native-scope exclusion lacks", report)
            for value in values:
                with self.subTest(field=field, value=value):
                    report = self.native_scope_exclusion_report()
                    report["original_design_skills"]["invocations"][1][field] = value
                    self.assert_bad("native-scope exclusion lacks", report)

    def test_original_native_scope_exclusion_cannot_claim_invocation(self):
        for evidence in ("synthetic trace", " ", True, False, 0, 1, [], {},
                         ["trace"], {"trace": "synthetic"}):
            with self.subTest(evidence=evidence):
                report = self.native_scope_exclusion_report()
                report["original_design_skills"]["invocations"][1]["invocation_evidence"] = evidence
                self.assert_bad("native-scope exclusion cannot claim invocation evidence", report)

    def test_original_native_scope_exclusion_blocks_all_approval_gates(self):
        for gate in ("AWAITING_VISUAL_APPROVAL", "OWNER_ACCEPTED", "IMPLEMENTED_NOT_RELEASED"):
            with self.subTest(gate=gate):
                report = self.native_scope_exclusion_report()
                report.update(gate=gate, mode="implement-approved",
                              owner_approval_evidence="synthetic approval claim for structural testing")
                if gate == "IMPLEMENTED_NOT_RELEASED":
                    report["implementation"]["status"] = "IMPLEMENTED"
                    report["changed_ui"] = True
                self.assertEqual(["all-three approval requires three actual invocations"],
                                 checker.validate(report))

    def test_original_presence_is_not_activation(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.assertTrue(all(row["status"] == "MISSING"
                                for row in checker.inspect_originals(target)))
            for name in checker.ORIGINALS:
                root = target / ".agents" / "skills" / name
                (root / "scripts").mkdir(parents=True)
                (root / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: test\n---\n",
                    encoding="utf-8")
            found = checker.inspect_originals(target)
            self.assertTrue(all(row["status"] == "FILES_PRESENT_UNATTESTED"
                                for row in found))
            self.assertEqual(64, len(found[0]["local_tree_sha256"]))
            (target / ".agents" / "skills" / "ui-ux-pro-max" / "SKILL.md").write_text(
                "---\nname: wrong\n---\n", encoding="utf-8")
            self.assertEqual("INCOMPLETE", checker.inspect_originals(target)[2]["status"])

    def test_valid_read_only_default(self):
        self.assertEqual([], checker.validate(self.good))
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertIn("ux-ui-design-orchestra", manifest["extension_skills"])
        self.assertEqual("ux-ui-design-orchestra", manifest["profiles"]["ui-orchestra"][0])
        self.assertNotIn("ux-ui-design-orchestra", manifest["profiles"]["general"])

    def test_new_design_can_use_native_skill_workflow_without_legacy_quality_form(self):
        payload = self.load_three_directions()
        self.assertEqual([], checker.validate(payload))
        del payload["design_quality"]
        self.assertEqual([], checker.validate(payload))

    def test_cards_hero_and_gradient_are_never_banned_by_structure(self):
        payload = self.load_three_directions()
        payload["design_quality"]["generic_template_risks"] = [
            "large hero", "product cards", "neon gradient", "large hero"]
        self.assertEqual([], checker.validate(payload))
        payload["design_quality"]["generic_template_risks"] = []
        self.assertEqual([], checker.validate(payload))
        payload["design_quality"]["generic_template_risks"] = [None]
        self.assert_bad("optional template observations", payload)

    def test_art_direction_assessment_does_not_forbid_user_review(self):
        payload = self.load_three_directions()
        payload["proposal"].update(visual_status="RENDERED", artifact_refs=["demo:mobile"])
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        payload["design_quality"]["quality_status"] = "NEEDS_DESIGN_REVISION"
        self.assertEqual([], checker.validate(payload))

    def test_mandatory_orchestra_before_generic_frontend_in_source(self):
        skill = (ROOT / ".agents/skills/ux-ui-design-orchestra/SKILL.md").read_text(encoding="utf-8")
        workflow = (ROOT / ".agents/skills/ux-ui-design-orchestra/references/WORKFLOW.md").read_text(encoding="utf-8")
        for doc in (ROOT / "AGENT_START.md", ROOT / "AGENT_START.ru.md"):
            text = doc.read_text(encoding="utf-8")
            self.assertIn("ORCHESTRA_SOURCE_UNAVAILABLE", text)
            self.assertIn("ux-ui-design-orchestra", text)
        self.assertIn("primary coordinator", skill)
        self.assertIn("Mandatory routing precedence", workflow)
        self.assertIn("Tool-native creative freedom", skill)
        self.assertIn("create-design", workflow)

    def test_ui_policy_follows_native_tools_without_style_bans(self):
        required = {
            ".agents/skills/ux-ui-design-orchestra/SKILL.md": "Tool-native creative freedom",
            ".agents/skills/ux-ui-design-orchestra/references/CREATE_DESIGN.md": "Tool-native creative freedom",
            ".agents/skills/ux-ui-design-orchestra/references/WORKFLOW.md": "Tool-native creative freedom",
            ".agents/skills/ux-ui-design-orchestra/references/SPECIALISTS.md": "Tool-native creative freedom",
            "AGENT_START.md": "Tool-native creative freedom",
            "AGENT_START.ru.md": "Свобода UI/UX",
            "docs/UX_UI_DESIGN.md": "Tool-native creative freedom",
            "docs/ru/UX_UI_DESIGN.md": "Свобода UI/UX",
            "integrations/chatgpt-plugin/ai-development-toolkit/skills/toolkit-ui-review/SKILL.md": "Tool-native creative freedom",
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

    def test_user_review_does_not_require_three_sketches(self):
        payload = self.load_three_directions()
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        payload["proposal"].update(visual_status="RENDERED", artifact_refs=["mobile.png"])
        self.assertEqual([], checker.validate(payload))
        self.assertEqual([], checker.validate(self.with_rendered_comparison(payload)))

    def test_optional_visual_comparison_cannot_claim_unrendered_frames(self):
        payload = self.load_three_directions()
        del payload["design_exploration"]["visual_comparison"]
        self.assertEqual([], checker.validate(payload))
        payload = self.load_three_directions()
        payload["design_exploration"]["visual_comparison"]["frames"] = [
            {"direction_id": "training-editorial", "evidence_id": "fake"}]
        self.assert_bad("missing visual comparison cannot claim frames", payload)

    def test_three_real_evidence_declarations_are_required(self):
        payload = self.with_rendered_comparison(self.load_three_directions())
        self.assertEqual([], checker.validate(payload))
        payload["evidence"][0]["status"] = "SOURCE_ONLY"
        self.assert_bad("missing rendered evidence", payload)

    def test_comparison_checks_evidence_not_composition_style(self):
        payload = self.with_rendered_comparison(self.load_three_directions())
        payload["design_exploration"]["visual_comparison"]["frames"].pop()
        self.assert_bad("rendered comparison frames must match", payload)
        payload = self.with_rendered_comparison(self.load_three_directions())
        frames = payload["design_exploration"]["visual_comparison"]["frames"]
        frames[1]["layout_signature"] = frames[0]["layout_signature"]
        self.assertEqual([], checker.validate(payload))
        frames[1]["direction_id"] = "training-editorial"
        self.assert_bad("frame directions/evidence inconsistent", payload)

    def test_visual_comparison_cannot_reuse_unsegmented_capture_or_inconsistent_scale(self):
        payload = self.with_rendered_comparison(self.load_three_directions())
        payload["evidence"][1]["artifact_ref"] = payload["evidence"][0]["artifact_ref"]
        self.assert_bad("reuses same unsegmented artifact", payload)
        payload = self.with_rendered_comparison(self.load_three_directions())
        payload["evidence"][2]["viewport"] = "960x1200"
        self.assert_bad("matching viewport scale", payload)

    def test_mobile_only_design_can_request_visual_review(self):
        payload = self.with_rendered_comparison(self.load_three_directions())
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        payload["proposal"]["artifact_refs"] = ["only-mobile.png"]
        self.assertEqual([], checker.validate(payload))
        payload["proposal"]["artifact_refs"] = []
        self.assert_bad("visual review requires actual referenced design previews", payload)

    def test_number_of_directions_is_not_imposed_on_upstream_tools(self):
        payload = self.load_three_directions()
        self.assertEqual([], checker.validate(payload))
        del payload["design_exploration"]
        self.assertEqual([], checker.validate(payload))
        payload = self.load_three_directions()
        exploration = payload["design_exploration"]
        exploration["directions"] = exploration["directions"][:1]
        exploration["rejections"] = []
        exploration["visual_comparison"] = {"status": "MISSING", "frames": []}
        self.assertEqual([], checker.validate(payload))
        exploration["directions"] = []
        self.assert_bad("nonempty list", payload)

    def test_multiple_variants_can_share_composition_and_palette(self):
        payload = self.load_three_directions()
        concepts = payload["design_exploration"]["directions"]
        concepts[1]["composition"] = concepts[0]["composition"]
        concepts[2]["information_architecture"] = concepts[0]["information_architecture"]
        self.assertEqual([], checker.validate(payload))

    def test_selected_direction_and_rejection_ids_are_consistent(self):
        payload = self.load_three_directions()
        payload["design_exploration"]["selected_id"] = "does-not-exist"
        self.assert_bad("selected direction missing", payload)
        payload = self.load_three_directions()
        payload["design_exploration"]["rejections"][0]["id"] = "training-editorial"
        self.assert_bad("rejected IDs invalid", payload)

    def test_invalid_selected_id_fails_closed_without_exception(self):
        payload = self.load_three_directions()
        for malformed in ([], {}, 42, None):
            with self.subTest(malformed=malformed):
                payload["design_exploration"]["selected_id"] = malformed
                self.assert_bad("selected direction missing", payload)

    def test_cross_domain_swap_heuristic_never_bans_a_design(self):
        payload = self.with_rendered_comparison(self.load_three_directions())
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        swap = payload["design_exploration"]["cross_domain_swap_test"]
        swap["would_require_structural_redesign"] = False
        self.assertEqual([], checker.validate(payload))
        swap["would_require_structural_redesign"] = "forbidden"
        self.assert_bad("optional swap-test declaration invalid", payload)

    def test_self_declared_revision_need_does_not_block_owner_feedback(self):
        payload = self.load_three_directions()
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        payload["proposal"].update(visual_status="RENDERED", artifact_refs=["desktop.png"])
        payload["design_exploration"]["status"] = "NEEDS_REVISION"
        self.assertEqual([], checker.validate(payload))

    def test_explicitly_requested_comparison_is_respected_without_forcing_three(self):
        payload = copy.deepcopy(self.good)
        payload["design_exploration_required"] = True
        self.assert_bad("explicitly requested design exploration is missing", payload)
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

    def test_visual_approval_still_requires_a_real_preview_declaration(self):
        payload = self.load_three_directions()
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        self.assert_bad("visual review requires actual referenced design previews", payload)
        payload["proposal"]["visual_status"] = "RENDERED"
        payload["proposal"]["artifact_refs"] = ["artifact:mobile"]
        self.assertEqual([], checker.validate(payload))

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


    def test_visual_baseline_is_preserved_with_separate_reviews(self):
        payload = self.load_three_directions()
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        payload["proposal"].update(visual_status="RENDERED", artifact_refs=["mango:new-mobile.png"])
        payload["prior_visual_baseline"] = True
        self.assert_bad("prior preferred visual baseline needs lineage", payload)
        payload["visual_lineage"] = {
            "baseline": {"version": "mango-preferred-v1",
                         "status": "USER_PREFERRED",
                         "artifact_refs": ["mango:original-desktop.png", "mango:original-mobile.png"],
                         "strengths": ["Rich fruit photography", "Editorial typography"]},
            "candidate": {"version": "mango-candidate-v2",
                          "artifact_refs": ["mango:new-mobile.png"]},
            "visual_review": {"status": "REVIEWED", "comparisons": [
                {"aspect": "composition", "assessment": "CHANGED",
                 "observation": "The new layout loses the original focal photograph."},
                {"aspect": "usability", "assessment": "UNCERTAIN",
                 "observation": "Comparative buyer testing was not performed."}]},
            "technical_review": {"status": "PASS", "evidence": "synthetic:responsive-check"},
            "recommendation": "KEEP_BASELINE",
            "owner_decision": "PENDING",
        }
        self.assertEqual([], checker.validate(payload))
        payload["visual_lineage"]["visual_review"] = {"status": "NOT_REVIEWED", "comparisons": []}
        payload["visual_lineage"]["recommendation"] = "PROPOSE_CANDIDATE"
        self.assert_bad("candidate replacement needs observed visual comparison", payload)
        payload["visual_lineage"]["recommendation"] = "UNDECIDED"
        self.assertEqual([], checker.validate(payload))
        payload["visual_lineage"]["owner_decision"] = "APPROVE_CANDIDATE"
        self.assert_bad("cannot claim owner approved candidate", payload)

    def test_technical_pass_is_not_artistic_certification(self):
        payload = self.load_three_directions()
        payload["gate"] = "AWAITING_VISUAL_APPROVAL"
        payload["proposal"].update(visual_status="RENDERED", artifact_refs=["mango:mobile.png"])
        payload["visual_lineage"] = {
            "baseline": {"version": "owner-v1", "status": "OWNER_ACCEPTED",
                         "artifact_refs": ["mango:original.png"], "strengths": ["Distinctive composition"]},
            "candidate": {"version": "candidate-v2", "artifact_refs": ["mango:mobile.png"]},
            "visual_review": {"status": "NOT_REVIEWED", "comparisons": []},
            "technical_review": {"status": "PASS", "evidence": "synthetic:ci-green"},
            "recommendation": "UNDECIDED", "owner_decision": "PENDING",
        }
        self.assertEqual([], checker.validate(payload))
        payload["visual_lineage"]["technical_review"]["evidence"] = ""
        self.assert_bad("technical PASS needs", payload)

    def test_preferred_artifact_claims_cannot_be_empty_or_forged(self):
        payload = self.load_three_directions()
        payload["visual_lineage"] = {
            "baseline": {"version": "old", "status": "USER_PREFERRED",
                         "artifact_refs": ["old.png"], "strengths": ["Strong imagery"]},
            "candidate": {"version": "new", "artifact_refs": ["new.png"]},
            "visual_review": {"status": "REVIEWED", "comparisons": [
                {"aspect": "imagery", "assessment": "PRESERVED",
                 "observation": "The same composition is retained."}]},
            "technical_review": {"status": "NOT_VERIFIED"},
            "recommendation": "REFINE_BASELINE", "owner_decision": "PENDING",
        }
        self.assertEqual([], checker.validate(payload))
        payload["visual_lineage"]["baseline"]["artifact_refs"] = []
        self.assert_bad("baseline artifact references missing", payload)
        payload["visual_lineage"]["baseline"]["artifact_refs"] = ["old.png"]
        payload["visual_lineage"]["visual_review"]["comparisons"][0]["observation"] = ""
        self.assert_bad("observation missing", payload)



    def test_malformed_visual_lineage_values_are_refused_without_exception(self):
        valid = self.load_three_directions()
        valid["visual_lineage"] = {
            "baseline": {"version": "v1", "status": "USER_PREFERRED",
                         "artifact_refs": ["sample:v1"], "strengths": ["Strong imagery"]},
            "candidate": {"version": "v2", "artifact_refs": ["sample:v2"]},
            "visual_review": {"status": "REVIEWED", "comparisons": [
                {"aspect": "layout", "assessment": "CHANGED", "observation": "Different photo hierarchy"}]},
            "technical_review": {"status": "PASS", "evidence": "synthetic:viewport"},
            "recommendation": "UNDECIDED", "owner_decision": "PENDING",
        }
        self.assertEqual([], checker.validate(valid))
        paths = [
            ("baseline", "status"),
            ("visual_review", "status"),
            ("technical_review", "status"),
            ("recommendation", None),
            ("owner_decision", None),
        ]
        for container, field in paths:
            for malformed in ([], {}, 4, None):
                payload = copy.deepcopy(valid)
                if field is None:
                    payload["visual_lineage"][container] = malformed
                else:
                    payload["visual_lineage"][container][field] = malformed
                with self.subTest(container=container, field=field, malformed=malformed):
                    self.assertNotEqual([], checker.validate(payload))
        payload = copy.deepcopy(valid)
        payload["visual_lineage"]["visual_review"]["comparisons"][0]["assessment"] = []
        self.assert_bad("decision invalid", payload)
        payload = copy.deepcopy(valid)
        payload["design_quality"]["impeccable_source_status"] = []
        self.assert_bad("source status invalid", payload)

    def test_rendered_frame_malformed_evidence_is_refused_without_exception(self):
        valid = self.with_rendered_comparison(self.load_three_directions())
        for bad in ([], {}, None, 100):
            payload = copy.deepcopy(valid)
            payload["design_exploration"]["visual_comparison"]["frames"][0]["evidence_id"] = bad
            with self.subTest(bad=bad):
                self.assertNotEqual([], checker.validate(payload))
        payload = copy.deepcopy(valid)
        payload["evidence"][0]["artifact_ref"] = []
        self.assert_bad("invalid artifact reference", payload)
        payload = copy.deepcopy(valid)
        payload["evidence"][0]["viewport"] = []
        self.assert_bad("invalid viewport", payload)


if __name__ == "__main__":
    unittest.main()
