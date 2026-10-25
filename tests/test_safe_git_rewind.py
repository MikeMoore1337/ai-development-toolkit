"""No-network, no-AI tests of the explicitly guarded Git rewind adapter."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

FILE = Path(__file__).resolve().parents[1] / "scripts" / "safe_git_rewind.py"
SPEC = importlib.util.spec_from_file_location("safe_git_rewind", FILE)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def run(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True)
    return p.stdout.strip()


class SafeGitRewindTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        run(self.root, "init", "-q")
        (self.root / "a.txt").write_text("old\n")
        run(self.root, "add", "a.txt")
        run(self.root, "-c", "user.name=Test", "-c", "user.email=t@example.test", "commit", "-qm", "one")
        self.old = run(self.root, "rev-parse", "HEAD")
        (self.root / "a.txt").write_text("new\n")
        run(self.root, "add", "a.txt")
        run(self.root, "-c", "user.name=Test", "-c", "user.email=t@example.test", "commit", "-qm", "two")
        self.head = run(self.root, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def cli(self, *args: str) -> tuple[int, str, str]:
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = MOD.main(["--repo", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def test_preview_is_read_only(self) -> None:
        rc, out, _ = self.cli("preview", "--commit", self.old, "--file", "a.txt")
        self.assertEqual(rc, 0)
        self.assertIn("RESTORE=NOT_RUN", out)
        self.assertEqual((self.root / "a.txt").read_text(), "new\n")

    def test_explicit_selective_restore_without_index_change(self) -> None:
        rc, _, _ = self.cli("apply", "--commit", self.old, "--file", "a.txt", "--expect-head", self.head, "--confirm")
        self.assertEqual(rc, 0)
        self.assertEqual((self.root / "a.txt").read_text(), "old\n")
        self.assertEqual(run(self.root, "rev-parse", "HEAD"), self.head)
        self.assertEqual(run(self.root, "show", ":a.txt"), "new")

    def test_no_implicit_write(self) -> None:
        rc, _, err = self.cli("apply", "--commit", self.old, "--file", "a.txt", "--expect-head", self.head)
        self.assertEqual(rc, 2)
        self.assertIn("--confirm", err)

    def test_dirty_worktree_refused(self) -> None:
        (self.root / "a.txt").write_text("manual\n")
        rc, _, err = self.cli("apply", "--commit", self.old, "--file", "a.txt", "--expect-head", self.head, "--confirm")
        self.assertEqual(rc, 2)
        self.assertIn("modification", err)
        self.assertEqual((self.root / "a.txt").read_text(), "manual\n")

    def test_dirty_index_refused(self) -> None:
        (self.root / "a.txt").write_text("stage\n")
        run(self.root, "add", "a.txt")
        rc, _, _ = self.cli("apply", "--commit", self.old, "--file", "a.txt", "--expect-head", self.head, "--confirm")
        self.assertEqual(rc, 2)

    def test_invalid_paths_refused(self) -> None:
        for name in ("../a.txt", "./a.txt", "/tmp/a.txt", ".git/config", "a.txt/..", "C:/a.txt", "a\\b"):
            with self.subTest(path=name):
                rc, _, _ = self.cli("preview", "--commit", self.old, "--file", name)
                self.assertEqual(rc, 2)

    def test_unknown_or_untracked_file_refused(self) -> None:
        (self.root / "b.txt").write_text("personal")
        rc, _, _ = self.cli("apply", "--commit", self.old, "--file", "b.txt", "--expect-head", self.head, "--confirm")
        self.assertEqual(rc, 2)
        self.assertEqual((self.root / "b.txt").read_text(), "personal")

    def test_stale_head_refused(self) -> None:
        rc, _, err = self.cli("apply", "--commit", self.old, "--file", "a.txt", "--expect-head", self.old, "--confirm")
        self.assertEqual(rc, 2)
        self.assertIn("HEAD moved", err)

    def test_symlink_file_refused(self) -> None:
        link = self.root / "link.txt"
        try:
            link.symlink_to("a.txt")
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation not available")
        rc, _, _ = self.cli("preview", "--commit", self.old, "--file", "link.txt")
        self.assertEqual(rc, 2)

    def test_commit_must_be_full_sha(self) -> None:
        rc, _, _ = self.cli("preview", "--commit", self.old[:12], "--file", "a.txt")
        self.assertEqual(rc, 2)

    def test_git_timeline(self) -> None:
        rc, out, _ = self.cli("timeline", "--count", "2")
        self.assertEqual(rc, 0)
        self.assertIn(self.head, out)
        self.assertIn(self.old, out)

    def test_refuse_nonroot(self) -> None:
        (self.root / "nested").mkdir()
        rc, _, err = self.cli("preview", "--commit", self.old, "--file", "a.txt", "--file", "nested")
        self.assertEqual(rc, 2)
        self.assertIn("regular", err)


if __name__ == "__main__":
    unittest.main()
