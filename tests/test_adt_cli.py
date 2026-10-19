"""Issue #50: beginner CLI is a read-only facade over Skill Manager v2."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import adt  # noqa: E402
import skill_manager as manager  # noqa: E402


def snapshot(root: Path) -> dict:
    """Compare file bytes and directory entries, not merely an applied flag."""
    result = {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if path.is_symlink() or path.is_junction():
            result[name] = ("link", os.readlink(path))
        elif path.is_file():
            result[name] = ("file", hashlib.sha256(path.read_bytes()).hexdigest())
        else:
            result[name] = ("directory",)
    return result


class BeginnerCliTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.target = Path(temp.name) / "target"
        self.target.mkdir()
        (self.target / "AGENTS.md").write_bytes(b"Secret fixture marker: PRIVATE_NEVER_PRINT\n")
        self.manifest = adt.manifest_data()

    def selected(self, profile="general"):
        return adt.choose(self.target, self.manifest, profile, None)

    def invoke(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = adt.main(list(args))
            except SystemExit as exc:
                code = exc.code
        self.assertNotIn("PRIVATE_NEVER_PRINT", out.getvalue() + err.getvalue())
        return code, out.getvalue(), err.getvalue()

    def test_help_profiles_and_invalid_arguments(self):
        self.assertEqual(0, self.invoke("--help")[0])
        code, output, _ = self.invoke("--json", "profile", "list")
        self.assertEqual(0, code)
        self.assertEqual(set(self.manifest["profiles"]), set(json.loads(output)["profiles"]))
        self.assertEqual(2, self.invoke("doctor", "--target", str(self.target),
                                        "--layout", "invalid")[0])
        self.assertEqual(2, self.invoke("init", "--target", str(self.target),
                                        "--profile", "unknown")[0])

    def test_read_only_calls_preserve_entire_project_bytes(self):
        before = snapshot(self.target)
        commands = [
            ("doctor", "--target", str(self.target)),
            ("profile", "list"),
            ("profile", "plan", "--target", str(self.target), "--task", "qa"),
            ("init", "--target", str(self.target), "--profile", "general"),
            ("status", "--target", str(self.target)),
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(0, self.invoke(*command)[0])
                self.assertEqual(before, snapshot(self.target))
                self.assertFalse((self.target / ".adt").exists())

    def test_codex_and_claude_apply_and_repeat_no_duplicates(self):
        for layout in ("codex", "claude"):
            with self.subTest(layout=layout):
                selection = self.selected("research")
                first = adt.preview(self.target, layout, selection, apply=False)
                self.assertEqual("PREVIEW", first["result"])
                self.assertEqual(set(selection["skills"]), set(first["changes"]))
                self.assertTrue(all(diff["change"] == "added"
                                    for changes in first["file_diffs"].values()
                                    for diff in changes))
                applied = adt.preview(self.target, layout, selection, apply=True)
                self.assertEqual("APPLIED", applied["result"])
                self.assertTrue(applied["applied"])
                self.assertTrue(all(row["status"] == "clean"
                                    for row in applied["verification"]["skills"].values()))
                stable = snapshot(self.target)
                repeated = adt.preview(self.target, layout, selection, apply=True)
                self.assertEqual("ALREADY_INSTALLED", repeated["result"])
                self.assertFalse(repeated["applied"])
                self.assertEqual(stable, snapshot(self.target))
        self.assertEqual(set(selection["skills"]), set(manager.read_state(self.target, "codex")["skills"]))
        self.assertEqual(set(selection["skills"]), set(manager.read_state(self.target, "claude")["skills"]))

    def test_partial_install_only_adds_missing_skills(self):
        selection = self.selected("general")
        manager.operate("install", self.target, names=[selection["skills"][0]], apply=True)
        report = adt.preview(self.target, "codex", selection, apply=False)
        self.assertEqual([selection["skills"][0]], report["already_managed"])
        self.assertEqual(len(selection["skills"]) - 1, len(report["changes"]))
        self.assertTrue(adt.preview(self.target, "codex", selection, apply=True)["applied"])

    def test_missing_target_is_blocked_without_creation(self):
        absent = self.target / "not-created"
        result = adt.diagnose(absent, "codex", self.selected())
        self.assertEqual("BLOCKED", result["result"])
        self.assertEqual("FAIL", result["checks"]["project"])
        code, _, _ = self.invoke("init", "--target", str(absent), "--apply")
        self.assertEqual(2, code)
        self.assertFalse(absent.exists())

    def test_unmanaged_collision_preserves_user_content(self):
        name = self.selected()["skills"][0]
        foreign = self.target / ".agents" / "skills" / name
        foreign.mkdir(parents=True)
        (foreign / "SKILL.md").write_bytes(b"PRIVATE_NEVER_PRINT\n")
        before = snapshot(self.target)
        report = adt.preview(self.target, "codex", self.selected(), apply=False)
        self.assertEqual("BLOCKED", report["result"])
        self.assertEqual([name], report["doctor"]["conflicts"])
        self.assertEqual(before, snapshot(self.target))
        self.assertEqual(2, self.invoke("init", "--target", str(self.target),
                                        "--profile", "general", "--apply")[0])
        self.assertEqual(before, snapshot(self.target))

    def test_unrelated_unmanaged_is_review_required_not_adopted(self):
        foreign = self.target / ".agents" / "skills" / "private-skill"
        foreign.mkdir(parents=True)
        (foreign / "SKILL.md").write_bytes(b"PRIVATE_NEVER_PRINT\n")
        result = adt.preview(self.target, "codex", self.selected("research"), apply=False)
        self.assertEqual("REVIEW_REQUIRED", result["result"])
        self.assertIn("private-skill", result["doctor"]["unmanaged"])
        self.assertFalse(result["applied"])

    def test_corrupted_lock_is_blocked_and_read_only(self):
        folder = self.target / ".adt"
        folder.mkdir()
        (folder / "skills-lock.json").write_text("{ invalid json", encoding="utf-8")
        before = snapshot(self.target)
        report = adt.diagnose(self.target, "codex")
        self.assertEqual("FAIL", report["checks"]["manager_state"])
        self.assertEqual("BLOCKED", report["result"])
        self.assertEqual(before, snapshot(self.target))

    def test_drift_detected_without_change(self):
        adt.preview(self.target, "codex", self.selected("research"), apply=True)
        skill = self.target / ".agents" / "skills" / "task-scoping" / "SKILL.md"
        skill.write_bytes(skill.read_bytes() + b"\nPRIVATE_NEVER_PRINT")
        before = snapshot(self.target)
        report = adt.preview(self.target, "codex", self.selected("research"), apply=True)
        self.assertEqual("BLOCKED", report["result"])
        self.assertEqual("FAIL", report["doctor"]["checks"]["managed_drift"])
        self.assertEqual(before, snapshot(self.target))

    def test_pending_and_partial_transaction_block(self):
        for kind in ("pending", "orphan"):
            with self.subTest(kind=kind):
                with tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp)
                    folder = target / ".adt" / "history" / ("f" * 32)
                    folder.mkdir(parents=True)
                    if kind == "pending":
                        (folder / "meta.json").write_text('{"status":"pending"}', encoding="utf-8")
                    else:
                        (folder / "staged").mkdir()
                    before = snapshot(target)
                    report = adt.diagnose(target, "codex")
                    self.assertEqual("BLOCKED", report["result"])
                    self.assertEqual("FAIL", report["checks"]["transactions"])
                    self.assertEqual(before, snapshot(target))

    @unittest.skipUnless(hasattr(os, "symlink"), "Symlinks unavailable")
    def test_symlinked_skill_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            root = self.target / ".agents"
            root.mkdir()
            try:
                (root / "skills").symlink_to(Path(elsewhere), target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink privileges unavailable")
            before = snapshot(self.target)
            self.assertEqual("BLOCKED", adt.diagnose(self.target, "codex")["result"])
            self.assertEqual(before, snapshot(self.target))

    def test_concurrent_writer_cannot_be_bypassed(self):
        selected = self.selected("research")
        with manager.exclusive(self.target):
            before = snapshot(self.target)
            with self.assertRaisesRegex(manager.ManagerError, "Another"):
                adt.preview(self.target, "codex", selected, apply=True)
            self.assertEqual(before, snapshot(self.target))

    def test_doctor_python_and_write_access_are_not_overclaimed(self):
        result = adt.diagnose(self.target, "codex")
        self.assertEqual("NOT_VERIFIED", result["client_activation"])
        self.assertIn(result["checks"]["write_access"], ("NOT_VERIFIED", "UNKNOWN"))
        self.assertEqual("NOT_INSTALLED", result["checks"]["lockfile"])
        self.assertEqual("OK", result["result"])

    def test_profile_task_does_not_install_automatically(self):
        (self.target / "pyproject.toml").touch()
        (self.target / "package.json").touch()
        selection = adt.choose(self.target, self.manifest, None, "qa")
        self.assertEqual("qa-python", selection["profile"])
        self.assertEqual("NOT_VERIFIED", selection["detected"]["pytest_installed"])
        self.assertIn("qa-core", selection["alternatives"])
        before = snapshot(self.target)
        result = adt.preview(self.target, "codex", selection, apply=False)
        self.assertFalse(result["applied"])
        self.assertEqual(before, snapshot(self.target))


if __name__ == "__main__":
    unittest.main()
