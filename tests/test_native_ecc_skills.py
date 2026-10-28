"""Offline checks for original MIT source **bundled inside Toolkit**, not external ECC runtime (#435)."""
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
from install import install, skill_sources  # noqa: E402

SOURCE_BLOBS = {
    "windows-desktop-e2e": "f965b043cee51ed1c464088c08b91cf05710d65f",
    "contract-first": "a828bd60db452daa6b4edaf4e6cc02d192b99071",
    "api-connector-builder": "52029f27565b1743b36582de0db7648261b463a5",
    "code-tour": "d66b7e008287833ac592550f9b0941feaea52443",
}


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


class ToolkitNativePortedSkillsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

    def test_exact_original_bytes_and_no_extra_bundle(self):
        base = ROOT / "optional-original-skills"
        self.assertEqual(set(SOURCE_BLOBS), {p.name for p in base.iterdir() if p.is_dir()})
        for name, expected_blob in SOURCE_BLOBS.items():
            with self.subTest(name=name):
                directory = base / name
                self.assertEqual(["SKILL.md"], sorted(p.name for p in directory.iterdir()))
                content = (directory / "SKILL.md").read_bytes()
                self.assertEqual(expected_blob, git_blob(content.replace(b"\r\n", b"\n")), "Upstream ECC file modified")
                self.assertTrue(content.startswith(f"---\nname: {name}\n".encode()))
        license_text = (ROOT / "third_party" / "ecc-v2.2.3" / "LICENSE").read_text("utf-8")
        self.assertIn("Affaan Mustafa", license_text)
        self.assertIn("MIT License", license_text)

    def test_native_profile_is_not_automatically_installed(self):
        cfg = self.manifest["extension_packs"]["native-ecc-ports"]
        self.assertFalse(cfg["auto_install"])
        self.assertEqual(set(SOURCE_BLOBS), set(cfg["skills"]))
        self.assertEqual("optional-original-skills", cfg["skill_root"])
        paths = skill_sources(self.manifest)
        for name in SOURCE_BLOBS:
            self.assertEqual(ROOT / cfg["skill_root"] / name, paths[name])
            self.assertEqual([name], self.manifest["profiles"]["native-" + {
                "windows-desktop-e2e": "windows-desktop",
                "contract-first": "contract-first",
                "api-connector-builder": "api-connectors",
                "code-tour": "code-tours",
            }[name]])

    def test_original_single_skill_install_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="ecc-optin-test-") as temp:
            target = Path(temp)
            baseline = target / "AGENTS.md"
            baseline.write_text("OWNER RULES\n", encoding="utf-8")
            install(target, ["contract-first"], False)
            self.assertFalse((target / ".agents").exists(), "dry run modified the destination")
            install(target, ["contract-first"], True)
            installed = target / ".agents" / "skills" / "contract-first" / "SKILL.md"
            self.assertEqual(git_blob(installed.read_bytes().replace(b"\r\n", b"\n")), SOURCE_BLOBS["contract-first"])
            self.assertEqual("OWNER RULES\n", baseline.read_text("utf-8"))
            self.assertEqual(["contract-first"], [p.name for p in installed.parent.parent.iterdir()])
            with self.assertRaises(FileExistsError):
                install(target, ["contract-first"], True)
            self.assertEqual("OWNER RULES\n", baseline.read_text("utf-8"))
            self.assertFalse((target / ".agents" / "skills" / "windows-desktop-e2e").exists())
            self.assertFalse((target / ".agents" / "skills" / "code-tour").exists())

    def test_user_visible_profile_dry_run_does_not_mutate(self):
        with tempfile.TemporaryDirectory(prefix="ecc-cli-test-") as temp:
            p = subprocess.run([sys.executable, str(ROOT / "scripts" / "install.py"),
                                "--target", temp, "--profile", "native-code-tours"],
                               capture_output=True, text=True, timeout=25, check=False)
            self.assertEqual(0, p.returncode, p.stderr)
            self.assertIn("DRY-RUN", p.stdout)
            self.assertFalse((Path(temp) / ".agents").exists())
            self.assertFalse((Path(temp) / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
