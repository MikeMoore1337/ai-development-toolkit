"""Reproducible source-drift behavior for translated documentation (#78)."""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "toolkit_translation_freshness", ROOT / "scripts/check_translation_freshness.py"
)
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class TranslationSourceFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        names = ["docs/ru/SOURCE_REVISIONS.json"]
        names.extend(
            p for pair in __import__("json").loads(
                (ROOT / names[0]).read_text(encoding="utf-8")
            )["pairs"] for p in (pair["source"], pair["translation"])
        )
        for name in names:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)

    def test_current_source_revisions(self):
        self.assertEqual(mod.check(self.root), ([], []))

    def test_editorial_source_change_only_warns(self):
        source = self.root / "docs/INSTALLATION.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nEditorial update.\n", encoding="utf-8")
        errors, warnings = mod.check(self.root)
        self.assertFalse(errors)
        self.assertEqual(len(warnings), 1)
        self.assertIn("L10N008", warnings[0])
        self.assertNotIn("Editorial update", warnings[0])

    def test_missing_translation_blocks(self):
        (self.root / "docs/ru/INSTALLATION.md").unlink()
        errors, warnings = mod.check(self.root)
        self.assertTrue(any(x.startswith("L10N007") for x in errors))
        self.assertFalse(warnings)

    def test_path_traversal_rejected(self):
        metadata = self.root / "docs/ru/SOURCE_REVISIONS.json"
        content = metadata.read_text(encoding="utf-8")
        metadata.write_text(content.replace("docs/INSTALLATION.md", "../private.txt", 1), encoding="utf-8")
        errors, _ = mod.check(self.root)
        self.assertTrue(any(x.startswith("L10N007") for x in errors))

    def test_russian_original_change_warns_not_blocks(self):
        source = self.root / "docs/ADAPTATION.md"
        self.assertTrue(source.is_file())
        source.write_text(source.read_text(encoding="utf-8") + "\nEditorial RU update.\n",
                          encoding="utf-8")
        errors, warnings = mod.check(self.root)
        self.assertEqual(errors, [])
        self.assertTrue(any("docs/en/ADAPTATION.md" in w for w in warnings), warnings)
        self.assertFalse(any("Editorial RU update" in w for w in warnings))

    def test_unsupported_source_language_rejected(self):
        path = self.root / "docs/ru/SOURCE_REVISIONS.json"
        content = path.read_text(encoding="utf-8")
        self.assertIn('"source_language": "ru"', content)
        path.write_text(content.replace('"source_language": "ru"',
                                        '"source_language": "unknown"', 1),
                        encoding="utf-8")
        errors, _ = mod.check(self.root)
        self.assertTrue(any(x.startswith("L10N007") for x in errors), errors)

    def test_reverse_unsafe_translation_path_rejected(self):
        path = self.root / "docs/ru/SOURCE_REVISIONS.json"
        content = path.read_text(encoding="utf-8")
        self.assertIn('"translation": "docs/en/ADAPTATION.md"', content)
        path.write_text(content.replace('"translation": "docs/en/ADAPTATION.md"',
                                        '"translation": "../unsafe.md"', 1),
                        encoding="utf-8")
        errors, _ = mod.check(self.root)
        self.assertTrue(any(x.startswith("L10N007") for x in errors), errors)

    def test_malformed_metadata_blocks(self):
        (self.root / "docs/ru/SOURCE_REVISIONS.json").write_text("{", encoding="utf-8")
        errors, _ = mod.check(self.root)
        self.assertTrue(any(x.startswith("L10N007") for x in errors))


if __name__ == "__main__":
    unittest.main()
