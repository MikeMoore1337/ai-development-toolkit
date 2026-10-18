"""Checksum verification refuses missing, corrupt and unsafe records."""
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


class ChecksumTests(unittest.TestCase):
    def test_real_inventory_matches(self):
        self.assertEqual([], checks.verify(ROOT))

    def test_corruption_and_path_traversal_are_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "file.txt").write_text("ok", encoding="utf-8")
            good = hashlib.sha256(b"ok").hexdigest()
            (root / "SHA256SUMS.txt").write_text(
                f"{good}  file.txt\n{good}  ../outside\n", encoding="utf-8",
            )
            self.assertEqual(1, len(checks.verify(root)))
            (root / "file.txt").write_text("changed", encoding="utf-8")
            self.assertEqual(2, len(checks.verify(root)))

    def test_windows_checkout_line_endings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            canonical = b"alpha\\nbeta\\n"
            (root / "file.txt").write_bytes(b"alpha\\r\\nbeta\\r\\n")
            digest = hashlib.sha256(canonical).hexdigest()
            (root / "SHA256SUMS.txt").write_text(
                f"{digest}  file.txt\\n", encoding="utf-8",
            )
            self.assertEqual([], checks.verify(root))

    def test_duplicate_inventory_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "x").write_bytes(b"x")
            digest = hashlib.sha256(b"x").hexdigest()
            (root / "SHA256SUMS.txt").write_text(
                f"{digest}  x\n{digest}  x\n", encoding="utf-8",
            )
            self.assertTrue(any("duplicate" in e for e in checks.verify(root)))


if __name__ == "__main__":
    unittest.main()
