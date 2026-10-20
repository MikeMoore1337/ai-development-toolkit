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
    "docs/CLIENT_MIGRATION.md",
    "docs/CLIENT_COMPATIBILITY.md",
    "docs/PUBLICATION_POLICY.md",
    "docs/ADAPTATION.md",
    "docs/PUBLICATION_POLICY.md",
    "docs/ru/README.md",
    "docs/ru/GETTING_STARTED.md",
    "docs/ru/GLOSSARY.md",
    "docs/ru/INSTALLATION.md",
    "docs/ru/SKILLS_CATALOG.md",
    "docs/ru/CURATED_SKILL_PACKS.md",
    "docs/ru/CLIENT_MIGRATION.md",
    "docs/ru/CLIENT_COMPATIBILITY.md",
    "docs/ru/PUBLICATION_POLICY.md",
    "docs/ru/ACCEPTANCE.md",
    "docs/MAKE_FEATURE_INTEGRATION.md",
    "docs/LANGUAGE_POLICY.md",
    "docs/ru/MAKE_FEATURE_INTEGRATION.md",
    "docs/ru/LANGUAGE_POLICY.md",
    "docs/BEGINNER_WORKFLOW.md",
    "docs/QUALITY_RUBRIC.md",
    "docs/ru/BEGINNER_WORKFLOW.md",
    "docs/ru/QUALITY_RUBRIC.md",
    "docs/CLEAR_VOICE_INTEGRATION.md",
    "docs/ru/CLEAR_VOICE_INTEGRATION.md",
    "docs/INTEGRATION_MATRIX.md",
    "docs/PORTABILITY_EVAL_SCENARIOS.md",
    "docs/TASK_PROMPT_TEMPLATE.md",
    "docs/en/ADAPTATION.md",
    "docs/en/INTEGRATION_MATRIX.md",
    "docs/en/PORTABILITY_EVAL_SCENARIOS.md",
    "docs/en/TASK_PROMPT_TEMPLATE.md",
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

        # The expanded catalog links to every SKILL.md and QA role. Populate
        # the fixture with existing link targets, without copying the whole
        # repository or suppressing missing-link detection in the validator.
        for name in FIXTURE_FILES:
            if not name.startswith("docs/ru/"):
                continue
            original = ROOT / name
            for raw in validator.LINK.findall(original.read_text(encoding="utf-8")):
                parsed = validator.urlsplit(raw)
                if parsed.scheme or parsed.netloc or raw.startswith("#"):
                    continue
                target = (original.parent / validator.unquote(parsed.path)).resolve()
                if target.is_file() and target.is_relative_to(ROOT):
                    destination = self.root / target.relative_to(ROOT)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if not destination.exists():
                        shutil.copyfile(target, destination)

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

    def test_stale_skills_catalog_fails(self):
        page = self.root / "docs/ru/SKILLS_CATALOG.md"
        content = page.read_text(encoding="utf-8")
        marker = "| [`adaptive-delivery`]"
        self.assertIn(marker, content)
        page.write_text(content.replace(marker, "| [`unlisted-skill`]", 1), encoding="utf-8")
        self.check("L10N005")

    def test_missing_cli_command_fails(self):
        page = self.root / "docs/ru/INSTALLATION.md"
        content = page.read_text(encoding="utf-8")
        command = "python scripts/skill_manager.py status --target /path/to/repo"
        self.assertIn(command, content)
        page.write_text(content.replace(command, "python scripts/skill_manager.py --help", 1), encoding="utf-8")
        self.check("L10N006")

    def test_missing_reverse_guide_link_fails(self):
        page = self.root / "docs/INSTALLATION.md"
        content = page.read_text(encoding="utf-8")
        self.assertIn("(ru/INSTALLATION.md)", content)
        page.write_text(content.replace("(ru/INSTALLATION.md)", "(INSTALLATION.md)", 1), encoding="utf-8")
        self.check("L10N004")




    def test_russian_original_missing_english_link_fails(self):
        page = self.root / "docs/ADAPTATION.md"
        content = page.read_text(encoding="utf-8")
        self.assertIn("(en/ADAPTATION.md)", content)
        page.write_text(content.replace("(en/ADAPTATION.md)", "(ADAPTATION.md)", 1),
                        encoding="utf-8")
        self.check("L10N004")

    def test_english_companion_missing_original_link_fails(self):
        page = self.root / "docs/en/TASK_PROMPT_TEMPLATE.md"
        content = page.read_text(encoding="utf-8")
        self.assertIn("(../TASK_PROMPT_TEMPLATE.md)", content)
        page.write_text(content.replace("(../TASK_PROMPT_TEMPLATE.md)",
                                        "(../LANGUAGE_POLICY.md)", 1), encoding="utf-8")
        self.check("L10N004")

    def test_russian_beginner_workflow_missing_fails(self):
        (self.root / "docs/ru/BEGINNER_WORKFLOW.md").unlink()
        self.check("L10N001")

    def test_quality_rubric_missing_language_link_fails(self):
        page = self.root / "docs/QUALITY_RUBRIC.md"
        text = page.read_text(encoding="utf-8")
        self.assertIn("(ru/QUALITY_RUBRIC.md)", text)
        page.write_text(text.replace("(ru/QUALITY_RUBRIC.md)", "(QUALITY_RUBRIC.md)", 1),
                        encoding="utf-8")
        self.check("L10N004")

    def test_beginner_missing_critical_gate_fails(self):
        page = self.root / "docs/ru/BEGINNER_WORKFLOW.md"
        text = page.read_text(encoding="utf-8")
        self.assertIn("EXTERNAL", text)
        page.write_text(text.replace("EXTERNAL", "UNRESTRICTED", 100),
                        encoding="utf-8")
        self.check("L10N009")

    def test_rubric_missing_release_gate_fails(self):
        page = self.root / "docs/ru/QUALITY_RUBRIC.md"
        text = page.read_text(encoding="utf-8")
        self.assertIn("--mode release", text)
        page.write_text(text.replace("--mode release", "--mode casual", 100),
                        encoding="utf-8")
        self.check("L10N009")

    def test_clear_voice_missing_reverse_link_fails(self):
        page = self.root / "docs/CLEAR_VOICE_INTEGRATION.md"
        content = page.read_text(encoding="utf-8")
        self.assertIn("(ru/CLEAR_VOICE_INTEGRATION.md)", content)
        page.write_text(content.replace("(ru/CLEAR_VOICE_INTEGRATION.md)",
                                        "(CLEAR_VOICE_INTEGRATION.md)", 1),
                        encoding="utf-8")
        self.check("L10N004")

    def test_clear_voice_missing_install_preview_fails(self):
        page = self.root / "docs/ru/CLEAR_VOICE_INTEGRATION.md"
        content = page.read_text(encoding="utf-8")
        command = "python scripts/skill_manager.py install --target /path/to/repo --profile editorial"
        self.assertIn(command, content)
        page.write_text(content.replace(command, "echo no-preview", 1), encoding="utf-8")
        self.check("L10N006")

    def test_clear_voice_missing_not_tested_fails(self):
        page = self.root / "docs/ru/CLEAR_VOICE_INTEGRATION.md"
        content = page.read_text(encoding="utf-8")
        self.assertIn("NOT_TESTED", content)
        page.write_text(content.replace("NOT_TESTED", "PASS", 100), encoding="utf-8")
        self.check("L10N009")

    def test_make_feature_missing_reverse_link_fails(self):
        page = self.root / "docs/MAKE_FEATURE_INTEGRATION.md"
        content = page.read_text(encoding="utf-8")
        self.assertIn("(ru/MAKE_FEATURE_INTEGRATION.md)", content)
        page.write_text(content.replace("(ru/MAKE_FEATURE_INTEGRATION.md)", "(INSTALLATION.md)", 1),
                        encoding="utf-8")
        self.check("L10N004")

    def test_make_feature_missing_preview_fails(self):
        page = self.root / "docs/ru/MAKE_FEATURE_INTEGRATION.md"
        content = page.read_text(encoding="utf-8")
        original = "python scripts/skill_manager.py install --target /path/to/project --profile make-feature"
        self.assertIn(original, content)
        page.write_text(content.replace(original, "echo no preview", 1), encoding="utf-8")
        self.check("L10N006")

    def test_make_feature_missing_safety_gate_fails(self):
        page = self.root / "docs/ru/MAKE_FEATURE_INTEGRATION.md"
        content = page.read_text(encoding="utf-8")
        self.assertIn("INDEPENDENT_REVIEW", content)
        page.write_text(content.replace("INDEPENDENT_REVIEW", "own-approval", 100), encoding="utf-8")
        self.check("L10N009")

    def test_advanced_guide_language_link_fails(self):
        page = self.root / "docs/CLIENT_MIGRATION.md"
        text = page.read_text(encoding="utf-8")
        self.assertIn("(ru/CLIENT_MIGRATION.md)", text)
        page.write_text(text.replace("(ru/CLIENT_MIGRATION.md)", "(CLIENT_MIGRATION.md)", 1),
                        encoding="utf-8")
        self.check("L10N004")

    def test_missing_migration_command_fails(self):
        page = self.root / "docs/ru/CLIENT_MIGRATION.md"
        text = page.read_text(encoding="utf-8")
        command = "python scripts/skill_manager.py migrate --target /tmp/adt-cli-python-demo --from-layout codex --layout claude --apply"
        self.assertIn(command, text)
        page.write_text(text.replace(command, "echo missing command", 1), encoding="utf-8")
        self.check("L10N006")

    def test_missing_client_verification_command_fails(self):
        page = self.root / "docs/ru/CLIENT_COMPATIBILITY.md"
        text = page.read_text(encoding="utf-8")
        command = "python scripts/verify_client_compatibility.py --project /tmp/demo --client codex --skills qa-strategy"
        self.assertIn(command, text)
        page.write_text(text.replace(command, "echo omitted", 1), encoding="utf-8")
        self.check("L10N006")

    def test_removed_release_gate_fails(self):
        page = self.root / "docs/ru/PUBLICATION_POLICY.md"
        text = page.read_text(encoding="utf-8")
        self.assertIn("--mode release", text)
        page.write_text(text.replace("--mode release", "--mode inventory", 1),
                        encoding="utf-8")
        self.check("L10N009")


if __name__ == "__main__":
    unittest.main()
