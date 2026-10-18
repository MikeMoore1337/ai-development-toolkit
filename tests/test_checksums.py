"""Checksum verification rejects missing, extra, unsafe, corrupt and untracked records."""
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("checksum_verifier", ROOT / "scripts" / "verify_checksums.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def record(root: Path, name: str, data: bytes) -> None:
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_bytes(data)
    (root / "SHA256SUMS.txt").write_text(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n", encoding="utf-8",
    )


class ChecksumTests(unittest.TestCase):
    def test_real_inventory_matches_and_is_complete(self):
        self.assertEqual([], checks.verify(ROOT))

    def test_corruption_and_path_traversal_are_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record(root, "file.txt", b"ok")
            good = hashlib.sha256(b"ok").hexdigest()
            with (root / "SHA256SUMS.txt").open("a", encoding="utf-8") as handle:
                handle.write(f"{good}  ../outside\n")
            self.assertEqual(1, len(checks.verify(root, tracked_paths={"file.txt"})))
            (root / "file.txt").write_text("changed", encoding="utf-8")
            self.assertEqual(2, len(checks.verify(root, tracked_paths={"file.txt"})))

    def test_windows_checkout_line_endings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            canonical = b"alpha\nbeta\n"
            record(root, "file.txt", canonical)
            (root / "file.txt").write_bytes(b"alpha\r\nbeta\r\n")
            self.assertEqual([], checks.verify(root, tracked_paths={"file.txt"}))

    def test_binary_looking_bytes_not_normalized(self):
        data = b"\x01alpha\r\nbeta\r\n"
        self.assertEqual(data, checks.canonical_bytes(data))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record(root, "bytes.bin", data)
            self.assertEqual([], checks.verify(root, tracked_paths={"bytes.bin"}))

    def test_duplicate_inventory_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record(root, "x", b"x")
            with (root / "SHA256SUMS.txt").open("a", encoding="utf-8") as handle:
                handle.write(f"{hashlib.sha256(b'x').hexdigest()}  x\n")
            self.assertTrue(any("duplicate" in e for e in
                                checks.verify(root, tracked_paths={"x"})))

    def test_new_tracked_file_requires_checksum(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record(root, "existing.md", b"hello")
            (root / "new.md").write_bytes(b"new")
            issues = checks.verify(root, tracked_paths={"existing.md", "new.md"})
            self.assertIn("missing checksum entry: new.md", issues)

    def test_extra_untracked_entry_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record(root, "untracked.md", b"hello")
            issues = checks.verify(root, tracked_paths={"tracked.md"})
            self.assertTrue(any("untracked or unexpected" in error for error in issues))
            self.assertIn("missing checksum entry: tracked.md", issues)

    def test_archive_mode_includes_unlisted_unicode_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record(root, "docs/описание.md", b"hello")
            self.assertEqual([], checks.verify(root, archive=True))
            (root / "new.txt").write_bytes(b"oops")
            self.assertIn("missing checksum entry: new.txt", checks.verify(root, archive=True))

    def test_archive_mode_requires_clean_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record(root, "file.md", b"hello")
            (root / ".git").mkdir()
            self.assertTrue(any("extracted archive" in e for e in
                                checks.verify(root, archive=True)))

    def test_symlink_record_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record(root, "safe.txt", b"hello")
            link = root / "linked.txt"
            try:
                link.symlink_to(root / "safe.txt")
            except OSError:
                self.skipTest("Symlink creation not permitted")
            h = hashlib.sha256(b"hello").hexdigest()
            with (root / "SHA256SUMS.txt").open("a", encoding="utf-8") as fh:
                fh.write(f"{h}  linked.txt\n")
            self.assertTrue(any("unsafe path" in e for e in
                                checks.verify(root, tracked_paths={"safe.txt", "linked.txt"})))

    def test_default_requires_actual_git_worktree(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record(root, "test.txt", b"data")
            issues = checks.verify(root)
            self.assertTrue(any("Git repository root" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
