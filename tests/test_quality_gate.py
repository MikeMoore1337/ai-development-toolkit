"""Offline quality gate negative fixtures and cross-platform regressions."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_quality", ROOT / "scripts/validate_quality.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class QualityGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skills = ["adaptive-delivery", "feature-delivery", "implementation", "make-feature"]
        self.manifest = {
            "core_skills": self.skills,
            "core_roles": ["orchestrator"],
            "extension_packs": {},
            "profiles": {"general": ["implementation"], "feature": ["feature-delivery", "implementation"]},
        }
        self.file("MANIFEST.json", json.dumps(self.manifest))
        self.file("docs/QUALITY_RULES.json", json.dumps({
            "schema_version": 1,
            "exclusive_workflows": [
                {"rule_id": "WF001", "skills": ["feature-delivery", "make-feature"], "reason": "select one"},
                {"rule_id": "WF002", "skills": ["adaptive-delivery", "feature-delivery"], "reason": "legacy"},
            ],
        }))
        self.file(".agents/roles/orchestrator.md", "# Orchestrator\n")
        for name in self.skills:
            self.file(f".agents/skills/{name}/SKILL.md", "# Skill\n")

    def file(self, path: str, content: str) -> Path:
        out = self.root / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        return out

    def check(self, rule: str | None = None) -> dict:
        report = module.inspect(self.root)
        ids = [x["rule_id"] for x in report["findings"]]
        if rule:
            self.assertIn(rule, ids, report)
            self.assertEqual("FAIL", report["status"])
        else:
            self.assertEqual("PASS", report["status"], report)
        return report

    def test_real_package(self):
        actual = module.inspect(ROOT)
        self.assertEqual("PASS", actual["status"], actual["findings"][:15])
        self.assertEqual(51, actual["counts"]["skills"])
        self.assertEqual(16, actual["counts"]["roles"])
        self.assertEqual(23, actual["counts"]["profiles"])

    def test_valid_inventory_profile_and_allowed_workflow(self):
        self.check()

    def test_missing_skill_in_profile(self):
        self.manifest["profiles"]["general"].append("phantom")
        self.file("MANIFEST.json", json.dumps(self.manifest))
        self.check("PROFILE001")

    def test_missing_role(self):
        (self.root / ".agents/roles/orchestrator.md").unlink()
        self.check("INV001")

    def test_broken_link(self):
        self.file(".agents/skills/implementation/SKILL.md", "[doc](references/missing.md)\n")
        self.check("LINK001")

    def test_outside_package_path(self):
        self.file(".agents/skills/implementation/SKILL.md", "[private](../../../../outside.md)\n")
        self.check("PATH001")

    def test_windows_style_local_path_rejected(self):
        self.file(".agents/skills/implementation/SKILL.md", r"[private](C:\private\file.md)" + "\n")
        self.check("PATH001")

    def test_valid_anchor_duplicate_headings_and_encoded_path(self):
        self.file(".agents/skills/implementation/references/a b.md",
                  "# Some Heading\n# Some Heading\n")
        self.file(".agents/skills/implementation/SKILL.md",
                  "[one](references/a%20b.md#some-heading)\n"
                  "[two](references/a%20b.md#some-heading-1)\n")
        self.check()

    def test_invalid_anchor(self):
        self.file(".agents/skills/implementation/references/detail.md", "# Valid\n")
        self.file(".agents/skills/implementation/SKILL.md",
                  "[bad](references/detail.md#absent)\n")
        self.check("ANCHOR001")

    def test_fenced_and_inline_examples_not_links(self):
        self.file(".agents/skills/implementation/SKILL.md",
                  "~~~md\n[example](missing.md)\n~~~\n"
                  "Use " + chr(96) + "[sample](other.md)" + chr(96) + " inline.\n")
        self.check()

    def test_reference_link_and_external_links(self):
        self.file(".agents/skills/implementation/SKILL.md",
                  "[doc][id]\n[id]: references/missing.md\n"
                  "[remote](https://example.org/docs?x=1)\n")
        self.check("LINK001")

    def test_disallowed_feature_workflow_combination(self):
        self.manifest["profiles"]["feature"].append("make-feature")
        self.file("MANIFEST.json", json.dumps(self.manifest))
        self.check("WF001")

    def test_legacy_conflict(self):
        self.manifest["profiles"]["feature"].append("adaptive-delivery")
        self.file("MANIFEST.json", json.dumps(self.manifest))
        self.check("WF002")

    def test_invalid_quality_rules_fail_closed(self):
        self.file("docs/QUALITY_RULES.json", "{}")
        self.check("CONFIG001")

    def test_unrecognized_skill_in_quality_rules_fails_closed(self):
        self.file("docs/QUALITY_RULES.json", json.dumps({
            "schema_version": 1,
            "exclusive_workflows": [{"rule_id": "WF001", "skills": ["implementation", "missing"],
                                     "reason": "invalid"}],
        }))
        self.check("CONFIG001")

    def test_report_is_deterministic(self):
        self.assertEqual(module.inspect(self.root), module.inspect(self.root))
        self.check()


if __name__ == "__main__":
    unittest.main()
