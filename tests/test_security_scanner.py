"""Synthetic regression fixtures for the offline publication scanner."""
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "public_package", ROOT / "scripts" / "check_public_package.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SecurityScannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, filename: str, data: str | bytes) -> None:
        path = self.root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(data, encoding="utf-8")

    def check_rule(self, filename: str, content: str | bytes, rule: str) -> None:
        self.put(filename, content)
        findings = module.scan(self.root)
        self.assertTrue(any(rule in finding for finding in findings), findings)
        if isinstance(content, str):
            self.assertNotIn(content, "\n".join(findings))

    def test_safe_text_and_example_env(self):
        self.put("sample.py", "print('example')\n")
        self.put("README.md", "# Public documentation\n")
        self.put(".env.example", "TOKEN=your-token-here\n")
        self.put("settings.yaml", "mode: development\n")
        self.assertEqual([], module.scan(self.root))

    def test_current_public_package(self):
        self.assertEqual([], module.scan(ROOT))

    def test_github_tokens_are_redacted(self):
        self.check_rule("sample.txt", "ghp_" + "A" * 36, "github-classic-token")
        self.check_rule("fine.txt", "github_pat_" + "B" * 82,
                        "github-fine-grained-token")

    def test_private_key_and_aws_and_openai(self):
        self.check_rule("key.txt", "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
                        "private-key-header")
        self.check_rule("aws.txt", "AKIA" + "A" * 16, "aws-access-key")
        self.check_rule("temporary.txt", "ASIA" + "C" * 16, "aws-access-key")
        self.check_rule("openai.txt", "sk-proj-" + "D" * 30, "openai-project-key")

    def test_secrets_in_allowed_document_and_env_template(self):
        self.check_rule(".env.example", "ghp_" + "E" * 36, "github-classic-token")
        self.check_rule("README.md", "sk-proj-" + "F" * 30, "openai-project-key")

    def test_line_number_and_no_value_in_report(self):
        secret = "ghp_" + "G" * 36
        self.put("docs/note.md", "safe line\n" + secret + "\n")
        result = module.scan(self.root)
        self.assertTrue(any("docs/note.md:2 / github-classic-token" in x
                            for x in result))
        self.assertNotIn(secret, "\n".join(result))

    def test_environment_archive_and_credentials_blocked(self):
        self.put("file.zip", b"PK")
        self.put(".env", "PLACEHOLDER")
        self.put(".env.production", "PLACEHOLDER")
        self.put(".npmrc", "// registry example")
        self.put("credentials.json", "{}")
        found = "\n".join(module.scan(self.root))
        for name in ("file.zip", ".env", ".env.production", ".npmrc",
                     "credentials.json"):
            self.assertIn(name, found)

    def test_unexpected_binary_invalid_utf8_and_oversize(self):
        self.check_rule("artifact.dat", b"\x00\x01", "Unexpected binary")
        self.check_rule("artifact.txt", b"\xff\xfe", "Unexpected binary")
        self.check_rule("huge.txt", b"A" * (module.MAX_TEXT_BYTES + 1),
                        "Oversized unreviewed")

    def test_corrupted_or_unreadable_file_fails_closed_without_error_detail(self):
        self.put("unreadable.txt", "public sample")
        with mock.patch.object(Path, "read_bytes", side_effect=OSError("SECRET_ERROR")):
            result = module.scan(self.root)
        self.assertTrue(any("Unreadable file: unreadable.txt" in x for x in result))
        self.assertNotIn("SECRET_ERROR", "\n".join(result))

    def test_symlink_outside_root_never_read(self):
        with tempfile.TemporaryDirectory() as external:
            sentinel = "ghp_" + "S" * 36
            target = Path(external) / "outside.txt"
            target.write_text(sentinel, encoding="utf-8")
            link = self.root / "outside-link.txt"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("Symlink requires privileges")
            found = "\n".join(module.scan(self.root))
            self.assertIn("Linked file: outside-link.txt", found)
            self.assertNotIn(sentinel, found)

    def test_symlink_directory_never_traversed(self):
        with tempfile.TemporaryDirectory() as external:
            target = Path(external) / "outside.txt"
            target.write_text("not public", encoding="utf-8")
            link = self.root / "external"
            try:
                link.symlink_to(Path(external), target_is_directory=True)
            except OSError:
                self.skipTest("Directory symlink requires privileges")
            self.assertIn("Linked directory: external", module.scan(self.root))

    def test_tracked_and_untracked_files_are_scanned(self):
        try:
            subprocess.run(["git", "init", "-q", str(self.root)],
                           check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("Git unavailable")
        self.put("tracked.txt", "ghp_" + "T" * 36)
        subprocess.run(["git", "-C", str(self.root), "add", "tracked.txt"],
                       check=True, capture_output=True)
        self.put("untracked.txt", "sk-proj-" + "U" * 30)
        result = "\n".join(module.scan(self.root))
        self.assertIn("tracked.txt", result)
        self.assertIn("untracked.txt", result)

    def test_scripts_are_read_only_and_cannot_execute_payload(self):
        self.put("sample.py", "raise RuntimeError('must not execute')\n")
        self.assertEqual([], module.scan(self.root))

    def test_local_cache_does_not_get_read(self):
        self.put(".venv/config.txt", "ghp_" + "V" * 36)
        self.put(".git/config", "ghp_" + "W" * 36)
        self.put("visible.txt", "safe")
        self.assertEqual([], module.scan(self.root))


if __name__ == "__main__":
    unittest.main()
