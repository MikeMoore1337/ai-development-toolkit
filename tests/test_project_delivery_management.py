"""Deterministic Issue #54 checks - NOT real client activation or evidence verification."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install import skill_sources
from skill_manager import operate, read_state

SKILL = ROOT / "extensions/management/skills/project-delivery-management"
CONTRACT = json.loads((SKILL / "references/DELIVERY_CONTRACT.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("validate_delivery_plan", ROOT / "scripts/validate_delivery_plan.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
validate = module.validate


def task(ident, requirement, ac, *, status="PLANNED", deps=None, evidence=None, blockers=None):
    return {
        "id": ident, "title": ident, "goal": "Synthetic", "requirement_ids": [requirement],
        "acceptance_ids": [ac], "outcome": "Synthetic result", "scope": "Small",
        "dependencies": deps or [], "priority": "P1", "verification": "Synthetic test",
        "owner": "UNKNOWN", "status": status, "evidence": evidence or [],
        "blockers": blockers or [], "approvals": [], "risk_ids": [],
    }


def sample():
    return {"schema_version": 1, "requirements": ["R1", "R2", "R3"],
            "acceptance_criteria": ["AC1", "AC2", "AC3", "AC4"],
            "tasks": [task("T1", "R1", "AC1"),
                      task("T2", "R2", "AC3", deps=[{"type": "BLOCKS", "task_id": "T1"}]),
                      task("T3", "R3", "AC4", deps=[{"type": "RELATED", "task_id": "T1"}])],
            "risks": [], "changes": []}


class DeliveryManagementTests(unittest.TestCase):
    def test_optional_profile_and_reuse_without_controller(self):
        self.assertEqual(SKILL, skill_sources(MANIFEST)["project-delivery-management"])
        self.assertEqual(["project-delivery-management"],
                         MANIFEST["extension_packs"]["management"]["skills"])
        profile = MANIFEST["profiles"]["project-delivery-management"]
        self.assertEqual(["project-delivery-management", "task-scoping",
                          "requirements-traceability", "quality-gate-assessment"], profile)
        self.assertNotIn("project-delivery-management", MANIFEST["profiles"]["general"])
        for controller in ("feature-delivery", "make-feature", "adaptive-delivery"):
            self.assertNotIn(controller, profile)

    def test_contract_and_manual_guidance(self):
        self.assertEqual("PROPOSED_NOT_IMPLEMENTED", CONTRACT["artifact_status"])
        for name in ("BLOCKS", "RELATED", "REQUIRES_DECISION", "REQUIRES_APPROVAL", "OPTIONAL"):
            self.assertIn(name, CONTRACT["dependency_types"])
        content = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("Positive triggers:", "Negative triggers:", "read-only", "in chat by default",
                       "NOT_VERIFIED", "VERIFIED", "MERGED", "RELEASED", "UNKNOWN"):
            self.assertIn(phrase, content)
        for name in ("WORKFLOW.md", "HANDOFF.md", "EXAMPLES.md", "MANUAL_ACCEPTANCE.md"):
            self.assertTrue((SKILL / "references" / name).is_file())

    def test_valid_traceability_and_no_unrequired_file_write(self):
        baseline = sample()
        self.assertEqual([], validate(baseline))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for layout in ("codex", "claude"):
                before = sorted(target.rglob("*"))
                preview = operate("install", target, names=["project-delivery-management"],
                                  layout=layout, apply=False)
                self.assertFalse(preview["applied"])
                self.assertEqual(before, sorted(target.rglob("*")))
                installed = operate("install", target, names=["project-delivery-management"],
                                    layout=layout, apply=True)
                self.assertTrue(installed["applied"])
                self.assertIn("project-delivery-management", read_state(target, layout)["skills"])
            for unwanted in ("reports", "plans", "prd", "research"):
                self.assertFalse((target / unwanted).exists())

    def test_unknown_reference_and_duplicate(self):
        p = sample()
        p["tasks"][0]["requirement_ids"] = ["R404"]
        p["tasks"][1]["id"] = "T1"
        self.assertTrue(any("invalid requirement_ids" in x for x in validate(p)))
        self.assertTrue(any("duplicate task id" in x for x in validate(p)))

    def test_cycles_and_missing_prerequisite(self):
        p = sample()
        p["tasks"][0]["dependencies"] = [{"type": "BLOCKS", "task_id": "T2"}]
        self.assertTrue(any("cycle:" in x for x in validate(p)))
        p = sample()
        p["tasks"][1]["dependencies"] = [{"type": "BLOCKS", "task_id": "MISSING"}]
        self.assertTrue(any("unknown blocking predecessor" in x for x in validate(p)))

    def test_status_cannot_promote_without_evidence(self):
        p = sample()
        for status in ("IN_PROGRESS", "VERIFIED", "MERGED", "RELEASED"):
            q = copy.deepcopy(p)
            q["tasks"][0]["status"] = status
            self.assertTrue(validate(q), status)
        p["tasks"][0]["status"] = "BLOCKED"
        self.assertIn("T1: BLOCKED needs an identified blocker", validate(p))
        p["tasks"][0]["blockers"] = ["Unresolved API decision"]
        self.assertEqual([], validate(p))

    def test_workflow_gates_and_dependency(self):
        p = sample()
        p["tasks"][0]["status"] = "VERIFIED"
        p["tasks"][0]["evidence"] = [{"kind": "TEST_PASS", "ref": "synthetic evidence"}]
        p["tasks"][1]["status"] = "IN_PROGRESS"
        p["tasks"][1]["evidence"] = [{"kind": "STARTED", "ref": "synthetic start"}]
        self.assertEqual([], validate(p))
        p["tasks"][0]["status"] = "PLANNED"
        self.assertTrue(any("unsatisfied BLOCKS" in x for x in validate(p)))
        p["tasks"][1]["dependencies"].append(
            {"type": "REQUIRES_APPROVAL", "reference": "Owner D1", "resolved": False})
        self.assertTrue(any("unresolved REQUIRES_APPROVAL" in x for x in validate(p)))

    def test_merge_and_release_require_separate_evidence(self):
        p = sample()
        t = p["tasks"][0]
        t["status"] = "MERGED"
        t["evidence"] = [{"kind": "TEST_PASS", "ref": "CI green"}]
        self.assertTrue(any("merge evidence missing" in x for x in validate(p)))
        t["evidence"].append({"kind": "GITHUB_MERGE", "ref": "exact target SHA"})
        self.assertEqual([], validate(p))
        t["status"] = "RELEASED"
        self.assertTrue(any("release evidence missing" in x for x in validate(p)))
        t["evidence"].append({"kind": "DEPLOY", "ref": "verified deployment"})
        self.assertEqual([], validate(p))

    def test_changes_risks_negative_cases(self):
        p = sample()
        p["changes"] = [{"id": "C1", "type": "NEW_REQUIREMENT",
                         "affected_requirements": ["R4"], "affected_tasks": ["T1"],
                         "dependency_impact": "unknown", "verification_impact": "unknown",
                         "risk_impact": "unknown", "approval": "PENDING"}]
        self.assertTrue(any("unknown R-ID" in x for x in validate(p)))
        p["requirements"].append("R4")
        self.assertEqual([], validate(p))
        p["risks"].append({"id": "K1"})  # incomplete risk register rejected
        self.assertIn("risk missing required fields", validate(p))

    def test_structural_checks_do_not_assert_live_trials(self):
        content = (SKILL / "references/MANUAL_ACCEPTANCE.md").read_text(encoding="utf-8")
        for term in ("not MERGED", "NOT_VERIFIED", "GitHub", "MVP", "cycle"):
            self.assertIn(term.lower(), content.lower())


if __name__ == "__main__":
    unittest.main()
