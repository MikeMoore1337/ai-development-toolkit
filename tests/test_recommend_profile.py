"""Profile recommendations must be reproducible, conservative and read-only."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("recommend_profile", ROOT / "scripts" / "recommend_profile.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))


class ProfileRecommendationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name)

    def check(self, task, profile):
        before = sorted(str(p.relative_to(self.target)) for p in self.target.rglob("*"))
        result = mod.recommend(self.target, task, MANIFEST)
        after = sorted(str(p.relative_to(self.target)) for p in self.target.rglob("*"))
        self.assertEqual(before, after, "Recommendation modified the target")
        self.assertEqual(profile, result["profile"])
        self.assertTrue(result["read_only"])
        self.assertTrue(result["skills"])
        return result

    def test_unknown_stack_uses_general_qa(self):
        self.check("qa", "qa-core")

    def test_python_qa(self):
        (self.target / "pyproject.toml").touch()
        result = self.check("qa", "qa-python")
        self.assertEqual("NOT_VERIFIED", result["detected"]["pytest_installed"])
        self.assertIn("pytest", " ".join(result["warnings"]))

    def test_fullstack_qa(self):
        (self.target / "pyproject.toml").touch()
        (self.target / "package.json").touch()
        result = self.check("qa", "qa-python")
        self.assertIn("qa-fullstack was not selected", " ".join(result["warnings"]))

    def test_fullstack_with_playwright_config_is_heuristic(self):
        (self.target / "pyproject.toml").touch()
        (self.target / "package.json").touch()
        (self.target / "playwright.config.ts").touch()
        result = self.check("qa", "qa-fullstack")
        self.assertEqual("NOT_VERIFIED", result["detected"]["playwright_installed"])
        self.assertIn("qa-core", result["alternatives"])

    def test_playwright_qa(self):
        (self.target / "package.json").touch()
        (self.target / "playwright.config.ts").touch()
        self.check("qa", "qa-ui")

    def test_js_without_browser_stack_stays_general(self):
        (self.target / "package.json").touch()
        self.check("qa", "qa-core")

    def test_explicit_workflow_tasks(self):
        for task, profile in {
            "feature": "codex-feature", "ui": "ui-orchestra", "ux": "ui-orchestra", "ci": "qa-ci",
            "release": "qa-release", "docs": "docs-technical", "docs-edit": "editorial",
            "docs-verify": "docs-technical", "agent": "agent-architecture",
            "backend": "backend", "frontend": "frontend",
            "fullstack": "fullstack",
            "research": "research", "provider": "provider-research",
        }.items():
            with self.subTest(task=task):
                self.check(task, profile)

    def test_visual_design_defaults_to_orchestra_not_generic_ui_fix(self):
        for task in ("ui", "ux"):
            result = self.check(task, "ui-orchestra")
            self.assertEqual("ux-ui-design-orchestra", result["skills"][0])
        self.assertIn("ui-fix", self.check("ui", "ui-orchestra")["optional_profiles"])
        self.assertIn("ux-design", self.check("ux", "ui-orchestra")["optional_profiles"])
        self.assertIn("ui-orchestra", self.check("frontend", "frontend")["optional_profiles"])

    def test_docs_routes_technical_work_to_documentation_maintenance(self):
        selected = self.check("docs", "docs-technical")
        self.assertIn("documentation-maintenance", selected["skills"])
        self.assertIn("clear-voice", selected["optional_skills"])
        self.assertEqual(["clear-voice"], self.check("docs-edit", "editorial")["skills"])

    def test_optional_suggestions_are_separate_and_stable(self):
        result = self.check("frontend", "frontend")
        self.assertEqual(result, mod.recommend(self.target, "frontend", MANIFEST))
        self.assertIn("ui-motion", result["optional_profiles"])
        self.assertIn("motion-quality", result["optional_skills"])
        self.assertIn("state-management", result["optional_skills"])
        self.assertIn("cross-layer-debugging", self.check("fullstack", "fullstack")["optional_skills"])
        self.assertNotIn("motion-quality", result["skills"])
        self.assertEqual(["qa-ci"], self.check("qa", "qa-core")["optional_profiles"])

    def test_optional_suggestions_reference_known_names(self):
        names = set(MANIFEST["core_skills"]) | set(MANIFEST.get("extension_skills", ()))
        for pack in MANIFEST["extension_packs"].values():
            names.update(pack["skills"])
        for task in mod.TASKS:
            with self.subTest(task=task):
                result = mod.recommend(self.target, task, MANIFEST)
                self.assertTrue(set(result["optional_skills"]) <= names)
                self.assertFalse(set(result["skills"]) & set(result["optional_skills"]))
                self.assertTrue(set(result["optional_profiles"]) <= set(MANIFEST["profiles"]))

    def test_unavailable_target_and_bad_task(self):
        with self.assertRaisesRegex(ValueError, "existing directory"):
            mod.recommend(self.target / "not-found", "qa", MANIFEST)
        with self.assertRaisesRegex(ValueError, "Unsupported task"):
            mod.recommend(self.target, "everything", MANIFEST)


if __name__ == "__main__":
    unittest.main()
