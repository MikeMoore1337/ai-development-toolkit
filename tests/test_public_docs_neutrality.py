"""Generic tracked-source neutrality and fail-closed regression tests (#393)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validate_public_docs_neutrality import audit


class PublicSourceNeutralityTests(unittest.TestCase):
    def test_public_upstream_and_current_repository_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "README.md").write_text(
                "OtherOrg/public-agent; example-owner/toolkit; "
                "https://github.com/example-owner/toolkit.git\n"
                "See https://github.com/example-owner/toolkit.\n", encoding="utf-8")
            self.assertEqual([], audit(root, repository="example-owner/toolkit"))

    def test_rejects_other_same_owner_repository_in_code_and_docs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "src").mkdir()
            (root / "src" / "settings.py").write_text(
                'url = "https://github.com/example-owner/private-app"\n',
                encoding="utf-8")
            (root / "README.md").write_text("example-owner/private-app\n", encoding="utf-8")
            findings = audit(root, repository="example-owner/toolkit")
            self.assertEqual(2, len(findings))
            self.assertTrue(all(x["token"] == "FOREIGN_OWNER_REPOSITORY" for x in findings))

    def test_external_private_literals_in_nested_sources_and_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "docs").mkdir()
            (root / "docs" / "notes.md").write_text("CLIENT_PRIVATE_TOKEN\n", encoding="utf-8")
            (root / "private-tag.json").write_text('{}', encoding="utf-8")
            found = audit(root, deny_patterns=("CLIENT_PRIVATE_TOKEN", "private-tag"))
            self.assertEqual(2, len(found))
            self.assertEqual({"PRIVATE_IDENTIFIER", "PRIVATE_NAME_IN_PATH"},
                             {entry["token"] for entry in found})
            self.assertNotIn("CLIENT_PRIVATE_TOKEN", str(found))

    def test_disposable_directories_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".git").mkdir()
            (root / ".git" / "copy.md").write_text("sensitive-marker", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "copy.md").write_text("sensitive-marker", encoding="utf-8")
            findings = audit(root, deny_patterns=("sensitive-marker",))
            self.assertEqual(1, len(findings))
            self.assertEqual("docs/copy.md", findings[0]["file"])

    def test_unrelated_identifier_is_not_a_namespace_match(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "code.py").write_text(
                "prefixexample-owner/another-project\n", encoding="utf-8")
            self.assertEqual([], audit(root, repository="example-owner/toolkit"))

    def test_invalid_utf8_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "bad.md").write_bytes(b"\xff\xfe")
            self.assertEqual("UNREADABLE", audit(root)[0]["token"])

    def test_links_not_followed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "safe.txt").write_text("safe", encoding="utf-8")
            link = root / "linked.txt"
            try:
                link.symlink_to(root / "safe.txt")
            except OSError:
                self.skipTest("symlinks unavailable")
            self.assertTrue(any(x["token"] == "UNSAFE_LINK" for x in audit(root)))


if __name__ == "__main__":
    unittest.main()
