"""Source-only acceptance for the native Windows UIA E2E skill (#450).

These checks never run pywinauto, a Windows application, or a model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_pack import validate_skill, _check_links, inspect  # noqa: E402

SKILL = ROOT / "optional-original-skills/windows-desktop-e2e"
ORIGINAL = SKILL / "references/ORIGINAL_SKILL.md"
UPSTREAM_BLOB = "f965b043cee51ed1c464088c08b91cf05710d65f"
UPSTREAM_REF = "25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b"


def git_blob(data: bytes) -> str:
    data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


class NativeWindowsE2ETests(unittest.TestCase):
    def test_compact_valid_skill_and_readable_reference(self):
        self.assertEqual([], validate_skill(SKILL))
        self.assertEqual([], _check_links(SKILL / "SKILL.md", SKILL))
        entry = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(entry.splitlines()), 500)
        self.assertIn("references/ORIGINAL_SKILL.md", entry)
        self.assertIn(UPSTREAM_REF, entry)
        self.assertEqual([], inspect())

    def test_original_source_is_unmodified(self):
        self.assertTrue(ORIGINAL.is_file())
        self.assertEqual(UPSTREAM_BLOB, git_blob(ORIGINAL.read_bytes()))
        self.assertGreaterEqual(len(ORIGINAL.read_text(encoding="utf-8").splitlines()), 800)
        self.assertEqual(
            (ROOT / "third_party/ecc-v2.2.3/LICENSE").read_bytes(),
            (SKILL / "LICENSE").read_bytes(),
        )

    def test_native_only_opt_in_and_explicit_permission(self):
        m = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        pack = m["extension_packs"]["native-ecc-ports"]
        self.assertIn("windows-desktop-e2e", pack["skills"])
        self.assertFalse(pack["auto_install"])
        self.assertTrue(pack["standalone"])
        self.assertEqual(["windows-desktop-e2e"], m["profiles"]["native-windows-desktop-e2e"])
        for profile in ("general", "qa-python", "qa-ci"):
            self.assertNotIn("windows-desktop-e2e", m["profiles"][profile])
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for marker in (
            "explicit owner authorization",
            "Electron",
            "WebView2",
            "NOT_VERIFIED",
            "production data store",
            "negative paths",
            "Windows interactive",
            "pywinauto",
        ):
            self.assertIn(marker, text)

    def test_managed_install_copies_full_reference_and_mit_notice(self):
        with tempfile.TemporaryDirectory(prefix="native-uia-") as temp:
            root = Path(temp)
            protected = root / "AGENTS.md"
            protected.write_text("PRESERVE ME\n", encoding="utf-8")
            command = [sys.executable, str(ROOT / "scripts/skill_manager.py"), "install",
                       "--target", temp, "--profile", "native-windows-desktop-e2e"]
            preview = subprocess.run(command, capture_output=True, text=True, timeout=35)
            self.assertEqual(0, preview.returncode, preview.stderr)
            self.assertFalse((root / ".agents").exists())
            applied = subprocess.run([*command, "--apply"], capture_output=True,
                                     text=True, timeout=35)
            self.assertEqual(0, applied.returncode, applied.stderr)
            folder = root / ".agents/skills/windows-desktop-e2e"
            self.assertEqual(UPSTREAM_BLOB, git_blob((folder / "references/ORIGINAL_SKILL.md").read_bytes()))
            self.assertEqual((SKILL / "LICENSE").read_bytes(), (folder / "LICENSE").read_bytes())
            self.assertEqual("PRESERVE ME\n", protected.read_text(encoding="utf-8"))
            with self.assertRaises(FileNotFoundError):
                # Installation never produces an external ECC runtime or CLI.
                (root / ".agents/skills/ecc-runtime").read_bytes()
            reapply = subprocess.run([*command, "--apply"], capture_output=True,
                                     text=True, timeout=35)
            self.assertNotEqual(0, reapply.returncode)
            self.assertEqual("PRESERVE ME\n", protected.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
