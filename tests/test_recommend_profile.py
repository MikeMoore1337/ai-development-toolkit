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
        self.check("qa", "qa-python")

    def test_fullstack_qa(self):
        (self.target / "pyproject.toml").touch()
        (self.target / "package.json").touch()
        self.check("qa", "qa-fullstack")

    def test_playwright_qa(self):
        (self.target / "package.json").touch()
        (self.target / "playwright.config.ts").touch()
        self.check("qa", "qa-ui")

    def test_js_without_browser_stack_stays_general(self):
        (self.target / "package.json").touch()
        self.check("qa", "qa-core")

    def test_explicit_workflow_tasks(self):
        for task, profile in {
            "feature": "codex-feature", "ui": "ui-fix", "ci": "qa-ci",
            "release": "qa-release", "docs": "editorial", "agent": "agent-architecture",
            "backend": "backend", "frontend": "frontend",
            "research": "research", "provider": "provider-research",
        }.items():
            with self.subTest(task=task):
                self.check(task, profile)

    def test_optional_suggestions_are_separate_and_stable(self):
        result = self.check("frontend", "frontend")
        self.assertEqual(result, mod.recommend(self.target, "frontend", MANIFEST))
        self.assertIn("ui-motion", result["optional_profiles"])
        self.assertIn("motion-quality", result["optional_skills"])
        self.assertNotIn("motion-quality", result["skills"])
        self.assertEqual(["qa-ci"], self.check("qa", "qa-core")["optional_profiles"])

    def test_optional_suggestions_reference_known_names(self):
        names = {skill for skills in MANIFEST["profiles"].values() for skill in skills}
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
