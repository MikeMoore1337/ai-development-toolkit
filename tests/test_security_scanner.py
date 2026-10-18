"""High-confidence publication checks with synthetic local-only fixtures."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("public_package", ROOT / "scripts" / "check_public_package.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SecurityScannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_benign_text(self):
        (self.root / "README.md").write_text("A minimal skill package", encoding="utf-8")
        self.assertEqual([], module.scan(self.root))

    def test_credential_detected_without_leaking_value(self):
        token = "ghp_" + "A" * 36
        (self.root / "sample.txt").write_text("token=" + token, encoding="utf-8")
        findings = module.scan(self.root)
        self.assertTrue(any("github-classic-token" in x for x in findings))
        self.assertNotIn(token, "\n".join(findings))

    def test_private_key_header_detected(self):
        content = "-----BEGIN " + "OPENSSH PRIVATE KEY-----"
        (self.root / "key.txt").write_text(content, encoding="utf-8")
        self.assertTrue(any("private-key-header" in x for x in module.scan(self.root)))

    def test_archive_and_environment_file_blocked(self):
        (self.root / "file.zip").write_bytes(b"PK")
        (self.root / ".env").write_text("PLACEHOLDER", encoding="utf-8")
        (self.root / ".env.example").write_text("PLACEHOLDER", encoding="utf-8")
        result = module.scan(self.root)
        self.assertTrue(any("file.zip" in x for x in result))
        self.assertTrue(any("Environment file" in x for x in result))
        self.assertFalse(any(".env.example" in x for x in result))

    def test_symlink_is_rejected_where_supported(self):
        destination = self.root / "target.txt"
        destination.write_text("safe", encoding="utf-8")
        linked = self.root / "linked.txt"
        try:
            linked.symlink_to(destination)
        except OSError:
            self.skipTest("Creating a symlink requires extra privileges here")
        self.assertTrue(any("Linked file" in x for x in module.scan(self.root)))


if __name__ == "__main__":
    unittest.main()
