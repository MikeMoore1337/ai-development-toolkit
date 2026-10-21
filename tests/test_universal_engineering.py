"""Technology-neutral engineering extension inventory and installation regressions."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install import install, skill_sources
from skill_manager import operate, read_state
from validate_pack import inspect, validate_skill

M = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
EXPECTED = {
    "frontend": {"component-architecture", "state-management",
                 "frontend-api-integration", "forms-validation", "frontend-performance"},
    "backend": {"service-architecture", "api-design", "data-access",
                "database-migrations", "background-processing",
                "authentication-authorization"},
    "fullstack": {"fullstack-integration", "cross-layer-debugging",
                  "end-to-end-feature-design"},
}


class UniversalEngineeringTests(unittest.TestCase):
    def test_three_opt_in_packs_and_unique_metadata(self):
        self.assertEqual([], inspect())
        self.assertEqual(76, len(skill_sources(M)))
        for pack, expected in EXPECTED.items():
            with self.subTest(pack=pack):
                cfg = M["extension_packs"][pack]
                self.assertFalse(cfg["auto_install"])
                self.assertEqual(expected, set(cfg["skills"]))
                self.assertEqual(len(expected), len(cfg["skills"]))
                root = ROOT / cfg["skill_root"]
                self.assertEqual(expected, {p.parent.name for p in root.glob("*/SKILL.md")})
                for name in expected:
                    skill = root / name
                    self.assertEqual([], validate_skill(skill))
                    content = (skill / "SKILL.md").read_text(encoding="utf-8")
                    self.assertIn("**Output:**", content)
                    self.assertIn("approval", content.lower())

    def test_selected_profiles_do_not_auto_include_unrelated_extensions(self):
        frontend = set(M["profiles"]["frontend"])
        backend = set(M["profiles"]["backend"])
        fullstack = set(M["profiles"]["fullstack"])
        qa = set(M["extension_packs"]["qa"]["skills"])
        self.assertTrue({"component-architecture", "frontend-api-integration"} <= frontend)
        self.assertTrue({"service-architecture", "api-design"} <= backend)
        self.assertTrue({"end-to-end-feature-design", "fullstack-integration"} <= fullstack)
        self.assertFalse((frontend | backend | fullstack) & qa)
        self.assertFalse(set(M["profiles"]["general"]) & set.union(*EXPECTED.values()))
        self.assertFalse((frontend | backend | fullstack) & {"feature-delivery", "make-feature"})

    def test_preview_and_install_in_both_client_layouts(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "AGENTS.md").write_text("project gates\n", encoding="utf-8")
            (target / "CLAUDE.md").write_text("project gates\n", encoding="utf-8")
            for profile, layout in (("frontend", "codex"), ("backend", "claude")):
                selected = M["profiles"][profile]
                existing = sorted(p.name for p in target.iterdir())
                planned = operate("install", target, names=selected, layout=layout)
                self.assertFalse(planned["applied"])
                self.assertEqual(existing, sorted(p.name for p in target.iterdir()))
                installed = operate("install", target, names=selected, layout=layout,
                                    apply=True)
                self.assertTrue(installed["applied"])
                self.assertEqual(set(selected), set(read_state(target, layout)["skills"]))
                parent = ".agents" if layout == "codex" else ".claude"
                for name in selected:
                    self.assertTrue((target / parent / "skills" / name / "SKILL.md").is_file())
            self.assertEqual("project gates\n", (target / "AGENTS.md").read_text())
            self.assertEqual("project gates\n", (target / "CLAUDE.md").read_text())


    def test_design_only_and_optional_single_controller(self):
        """Static integration contract; does not establish real agent activation."""
        manifest = M
        names = set(skill_sources(manifest))
        profile = set(manifest["profiles"]["fullstack"])
        controllers = {"feature-delivery", "make-feature"}
        self.assertFalse(profile & controllers)
        self.assertTrue(controllers <= names)
        design = (ROOT / "extensions/fullstack/skills/end-to-end-feature-design/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Design-only request:", design)
        self.assertIn("Implementation request:", design)
        self.assertIn("Do not start or require a delivery controller", design)
        rules = json.loads((ROOT / "docs/QUALITY_RULES.json").read_text(encoding="utf-8"))
        wf001 = next(rule for rule in rules["exclusive_workflows"] if rule["rule_id"] == "WF001")
        self.assertEqual(controllers, set(wf001["skills"]))
        for chosen in ({"feature-delivery"}, {"make-feature"}):
            selected = profile | chosen
            self.assertEqual(1, len(selected & controllers))
        self.assertEqual(2, len(profile | controllers) - len(profile))

    def test_optional_engineering_examples_are_packaged(self):
        """Ensure references survive copy/install, rather than only existing in source."""
        example = {
            "state-management": "stale-response.md",
            "frontend-performance": "baseline-comparison.md",
            "api-design": "compatible-evolution.md",
            "database-migrations": "expand-migrate-contract.md",
            "fullstack-integration": "account-preferences.md",
            "end-to-end-feature-design": "design-handoff.md",
        }
        sources = skill_sources(M)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            install(target, sorted(example), True)
            for skill, reference in example.items():
                with self.subTest(skill=skill):
                    src = sources[skill]
                    ref = src / "references" / reference
                    dest = target / ".agents" / "skills" / skill / "references" / reference
                    self.assertTrue(ref.is_file())
                    self.assertTrue(dest.is_file())
                    self.assertEqual(ref.read_bytes(), dest.read_bytes())

    def test_fullstack_opt_in_is_selective(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            install(target, M["profiles"]["fullstack"], False)
            self.assertFalse((target / ".agents").exists())
            install(target, ["cross-layer-debugging"], True)
            self.assertTrue((target / ".agents/skills/cross-layer-debugging/SKILL.md").is_file())
            self.assertFalse((target / ".agents/skills/background-processing").exists())


if __name__ == "__main__":
    unittest.main()
