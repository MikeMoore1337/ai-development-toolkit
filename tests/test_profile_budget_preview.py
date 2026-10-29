"""Read-only byte-budget preview; synthetic files do not represent model tokens."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("profile_metrics", ROOT / "scripts/profile_metrics.py")
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class BudgetPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = {"core_skills": ["alpha", "beta"], "extension_skills": [],
                         "extension_packs": {}, "profiles": {"focused": ["alpha", "beta"]}}
        self.source = {}
        for name in ("alpha", "beta"):
            folder = self.root / ".agents" / "skills" / name
            folder.mkdir(parents=True)
            text = f"---\nname: {name}\ndescription: Test only\n---\n\n# Body excluded\n"
            (folder / "SKILL.md").write_text(text, encoding="utf-8")
            self.source[name] = text.split("---\n", 2)[0:2]

    def test_budget_is_readonly_and_counts_only_metadata(self):
        before = sorted(str(x) for x in self.root.rglob("*"))
        result = mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)
        self.assertTrue(result["within_budget"])
        self.assertEqual("NOT_MEASURED", result["tokens"])
        self.assertEqual("NOT_VERIFIED", result["activation"])
        self.assertFalse(result["applied"])
        self.assertFalse(result["automatic_pruning"])
        self.assertEqual(2, len(result["skill_metadata"]))
        self.assertEqual(sum(x["metadata_bytes"] for x in result["skill_metadata"]),
                         result["eager_metadata_bytes"])
        self.assertEqual(before, sorted(str(x) for x in self.root.rglob("*")))

    def test_small_budget_fails_as_preview_without_skipping_required_skill(self):
        result = mod.preview_metadata_budget(self.root, self.manifest, "focused", 1)
        self.assertFalse(result["within_budget"])
        self.assertGreater(result["over_budget_bytes"], 0)
        self.assertEqual(["alpha", "beta"], [x["skill"] for x in result["skill_metadata"]])

    def test_invalid_and_ambiguous_budget_rejected(self):
        for budget in (True, False, 0, -1, 1_000_001, 3.4, "2000"):
            with self.subTest(budget=budget):
                with self.assertRaises(ValueError):
                    mod.preview_metadata_budget(self.root, self.manifest, "focused", budget)
        with self.assertRaisesRegex(ValueError, "Unknown profile"):
            mod.preview_metadata_budget(self.root, self.manifest, "absent", 100)

    def test_unlisted_or_duplicate_skill_rejected(self):
        self.manifest["profiles"]["focused"] = ["alpha", "missing"]
        with self.assertRaisesRegex(ValueError, "Unknown skill"):
            mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)
        self.manifest["profiles"]["focused"] = ["alpha", "alpha"]
        with self.assertRaisesRegex(ValueError, "Invalid profile"):
            mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)

    def test_missing_frontmatter_is_not_inferred(self):
        source = self.root / ".agents" / "skills" / "alpha" / "SKILL.md"
        source.write_text("# Header without YAML\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Missing YAML"):
            mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)


if __name__ == "__main__":
    unittest.main()
