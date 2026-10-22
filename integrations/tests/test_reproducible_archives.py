"""Offline evidence: integration bundles use stable metadata and source-derived versions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_packages as pkg


class ReproduciblePackagesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / "src"
        self.src.mkdir()
        (self.src / "z").mkdir()
        (self.src / "z" / "two.txt").write_text("second\n", encoding="utf-8")
        (self.src / "alpha.txt").write_text("one\n", encoding="utf-8")

    def test_same_source_produces_identical_archives_across_mtime(self):
        first = self.root / "first.zip"
        second = self.root / "second.zip"
        a = pkg.archive(self.src, first, "bundle")
        os.utime(self.src / "alpha.txt", (100_000_000, 100_000_000))
        os.utime(self.src / "z" / "two.txt", (2_000_000_000, 2_000_000_000))
        b = pkg.archive(self.src, second, "bundle")
        self.assertEqual(a["sha256"], b["sha256"])
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(a["source_sha256"], b["source_sha256"])
        self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(), a["sha256"])
        with ZipFile(first, "r") as z:
            self.assertEqual(
                ["bundle/alpha.txt", "bundle/z/two.txt"], z.namelist())
            self.assertEqual({pkg.ZIP_TIMESTAMP},
                             {item.date_time for item in z.infolist()})
            self.assertEqual({0o100644},
                             {item.external_attr >> 16 for item in z.infolist()})
            self.assertIsNone(z.testzip())

    def test_change_in_content_changes_digest(self):
        a = pkg.archive(self.src, self.root / "a.zip", "bundle")
        (self.src / "alpha.txt").write_text("modified", encoding="utf-8")
        b = pkg.archive(self.src, self.root / "b.zip", "bundle")
        self.assertNotEqual(a["sha256"], b["sha256"])
        self.assertNotEqual(a["source_sha256"], b["source_sha256"])

    def test_filters_build_cache_without_changing_contents(self):
        (self.src / "__pycache__").mkdir()
        (self.src / "__pycache__" / "module.pyc").write_bytes(b"bytecode")
        (self.src / ".DS_Store").write_bytes(b"macOS metadata")
        records = pkg.source_files(self.src)
        self.assertEqual(["alpha.txt", "z/two.txt"], [path for path, _ in records])

    def test_symlink_not_archived(self):
        target = self.root / "outside.txt"
        target.write_text("private", encoding="utf-8")
        try:
            (self.src / "linked.txt").symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Host OS forbids creating symlinks")
        with self.assertRaisesRegex(pkg.BundleError, "linked source"):
            pkg.source_files(self.src)

    def test_rejects_unknown_versions_without_importing_code(self):
        py = self.src / "mcp.py"
        py.write_text("VERSION = '0.1.9'\nraise RuntimeError('Must not execute')\n",
                      encoding="utf-8")
        self.assertEqual("0.1.9", pkg.source_version(py))
        py.write_text("VERSION = os.getenv('FAKE_VERSION')", encoding="utf-8")
        with self.assertRaisesRegex(pkg.BundleError, "VERSION literal"):
            pkg.source_version(py)
        for version in ("0.1.9/../../path", "a.b.c", "1.2.3+evil", ""):
            with self.subTest(version=version):
                with self.assertRaises(pkg.BundleError):
                    pkg.checked_version(version)

    def test_rejects_unsafe_paths_and_empty_package(self):
        for top in ("../out", ".", "..", "nested/name", "nested\\name", ""):
            with self.subTest(top=top):
                with self.assertRaises(pkg.BundleError):
                    pkg.archive(self.src, self.root / "no.zip", top)
        with self.assertRaisesRegex(pkg.BundleError, "Empty"):
            empty = self.root / "empty"\n            empty.mkdir()\n            pkg.source_files(empty)

    def test_refuses_large_file_before_writing_archive(self):
        big = self.src / "oversized.bin"
        with big.open("wb") as handle:
            handle.truncate(pkg.MAX_FILE_BYTES + 1)
        with self.assertRaisesRegex(pkg.BundleError, "size limit"):
            pkg.archive(self.src, self.root / "big.zip", "bundle")
        self.assertFalse((self.root / "big.zip").exists())

    def test_main_uses_source_versions_and_never_claims_installed(self):
        import io
        from contextlib import redirect_stdout
        fakebase = self.root / "integrations"
        server = fakebase / "personal-mcp" / "adt-personal"
        plugin = fakebase / "chatgpt-plugin" / "ai-development-toolkit"
        (server / "mcp").mkdir(parents=True)
        plugin.mkdir(parents=True)
        (server / "mcp" / "adt_mcp.py").write_text("VERSION = '9.8.7'\n",
                                                     encoding="utf-8")
        (plugin / "plugin.json").write_text(
            json.dumps({"name": "ai-development-toolkit", "version": "3.2.1"}),
            encoding="utf-8")
        buf = io.StringIO()
        with patch.object(pkg, "BASE", fakebase), redirect_stdout(buf):
            self.assertEqual(0, pkg.main(["--output", str(self.root / "dist")]))
        result = json.loads(buf.getvalue())
        self.assertEqual("SOURCE_ARCHIVES_BUILT_NOT_INSTALLED", result["status"])
        self.assertEqual("NOT_VERIFIED", result["codex_installed_mcp"])
        self.assertEqual("NOT_VERIFIED", result["chatgpt_installed_plugin"])
        self.assertEqual("9.8.7", result["mcp_source_version"])
        self.assertEqual("3.2.1", result["plugin_package_version"])
        self.assertTrue((self.root / "dist" / "AI-Development-Toolkit-Personal-MCP-9.8.7.zip").is_file())
        self.assertTrue((self.root / "dist" / "AI-Development-Toolkit-ChatGPT-Plugin-3.2.1.zip").is_file())

    def test_no_real_client_or_unreviewed_update_is_invoked(self):
        import inspect
        text = inspect.getsource(pkg)
        self.assertNotIn("import requests", text)
        self.assertNotIn("subprocess.run(", text)
        self.assertNotIn("codex mcp add", text)
        self.assertNotIn("plugin install", text)


if __name__ == "__main__":
    unittest.main()
