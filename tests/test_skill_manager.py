"""Skill Manager lifecycle tests use synthetic, isolated projects only."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("skill_manager", ROOT / "scripts" / "skill_manager.py")
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class SkillManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.repo, self.source = base / "project", base / "toolkit"
        self.repo.mkdir()
        self.source.mkdir()
        source = self.source / ".agents" / "skills" / "test-skill"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("# Version one\n", encoding="utf-8")
        (self.source / "MANIFEST.json").write_text(json.dumps({
            "version": "1.0.0",
            "core_skills": ["test-skill"], "extension_skills": [], "extension_packs": {},
            "profiles": {"demo": ["test-skill"]},
        }), encoding="utf-8")
        (self.repo / "AGENTS.md").write_text("Private project rules.\n", encoding="utf-8")
        self.installed = self.repo / ".agents" / "skills" / "test-skill"

    def call(self, action, *, names=None, apply=False, layout="codex"):
        return manager.operate(action, self.repo, names=names, apply=apply,
                               layout=layout, source_root=self.source)

    def test_install_dry_run_is_read_only(self):
        result = self.call("install", names=["test-skill"])
        self.assertFalse(result["applied"])
        self.assertEqual(["test-skill"], result["changes"])
        self.assertFalse((self.repo / ".adt").exists())
        self.assertFalse((self.repo / ".agents").exists())

    def test_install_status_and_idempotent_no_update(self):
        self.assertTrue(self.call("install", names=["test-skill"], apply=True)["applied"])
        self.assertEqual("clean", self.call("status")["skills"]["test-skill"]["status"])
        self.assertEqual([], self.call("update")["changes"])
        self.assertEqual("Private project rules.\n",
                         (self.repo / "AGENTS.md").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(manager.ManagerError, "Existing skill"):
            self.call("install", names=["test-skill"], apply=True)

    def test_unmanaged_existing_folder_not_adopted(self):
        self.installed.mkdir(parents=True)
        (self.installed / "SKILL.md").write_text("# User-owned\n")
        with self.assertRaisesRegex(manager.ManagerError, "Existing skill"):
            self.call("install", names=["test-skill"], apply=True)
        self.assertEqual("# User-owned\n",
                         (self.installed / "SKILL.md").read_text())

    def test_update_dry_run_and_rollback_restores_exact_bytes(self):
        self.call("install", names=["test-skill"], apply=True)
        source = self.source / ".agents" / "skills" / "test-skill" / "SKILL.md"
        source.write_text("# Version two\n", encoding="utf-8")
        self.assertEqual(["test-skill"], self.call("update")["changes"])
        self.assertEqual("# Version one\n",
                         (self.installed / "SKILL.md").read_text())
        self.call("update", apply=True)
        self.assertEqual("# Version two\n",
                         (self.installed / "SKILL.md").read_text())
        self.assertEqual(["test-skill"], self.call("rollback")["changes"])
        self.call("rollback", apply=True)
        self.assertEqual("# Version one\n",
                         (self.installed / "SKILL.md").read_text())
        self.assertEqual("clean", self.call("status")["skills"]["test-skill"]["status"])

    def test_uninstall_only_owned_and_rollback(self):
        with self.assertRaisesRegex(manager.ManagerError, "not owned"):
            self.call("uninstall", names=["test-skill"], apply=True)
        self.call("install", names=["test-skill"], apply=True)
        self.assertFalse(self.call("uninstall", names=["test-skill"])["applied"])
        self.assertTrue(self.installed.exists())
        self.call("uninstall", names=["test-skill"], apply=True)
        self.assertFalse(self.installed.exists())
        self.assertEqual({}, self.call("status")["skills"])
        self.call("rollback", apply=True)
        self.assertTrue(self.installed.exists())

    def test_drift_refuses_update_remove_or_rollback(self):
        self.call("install", names=["test-skill"], apply=True)
        (self.installed / "SKILL.md").write_text("User edits\n", encoding="utf-8")
        self.assertEqual("modified", self.call("status")["skills"]["test-skill"]["status"])
        for action in ("update", "uninstall", "rollback"):
            with self.subTest(action=action):
                with self.assertRaisesRegex(manager.ManagerError, "Local modifications"):
                    self.call(action, names=["test-skill"], apply=True)
        self.assertEqual("User edits\n", (self.installed / "SKILL.md").read_text())

    def test_interrupted_replace_rolls_back_instead_of_losing_skill(self):
        self.call("install", names=["test-skill"], apply=True)
        source = self.source / ".agents" / "skills" / "test-skill" / "SKILL.md"
        source.write_text("# New\n", encoding="utf-8")
        real_replace = manager.os.replace
        failures = [0]
        def fail_staged_once(old, new):
            if "staged" in str(old) and failures[0] == 0:
                failures[0] += 1
                raise OSError("Synthetic rename error")
            return real_replace(old, new)
        with patch.object(manager.os, "replace", side_effect=fail_staged_once):
            with self.assertRaises(OSError):
                self.call("update", apply=True)
        self.assertEqual("# Version one\n",
                         (self.installed / "SKILL.md").read_text())
        self.assertEqual(0, len(manager.pending_transactions(self.repo)))
        self.call("update", apply=True)
        self.assertEqual("# New\n", (self.installed / "SKILL.md").read_text())

    def test_exclusive_lock_rejects_concurrent_writer(self):
        with manager.exclusive(self.repo):
            with self.assertRaisesRegex(manager.ManagerError, "Another"):
                with manager.exclusive(self.repo):
                    pass

    def test_incomplete_lockfile_rejected_without_mutation(self):
        state = self.repo / ".adt" / "skills-lock.json"
        state.parent.mkdir(parents=True)
        state.write_text('{"schema_version":1,"skills":{}}', encoding="utf-8")
        with self.assertRaisesRegex(manager.ManagerError, "layout"):
            self.call("install", names=["test-skill"], apply=True)
        self.assertFalse(self.installed.exists())

    def test_claude_layout_is_supported(self):
        self.call("install", names=["test-skill"], layout="claude", apply=True)
        self.assertTrue((self.repo / ".claude" / "skills" / "test-skill" / "SKILL.md").exists())
        self.assertEqual("claude", self.call("status")["layout"])


if __name__ == "__main__":
    unittest.main()
