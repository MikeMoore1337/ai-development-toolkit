"""Ensure official Agent Skills validation covers every declared skill."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("upstream_validator", ROOT / "scripts" / "validate_with_skills_ref.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class OfficialCoverageTests(unittest.TestCase):
    def test_all_declared_skills_are_covered(self):
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        count = len(manifest["core_skills"]) + len(manifest.get("extension_skills", []))
        count += sum(len(pack["skills"]) for pack in manifest["extension_packs"].values())
        declared = validator.skill_directories(ROOT, "all")
        self.assertEqual(count, len(declared))
        self.assertTrue(any("extensions/qa/" in path.as_posix() for path in declared))
        self.assertTrue(any("extensions/make-feature/" in path.as_posix() for path in declared))
        self.assertTrue(all((p / "SKILL.md").exists() for p in declared))

    def test_core_does_not_include_optional_packs(self):
        paths = validator.skill_directories(ROOT, "core")
        self.assertEqual(24, len(paths))
        self.assertTrue(all(".agents/skills/" in p.as_posix() for p in paths))

    def test_missing_declared_skill_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "MANIFEST.json").write_text(
                json.dumps({"core_skills": ["absent"], "extension_skills": [],
                            "extension_packs": {}}), encoding="utf-8",
            )
            with self.assertRaises(FileNotFoundError):
                validator.skill_directories(root)

    def test_upstream_not_installed_is_not_reported_as_pass(self):
        with patch.object(validator.shutil, "which", return_value=None):
            self.assertEqual(2, validator.run("core"))


if __name__ == "__main__":
    unittest.main()
