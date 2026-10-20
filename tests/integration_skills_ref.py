"""Run only in the CI step that installs the pinned official upstream CLI.

These fixtures invoke the REAL skills-ref binary, not a mock.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("upstream_integration_runner", ROOT / "scripts" / "validate_with_skills_ref.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RealSkillsRefIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = shutil.which("skills-ref")
        if cls.binary is None:
            raise RuntimeError("The official CLI must be installed for this integration suite")

    def check_fixture(self, skill_name: str, skill_body: str | None, *, valid: bool):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / skill_name
            folder.mkdir()
            if skill_body is not None:
                (folder / "SKILL.md").write_text(skill_body, encoding="utf-8")
            result = subprocess.run(
                [self.binary, "validate", str(folder)],
                capture_output=True, text=True, timeout=15, check=False,
            )
            if valid:
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(f"Valid skill: {folder}", result.stdout.strip())
            else:
                self.assertNotEqual(0, result.returncode, result.stdout)
                self.assertIn("Validation failed", result.stderr)

    def test_valid_skill(self):
        self.check_fixture(
            "valid-skill",
            "---\nname: valid-skill\ndescription: Describes when to use the skill.\n---\n\nInstructions.\n",
            valid=True,
        )

    def test_missing_skill_md(self):
        self.check_fixture("missing-skill", None, valid=False)

    def test_malformed_yaml(self):
        self.check_fixture(
            "bad-yaml", "---\nname: [unterminated\ndescription: Broken YAML\n---\n", valid=False,
        )

    def test_invalid_name(self):
        self.check_fixture(
            "bad-name", "---\nname: WrongName\ndescription: Incorrect directory/name.\n---\n", valid=False,
        )

    def test_missing_required_description(self):
        self.check_fixture("no-description", "---\nname: no-description\n---\n", valid=False)

    def test_quality_v2_template_with_official_cli(self):
        """Check the copyable template using pinned upstream skills-ref."""
        folder = ROOT / "templates" / "skill-quality-v2" / "example-skill"
        result = subprocess.run(
            [self.binary, "validate", str(folder)],
            capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(f"Valid skill: {folder}", result.stdout.strip())

    def test_entire_manifest_with_real_official_cli(self):
        self.assertEqual(70, len(runner.skill_directories(ROOT, "all")))
        self.assertEqual(0, runner.run("all", ROOT))


if __name__ == "__main__":
    unittest.main()
