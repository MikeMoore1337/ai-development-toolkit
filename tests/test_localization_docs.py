"""Positive and negative offline regressions for Russian docs onboarding (#78)."""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "toolkit_localization_validator", ROOT / "scripts/validate_localization.py"
)
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

FIXTURE_FILES = (
    "README.md",
    "README.ru.md",
    "CONTRIBUTING.md",
    "docs/INSTALLATION.md",
    "docs/SKILLS_CATALOG.md",
    "docs/CURATED_SKILL_PACKS.md",
    "docs/ADAPTATION.md",
    "docs/PUBLICATION_POLICY.md",
    "docs/ru/README.md",
    "docs/ru/GETTING_STARTED.md",
    "docs/ru/GLOSSARY.md",
)


class RussianOnboardingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        for name in FIXTURE_FILES:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)

    def check(self, expected: str | None = None):
        findings = validator.validate(self.root)
        if expected:
            self.assertTrue(any(f.startswith(expected) for f in findings), findings)
        else:
            self.assertEqual(findings, [])

    def test_current_russian_onboarding(self):
        self.check()

    def test_missing_page_fails(self):
        (self.root / "docs/ru/GLOSSARY.md").unlink()
        self.check("L10N001")

    def test_broken_internal_link_fails(self):
        page = self.root / "docs/ru/README.md"
        page.write_text(
            page.read_text(encoding="utf-8") + "\n[Broken](MISSING.md)\n",
            encoding="utf-8",
        )
        self.check("L10N002")

    def test_missing_preview_fails(self):
        page = self.root / "docs/ru/GETTING_STARTED.md"
        content = page.read_text(encoding="utf-8")
        before = "python scripts/skill_manager.py install --target ../toolkit-demo --profile general\n"
        self.assertIn(before, content)
        page.write_text(content.replace(before, "", 1), encoding="utf-8")
        self.check("L10N003")

    def test_missing_language_navigation_fails(self):
        page = self.root / "README.ru.md"
        content = page.read_text(encoding="utf-8")
        self.assertIn("(docs/ru/GETTING_STARTED.md)", content)
        page.write_text(
            content.replace("(docs/ru/GETTING_STARTED.md)", "(docs/INSTALLATION.md)"),
            encoding="utf-8",
        )
        self.check("L10N004")


if __name__ == "__main__":
    unittest.main()
