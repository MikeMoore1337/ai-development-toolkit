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

    def test_file_diff_preview_has_added_modified_and_deleted_paths(self):
        installation = self.call("install", names=["test-skill"])
        self.assertEqual("added", installation["file_diffs"]["test-skill"][0]["change"])
        self.assertFalse((self.repo / ".adt").exists())
        self.call("install", names=["test-skill"], apply=True)
        source = self.source / ".agents" / "skills" / "test-skill" / "SKILL.md"
        source.write_text("# Changed content\n", encoding="utf-8")
        preview = self.call("update")
        details = preview["file_diffs"]["test-skill"]
        self.assertEqual(["SKILL.md"], [d["path"] for d in details])
        self.assertEqual("modified", details[0]["change"])
        self.assertNotEqual(details[0]["before_sha256"], details[0]["after_sha256"])
        self.assertEqual("# Version one\n",
                         (self.installed / "SKILL.md").read_text(encoding="utf-8"))
        removal = self.call("uninstall", names=["test-skill"])
        self.assertEqual("deleted", removal["file_diffs"]["test-skill"][0]["change"])

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

    def test_install_rollback_removes_only_owned_skill(self):
        self.call("install", names=["test-skill"], apply=True)
        self.call("rollback", apply=True)
        self.assertFalse(self.installed.exists())
        self.assertEqual("Private project rules.\n",
                         (self.repo / "AGENTS.md").read_text(encoding="utf-8"))
        self.call("rollback", apply=True)
        self.assertTrue(self.installed.exists())

    def test_explicit_recovery_of_interrupted_move(self):
        self.call("install", names=["test-skill"], apply=True)
        before = manager.read_state(self.repo)
        tid = "c" * 32
        base = self.repo / ".adt" / "history" / tid
        (base / "old").mkdir(parents=True)
        after = json.loads(json.dumps(before))
        after["last_transaction"] = tid
        manager.atomic_json(base / "meta.json", {
            "status": "pending", "before": before,
            "after": after, "changes": ["test-skill"],
        })
        manager.os.replace(self.installed, base / "old" / "test-skill")
        with self.assertRaisesRegex(manager.ManagerError, "Interrupted"):
            self.call("status")
        self.assertEqual(1, self.call("recover")["pending"])
        self.assertEqual(1, self.call("recover", apply=True)["recovered"])
        self.assertTrue(self.installed.exists())
        self.assertEqual("clean", self.call("status")["skills"]["test-skill"]["status"])

    def test_recover_orphaned_staging_without_touching_skills(self):
        base = self.repo / ".adt" / "history" / ("e" * 32)
        (base / "staged" / "test-skill").mkdir(parents=True)
        (base / "staged" / "test-skill" / "SKILL.md").write_text(
            "# Staged but not applied\n", encoding="utf-8",
        )
        with self.assertRaisesRegex(manager.ManagerError, "Interrupted"):
            self.call("status")
        self.assertEqual(1, self.call("recover")["orphan_staging"])
        result = self.call("recover", apply=True)
        self.assertEqual(1, result["discarded_incomplete_staging"])
        self.assertFalse(base.exists())
        self.assertEqual("Private project rules.\n",
                         (self.repo / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertEqual({}, self.call("status")["skills"])

    def test_manifest_source_traversal_refused(self):
        extension = self.source / "external"
        extension.mkdir()
        outside = extension.parent.parent / "untrusted"
        outside.mkdir()
        (outside / "SKILL.md").write_text("# unsafe\n", encoding="utf-8")
        config = json.loads((self.source / "MANIFEST.json").read_text(encoding="utf-8"))
        config["extension_packs"] = {
            "unsafe": {"skill_root": "../../untrusted", "skills": ["bad-skill"]}
        }
        (self.source / "MANIFEST.json").write_text(json.dumps(config), encoding="utf-8")
        with self.assertRaisesRegex(manager.ManagerError, "escapes toolkit"):
            self.call("install", names=["bad-skill"], apply=True)

    def test_claude_layout_is_supported(self):
        self.call("install", names=["test-skill"], layout="claude", apply=True)
        self.assertTrue((self.repo / ".claude" / "skills" / "test-skill" / "SKILL.md").exists())
        self.assertEqual("claude", self.call("status", layout="claude")["layout"])
        self.assertEqual({}, self.call("status")["skills"])

    def test_dual_client_migration_preserves_both_independent_installs(self):
        (self.repo / "CLAUDE.md").write_bytes(b"Private Claude rules\r\n")
        self.call("install", names=["test-skill"], apply=True)
        first_lock = (self.repo / ".adt" / "skills-lock.json").read_bytes()
        preview = manager.operate("migrate", self.repo, layout="claude",
                                  from_layout="codex", source_root=self.source)
        self.assertFalse(preview["applied"])
        self.assertEqual(["test-skill"], preview["changes"])
        self.assertFalse((self.repo / ".claude").exists())
        self.assertFalse((self.repo / ".adt" / "skills-lock-claude.json").exists())
        result = manager.operate("migrate", self.repo, layout="claude",
                                 from_layout="codex", source_root=self.source, apply=True)
        self.assertTrue(result["applied"])
        other = self.repo / ".claude" / "skills" / "test-skill"
        self.assertEqual(self.installed.joinpath("SKILL.md").read_bytes(),
                         other.joinpath("SKILL.md").read_bytes())
        self.assertEqual(first_lock, (self.repo / ".adt" / "skills-lock.json").read_bytes())
        self.assertEqual(b"Private Claude rules\r\n",
                         (self.repo / "CLAUDE.md").read_bytes())
        self.assertEqual("clean", self.call("status")["skills"]["test-skill"]["status"])
        self.assertEqual("clean", self.call("status", layout="claude")
                         ["skills"]["test-skill"]["status"])
        self.call("uninstall", names=["test-skill"], layout="claude", apply=True)
        self.assertTrue(self.installed.exists())
        self.assertFalse(other.exists())
        self.call("rollback", layout="claude", apply=True)
        self.assertTrue(other.exists())
        self.assertEqual(first_lock, (self.repo / ".adt" / "skills-lock.json").read_bytes())

    def test_claude_first_uses_legacy_lock_and_codex_uses_secondary(self):
        self.call("install", names=["test-skill"], layout="claude", apply=True)
        first_lock = (self.repo / ".adt" / "skills-lock.json").read_bytes()
        self.call("install", names=["test-skill"], layout="codex", apply=True)
        self.assertEqual(first_lock, (self.repo / ".adt" / "skills-lock.json").read_bytes())
        self.assertEqual("codex", manager.read_state(self.repo, "codex")["layout"])
        self.assertEqual("claude", manager.read_state(self.repo, "claude")["layout"])
        self.assertTrue((self.repo / ".adt" / "skills-lock-codex.json").is_file())

    def test_migrate_is_idempotent_via_update_not_silent_reinstall(self):
        self.call("install", names=["test-skill"], apply=True)
        manager.operate("migrate", self.repo, layout="claude",
                        from_layout="codex", apply=True, source_root=self.source)
        with self.assertRaisesRegex(manager.ManagerError, "Existing skill"):
            manager.operate("migrate", self.repo, layout="claude",
                            from_layout="codex", apply=True, source_root=self.source)
        self.assertEqual([], self.call("update", layout="claude")["changes"])
        self.assertEqual("clean", self.call("status")["skills"]["test-skill"]["status"])

    def test_migrate_refuses_modified_source_or_changed_toolkit_version(self):
        self.call("install", names=["test-skill"], apply=True)
        self.installed.joinpath("SKILL.md").write_text("user changed", encoding="utf-8")
        with self.assertRaisesRegex(manager.ManagerError, "Local modifications"):
            manager.operate("migrate", self.repo, layout="claude",
                            from_layout="codex", source_root=self.source, apply=True)
        self.assertFalse((self.repo / ".claude").exists())
        self.installed.joinpath("SKILL.md").write_text("# Version one\n", encoding="utf-8")
        self.source.joinpath(".agents/skills/test-skill/SKILL.md").write_text(
            "# Different upstream\n", encoding="utf-8")
        with self.assertRaisesRegex(manager.ManagerError, "non-identical migration"):
            manager.operate("migrate", self.repo, layout="claude",
                            from_layout="codex", source_root=self.source, apply=True)
        self.assertFalse((self.repo / ".claude").exists())

    def test_migrate_refuses_collision_with_unmanaged_claude_skill(self):
        self.call("install", names=["test-skill"], apply=True)
        unmanaged = self.repo / ".claude" / "skills" / "test-skill"
        unmanaged.mkdir(parents=True)
        unmanaged.joinpath("SKILL.md").write_text("# user-owned\n", encoding="utf-8")
        with self.assertRaisesRegex(manager.ManagerError, "Existing skill"):
            manager.operate("migrate", self.repo, layout="claude",
                            from_layout="codex", source_root=self.source, apply=True)
        self.assertEqual("# user-owned\n", unmanaged.joinpath("SKILL.md").read_text())
        self.assertTrue(self.installed.exists())

    def test_separate_state_corruption_and_dangling_links_fail_closed(self):
        self.call("install", names=["test-skill"], apply=True)
        other = self.repo / ".adt" / "skills-lock-claude.json"
        other.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(manager.ManagerError, "Unable to read lockfile"):
            self.call("install", names=["test-skill"], layout="claude", apply=True)
        self.assertTrue(self.installed.exists())
        other.unlink()
        collision = self.repo / ".claude" / "skills" / "test-skill"
        collision.parent.mkdir(parents=True)
        try:
            collision.symlink_to(self.repo / "missing", target_is_directory=True)
        except OSError:
            self.skipTest("Platform disallows creating symlinks")
        with self.assertRaisesRegex(manager.ManagerError, "Existing skill"):
            self.call("install", names=["test-skill"], layout="claude", apply=True)

    def test_deleted_primary_lock_does_not_reassign_secondary(self):
        self.call("install", names=["test-skill"], apply=True)
        self.call("install", names=["test-skill"], layout="claude", apply=True)
        (self.repo / ".adt" / "skills-lock.json").unlink()
        with self.assertRaisesRegex(manager.ManagerError, "Primary manager lockfile missing"):
            self.call("status", layout="claude")
        self.assertTrue(self.installed.exists())

    def test_migration_interruption_recovers_without_affecting_source(self):
        self.call("install", names=["test-skill"], apply=True)
        first_lock = (self.repo / ".adt" / "skills-lock.json").read_bytes()
        real_replace = manager.os.replace
        def fail_destination_once(old, new):
            if "staged" in str(old) and ".claude" in str(new):
                raise OSError("synthetic migrate failure")
            return real_replace(old, new)
        with patch.object(manager.os, "replace", side_effect=fail_destination_once):
            with self.assertRaises(OSError):
                manager.operate("migrate", self.repo, layout="claude",
                                from_layout="codex", source_root=self.source, apply=True)
        self.assertEqual(first_lock, (self.repo / ".adt" / "skills-lock.json").read_bytes())
        self.assertEqual("clean", self.call("status")["skills"]["test-skill"]["status"])
        self.assertEqual({}, self.call("status", layout="claude")["skills"])
        self.assertEqual(0, len(manager.pending_transactions(self.repo)))

    def test_concurrent_identical_unmanaged_destination_is_never_deleted(self):
        self.call("install", names=["test-skill"], apply=True)
        original_lock = (self.repo / ".adt" / "skills-lock.json").read_bytes()
        other = self.repo / ".claude" / "skills" / "test-skill"
        real_write = manager.atomic_json
        injected = [False]

        def collide_after_pending_metadata(path, payload):
            real_write(path, payload)
            if (path.name == "meta.json" and payload.get("status") == "pending"
                    and not injected[0]):
                injected[0] = True
                other.parent.mkdir(parents=True, exist_ok=True)
                manager.shutil.copytree(
                    self.source / ".agents" / "skills" / "test-skill", other)

        with patch.object(manager, "atomic_json", side_effect=collide_after_pending_metadata):
            with self.assertRaisesRegex(manager.ManagerError, "manual recovery"):
                manager.operate("migrate", self.repo, layout="claude",
                                from_layout="codex", source_root=self.source, apply=True)
        self.assertTrue(injected[0])
        self.assertEqual("# Version one\n", (other / "SKILL.md").read_text())
        self.assertEqual("# Version one\n", (self.installed / "SKILL.md").read_text())
        self.assertEqual(original_lock, (self.repo / ".adt" / "skills-lock.json").read_bytes())
        self.assertEqual(1, len(manager.pending_transactions(self.repo)))

    def test_catalog_and_migrate_cli_errors_are_read_only(self):
        import subprocess
        cmd = [sys.executable, str(ROOT / "scripts" / "skill_manager.py")]
        profile = subprocess.run(cmd + ["catalog", "--profile", "qa-python"],
                                 capture_output=True, text=True)
        self.assertEqual(0, profile.returncode, profile.stderr)
        self.assertIn("pytest-test-design", json.loads(profile.stdout)["skills"])
        missing = subprocess.run(cmd + ["catalog", "--profile", "nonexistent"],
                                 capture_output=True, text=True)
        self.assertEqual(2, missing.returncode)
        no_target = subprocess.run(cmd + ["status"], capture_output=True, text=True)
        self.assertEqual(2, no_target.returncode)
        bad_migrate = subprocess.run(cmd + ["migrate", "--target", str(self.repo),
                                           "--layout", "claude", "--from-layout", "claude"],
                                     capture_output=True, text=True)
        self.assertEqual(2, bad_migrate.returncode)
        self.assertFalse((self.repo / ".adt").exists())


if __name__ == "__main__":
    unittest.main()
