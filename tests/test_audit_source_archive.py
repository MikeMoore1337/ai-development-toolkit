"""ZIP audit: path, confidentiality, binary and execution boundaries."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import zipfile
import stat
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_source_archive as audit


class ArchiveAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "bundle.zip"

    def make(self, entries):
        with zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name, body in entries:
                z.writestr(name, body)

    def check(self, **kwargs):
        return audit.audit_zip(self.path, repository="sample-owner/toolkit", **kwargs)

    def test_source_text_six_formats_and_own_repo_are_accepted(self):
        self.make([
            ("README.md", "sample-owner/toolkit.git"),
            ("module.py", "a=1"),
            ("settings.json", '{"status":"ok"}'),
            ("settings.yaml", "status: ok"),
            ("fixtures.csv", "a,b\n1,2"),
            ("image.svg", "<svg/>"),
        ])
        before = self.path.read_bytes()
        result = self.check()
        self.assertEqual("PASS", result["status"], result["findings"])
        self.assertEqual(6, result["text_members_scanned"])
        self.assertEqual(0, result["opaque_members_uninspected"])
        self.assertEqual(before, self.path.read_bytes())

    def test_private_references_in_all_source_types_fail(self):
        names = ("a.md", "b.py", "c.json", "d.yaml", "e.csv", "f.svg")
        self.make([(name, "sample-owner/private-project") for name in names])
        result = self.check()
        self.assertEqual(6, len(result["findings"]))
        self.assertEqual({"FOREIGN_OWNER_REPOSITORY"},
                         {x["token"] for x in result["findings"]})

    def test_private_literal_and_filename_redacted(self):
        self.make([("personal-secret.txt", "LOCAL_SECRET_PATTERN")])
        result = self.check(deny_patterns=("personal-secret", "LOCAL_SECRET_PATTERN"))
        self.assertEqual("FAIL", result["status"])
        self.assertNotIn("personal-secret", json.dumps(result))
        self.assertNotIn("LOCAL_SECRET_PATTERN", json.dumps(result))
        self.assertEqual({"PRIVATE_IDENTIFIER_IN_PATH", "PRIVATE_IDENTIFIER"},
                         {x["token"] for x in result["findings"]})

    def test_path_traversal_duplicates_and_nested_archives(self):
        for name, code in (
            ("../x", "UNSAFE_ARCHIVE_PATH"),
            ("/etc/x", "UNSAFE_ARCHIVE_PATH"),
            ("C:/x", "UNSAFE_ARCHIVE_PATH"),
            ("nested.zip", "NESTED_ARCHIVE_UNINSPECTED"),
        ):
            with self.subTest(name=name):
                self.make([(name, "data")])
                self.assertIn(code, {x["token"] for x in self.check()["findings"]})
        self.make([("foo.md", "a"), ("FOO.MD", "b")])
        self.assertIn("DUPLICATE_ARCHIVE_PATH",
                      {x["token"] for x in self.check()["findings"]})

    def test_links_and_file_directory_collisions(self):
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.make([(link, "target")])
        self.assertIn("UNSAFE_ARCHIVE_MEMBER_TYPE",
                      {x["token"] for x in self.check()["findings"]})
        self.make([("folder", "file"), ("folder/child.md", "text")])
        self.assertIn("FILE_DIRECTORY_COLLISION",
                      {x["token"] for x in self.check()["findings"]})

    def test_binary_is_explicitly_uninspected(self):
        self.make([("asset.png", b"\x89PNG\r\n"), ("readme.md", "safe")])
        result = self.check()
        self.assertEqual("PASS", result["status"])
        self.assertEqual(1, result["opaque_members_uninspected"])
        self.assertFalse(result["binary_contents_verified"])

    def test_corrupt_empty_and_cli_readonly(self):
        self.make([])
        self.assertEqual("FAIL", self.check()["status"])
        self.path.write_bytes(b"not zip")
        self.assertEqual("FAIL", self.check()["status"])
        self.make([("readme.md", "okay")])
        before = self.path.read_bytes()
        output = io.StringIO()
        with redirect_stdout(output):
            code = audit.main(["--zip", str(self.path),
                               "--repository", "sample-owner/toolkit"])
        self.assertEqual(0, code)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual("PASS", json.loads(output.getvalue())["status"])


if __name__ == "__main__":
    unittest.main()
