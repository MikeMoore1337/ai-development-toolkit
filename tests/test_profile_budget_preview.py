"""Read-only byte-budget preview; synthetic files do not represent model tokens."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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


    def test_utf8_bytes_and_indented_delimiter(self):
        source = self.root / ".agents" / "skills" / "alpha" / "SKILL.md"
        original = (
            "---\\r\\nname: alpha\\r\\ndescription: |\\r\\n"
            "  Пример 🧪\\r\\n  ---\\r\\n  продолжение\\r\\n"
            "---\\r\\n\\r\\n# Body not counted\\r\\n"
        ).replace("\\r", "\r").replace("\\n", "\n")
        source.write_bytes(original.encode("utf-8"))
        result = mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)
        counted = original.encode("utf-8").split(b"---" + bytes((13, 10, 13, 10)))[0]
        self.assertEqual(len(counted) + len(b"---") + 2, result["skill_metadata"][0]["metadata_bytes"])
        self.assertEqual("NOT_MEASURED", result["tokens"])

    def test_invalid_yaml_and_duplicate_keys_are_rejected(self):
        source = self.root / ".agents" / "skills" / "alpha" / "SKILL.md"
        for contents in (
            "---\\nname: alpha\\ndescription: [unclosed\\n---\\n",
            "---\\nname: alpha\\nname: alpha\\ndescription: duplicate\\n---\\n",
            "---\\nname: wrong\\ndescription: mismatch\\n---\\n",
            "---\\ndescription: no name\\n---\\n",
        ):
            with self.subTest(contents=contents):
                source.write_text(contents.replace("\\n", "\n"), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Invalid skill frontmatter"):
                    mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)

    def test_invalid_utf8_and_unreadable_metadata_are_rejected(self):
        source = self.root / ".agents" / "skills" / "alpha" / "SKILL.md"
        source.write_bytes("---\nname: alpha\ndescription: ".encode() + bytes([255]) + "\n---\n".encode())
        with self.assertRaisesRegex(ValueError, "Non-UTF8 skill metadata"):
            mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)
        source.write_text("---\\nname: alpha\\ndescription: Ok\\n---\\n".replace("\\n", "\n"), encoding="utf-8")
        with mock.patch.object(Path, "read_bytes", side_effect=PermissionError("blocked")):
            with self.assertRaises(PermissionError):
                mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)

    def test_empty_nonstring_and_traversal_members_are_rejected(self):
        for members in ([], ["alpha", 17], ["alpha", "../outside"], ["alpha", "/etc"]):
            with self.subTest(members=members):
                self.manifest["profiles"]["focused"] = members
                with self.assertRaisesRegex(ValueError, "Invalid profile skill list"):
                    mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)

    def test_symlink_to_skill_and_linked_parent_rejected(self):
        source = self.root / ".agents" / "skills" / "alpha" / "SKILL.md"
        original = source.read_bytes()
        source.unlink()
        target = source.parent / "target.md"
        target.write_bytes(original)
        try:
            source.symlink_to(target)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"File symlinks unavailable in this environment: {exc}")
        with self.assertRaisesRegex(ValueError, "Linked skill source"):
            mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)

    def test_unsafe_manifest_root_outside_checkout_is_rejected(self):
        outside = self.root.parent / ("budget-external-" + self.root.name)
        outside.mkdir()
        self.addCleanup(lambda: shutil.rmtree(outside, ignore_errors=True))
        (outside / "alpha").mkdir()
        (outside / "alpha" / "SKILL.md").write_text(
            "---\\nname: alpha\\ndescription: External\\n---\\n".replace("\\n", "\n"),
            encoding="utf-8",
        )
        self.manifest["extension_packs"] = {
            "override": {"skill_root": str(outside), "skills": ["alpha"]}
        }
        self.manifest["core_skills"] = ["beta"]
        # Prove that invalid paths are refused before calling is_file()
        # on a location outside the requested repository.
        original_is_file = Path.is_file

        def guard_external_stat(path):
            if path.is_relative_to(outside):
                raise AssertionError("Outside-root file inspected")
            return original_is_file(path)

        with mock.patch.object(Path, "is_file", guard_external_stat):
            with self.assertRaisesRegex(ValueError, "escapes Toolkit root"):
                mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)

    def test_repeat_and_content_integrity(self):
        files = list(self.root.rglob("SKILL.md"))
        before = {str(f): f.read_bytes() for f in files}
        first = mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)
        second = mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)
        self.assertEqual(first, second)
        self.assertEqual(before, {str(f): f.read_bytes() for f in files})

    def test_synthetic_cli_end_to_end_no_client(self):
        scripts = self.root / "scripts"
        scripts.mkdir()
        for name in ("profile_metrics.py", "validate_pack.py"):
            shutil.copyfile(ROOT / "scripts" / name, scripts / name)
        (self.root / "MANIFEST.json").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )
        completed = subprocess.run(
            [sys.executable, str(scripts / "profile_metrics.py"),
             "--profile", "focused", "--metadata-budget-bytes", "1000"],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)["metadata_budget_preview"]
        self.assertTrue(result["within_budget"])
        self.assertFalse(result["applied"])
        self.assertEqual("NOT_OBSERVED", result["host_context"])
        self.assertEqual([], list(scripts.rglob("*.pyc")))
        self.assertEqual([], list(scripts.rglob("__pycache__")))

    def test_cli_previews_before_reading_any_source_inventory(self):
        # A rejected preview must not run the broader source-file inventory.
        fake_argv = ["profile_metrics.py", "--profile", "focused",
                     "--metadata-budget-bytes", "1000"]
        (self.root / "MANIFEST.json").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )
        with (mock.patch.object(mod, "ROOT", self.root),
              mock.patch.object(sys, "argv", fake_argv),
              mock.patch.object(mod, "preview_metadata_budget",
                                side_effect=ValueError("unsafe source")),
              mock.patch.object(mod, "measure",
                                side_effect=AssertionError("traversed"))):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(2, mod.main())
            self.assertIn("unsafe source", err.getvalue())



    def test_manifest_profiles_remain_compatible_without_selection_changes(self):
        # Integration: cover the complete declared catalog, not just
        # two synthetic skills or one hand-picked profile.
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["profiles"])
        for name, declared in sorted(manifest["profiles"].items()):
            with self.subTest(profile=name):
                output = mod.preview_metadata_budget(ROOT, manifest, name, 1_000_000)
                self.assertEqual(declared, [
                    row["skill"] for row in output["skill_metadata"]
                ])
                self.assertTrue(output["within_budget"])
                self.assertFalse(output["applied"])
                self.assertFalse(output["automatic_pruning"])
                self.assertEqual("NOT_MEASURED", output["tokens"])
                self.assertEqual(
                    sum(row["metadata_bytes"] for row in output["skill_metadata"]),
                    output["eager_metadata_bytes"]
                )

    def test_linked_skill_folder_is_rejected(self):
        skill = self.root / ".agents" / "skills" / "alpha"
        original = (skill / "SKILL.md").read_bytes()
        shutil.rmtree(skill)
        target = self.root / "linked-skill-target"
        target.mkdir()
        (target / "SKILL.md").write_bytes(original)
        try:
            skill.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Directory symlinks unavailable: {exc}")
        with self.assertRaisesRegex(ValueError, "Linked skill source"):
            mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)

    @unittest.skipUnless(sys.platform == "win32", "Windows junction only")
    def test_windows_junction_skill_folder_is_rejected(self):
        skill = self.root / ".agents" / "skills" / "alpha"
        original = (skill / "SKILL.md").read_bytes()
        shutil.rmtree(skill)
        target = self.root / "junction-target"
        target.mkdir()
        (target / "SKILL.md").write_bytes(original)
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(skill), str(target)],
            capture_output=True, text=True, check=False,
        )
        if completed.returncode:
            self.skipTest(f"Junction creation unavailable: {completed.stderr}")
        self.assertTrue(skill.is_junction())
        with self.assertRaisesRegex(ValueError, "Linked skill source"):
            mod.preview_metadata_budget(self.root, self.manifest, "focused", 1000)


if __name__ == "__main__":
    unittest.main()
