"""Offline real-CLI smoke for the Russian first-run guide (#78).

This measures local file behavior only, never comprehension or client activation.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "skill_manager.py"


class RussianFirstRunAcceptance(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="adt-ru-acceptance-")
        self.addCleanup(tmp.cleanup)
        self.demo = Path(tmp.name) / "toolkit-demo"
        self.demo.mkdir()
        (self.demo / "AGENTS.md").write_text("Existing local project policy.\n", encoding="utf-8")
        (self.demo / "CLAUDE.md").write_text("Existing second client policy.\n", encoding="utf-8")

    def run_cli(self, *args: str, success: bool = True):
        result = subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT, text=True, encoding="utf-8",
            capture_output=True, timeout=30, check=False,
        )
        if success:
            self.assertEqual(0, result.returncode,
                             f"{args}: {result.stderr[:400]} {result.stdout[:400]}")
        return result

    def test_first_run_preview_apply_and_status(self):
        self.run_cli("catalog")
        before = {p.relative_to(self.demo).as_posix(): p.read_bytes()
                  for p in self.demo.rglob("*") if p.is_file()}
        self.run_cli("install", "--target", str(self.demo), "--profile", "general")
        after = {p.relative_to(self.demo).as_posix(): p.read_bytes()
                 for p in self.demo.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "Preview must never write files")
        self.run_cli("install", "--target", str(self.demo),
                     "--profile", "general", "--apply")
        self.run_cli("status", "--target", str(self.demo))
        for name, contents in before.items():
            self.assertEqual(contents, (self.demo / name).read_bytes())
        for skill in ("task-scoping", "implementation", "qa-strategy",
                      "code-review", "minimal-safe-change"):
            self.assertTrue((self.demo / ".agents" / "skills" / skill / "SKILL.md").is_file(),
                            f"Expected copied skill: {skill}")
        self.assertTrue((self.demo / ".adt" / "skills-lock.json").is_file())

    def test_unmanaged_skill_is_not_overwritten(self):
        path = self.demo / ".agents" / "skills" / "task-scoping" / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("Private user-owned skill\n", encoding="utf-8")
        result = self.run_cli("install", "--target", str(self.demo),
                              "--profile", "general", "--apply", success=False)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("Private user-owned skill\n", path.read_text(encoding="utf-8"))
        self.assertFalse((self.demo / ".adt" / "skills-lock.json").exists())


if __name__ == "__main__":
    unittest.main()
