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


if __name__ == "__main__":
    unittest.main()
