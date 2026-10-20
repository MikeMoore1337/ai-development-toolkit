"""Independent known-bad security mutants and offline contract regression tests."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_security as security  # noqa: E402
from install import skill_sources  # noqa: E402
from skill_manager import operate, read_state  # noqa: E402
import json


class SecurityContracts(unittest.TestCase):
    def test_complete_threat_control_risk_links(self):
        packet = security.sample_packet()
        security.validate_packet(packet)
        for category, field in (
            ("threats", "asset"), ("threats", "trust_boundary"),
            ("threats", "actor"), ("controls", "invariant"),
            ("controls", "expected_allow"), ("controls", "forbidden_side_effects"),
            ("risks", "likelihood"), ("risks", "residual_risk"),
        ):
            broken = copy.deepcopy(packet)
            broken[category][0][field] = ""
            with self.subTest(category=category, field=field):
                with self.assertRaises(ValueError):
                    security.validate_packet(broken)

    def test_unproved_mitigation_and_unexecuted_claims(self):
        for status, evidence in (("MITIGATED", ""), ("IMPOSSIBLE", "rumor")):
            packet = security.sample_packet()
            packet["threats"][0]["risk_status"] = status
            packet["threats"][0]["evidence"] = evidence
            with self.assertRaises(ValueError):
                security.validate_packet(packet)
        for status, evidence in (("PASS", ""), ("NOT_TESTED", "invented run")):
            packet = security.sample_packet()
            packet["controls"][0].update(status=status, actual_evidence=evidence)
            with self.assertRaises(ValueError):
                security.validate_packet(packet)

    def test_reference_and_each_independent_mutant(self):
        self.assertEqual(10, len(security.CASES))
        for case in security.CASES:
            with self.subTest(case=case):
                self.assertTrue(security.oracle(case, security.observation(case)))
                self.assertFalse(security.oracle(case, security.observation(case, True)))
        result = security.run_cases()
        self.assertEqual((10, 10), (result["reference_pass"], result["mutants_rejected"]))
        self.assertEqual("NOT_MEASURED", result["real_assessment"])

    def test_allowed_actions_and_expired_session(self):
        own = {"user": "user-A", "tenant": "tenant-A", "body": "fictional-A"}
        foreign = {"user": "user-B", "tenant": "tenant-B", "body": "fictional-B"}
        for action in ("read", "update", "delete"):
            result = security.note_operation("user-A", own, action)
            self.assertEqual("ALLOW", result["response"])
        expired = security.note_operation("user-A", own, "update", session=False)
        self.assertEqual("DENY", expired["response"])
        self.assertEqual(expired["before"], expired["after"])
        denied = security.note_operation("user-A", foreign, "delete")
        self.assertEqual("DENY", denied["response"])
        self.assertEqual(denied["before"], denied["after"])

    def test_ci_authority_and_tool_scope(self):
        allowed = {"fork_pr": True, "permissions": "contents:read",
                   "secrets": False, "unsafe_checkout": False,
                   "shell_interpolation": False}
        self.assertTrue(security.ci_policy(allowed))
        for key, value in (("permissions", "contents:write"), ("secrets", True),
                           ("unsafe_checkout", True), ("shell_interpolation", True)):
            bad = dict(allowed, **{key: value})
            self.assertFalse(security.ci_policy(bad))
        self.assertTrue(security.tool_scope("/workspace/notes/readme.txt"))
        self.assertFalse(security.tool_scope("/workspace/notes/../../secret"))
        self.assertFalse(security.tool_scope("/workspace-private/notes/file"))

    def test_install_preview_apply_and_source_storage_boundary(self):
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        names = manifest["profiles"]["security-engineering"]
        self.assertEqual(names, ["security-engineering", "security-boundaries",
                                 "security-review", "security-testing"])
        self.assertIn("security-engineering", skill_sources(manifest))
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            source = ROOT / "extensions/security/skills/security-engineering/SKILL.md"
            unchanged = source.read_bytes()
            for layout in ("codex", "claude"):
                preview = operate("install", target, names=names, layout=layout)
                self.assertFalse(preview["applied"])
                applied = operate("install", target, names=names, layout=layout,
                                  apply=True)
                self.assertTrue(applied["applied"])
                self.assertEqual(set(names), set(read_state(target, layout)["skills"]))
            self.assertEqual(unchanged, source.read_bytes())
            self.assertFalse(list(ROOT.glob("user-security-report*")))


if __name__ == "__main__":
    unittest.main()
