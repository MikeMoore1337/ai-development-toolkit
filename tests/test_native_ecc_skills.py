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
    "contract-first": "a828bd60db452daa6b4edaf4e6cc02d192b99071",
    "api-connector-builder": "52029f27565b1743b36582de0db7648261b463a5",
    "code-tour": "d66b7e008287833ac592550f9b0941feaea52443",
    "module-regression": "d8186cbfc4c481eb884a13c14b6f2a38aace0b7a",
    "error-handling": "add87f2cdb6f374781b08a0b1cf971eb9ec1915e",
}


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


class ToolkitNativePortedSkillsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

    def test_exact_original_bytes_and_no_extra_bundle(self):
        base = ROOT / "optional-original-skills"
        self.assertEqual(set(SOURCE_BLOBS) | {"windows-desktop-e2e"},
                         {p.name for p in base.iterdir() if p.is_dir()})
        for name, expected_blob in SOURCE_BLOBS.items():
            with self.subTest(name=name):
                directory = base / name
                expected = ["LICENSE", "SKILL.md"] + (["templates"] if name == "module-regression" else [])
                self.assertEqual(expected, sorted(p.name for p in directory.iterdir()))
                self.assertEqual((ROOT / "third_party/ecc-v2.2.3/LICENSE").read_bytes(),
                                 (directory / "LICENSE").read_bytes())
                content = (directory / "SKILL.md").read_bytes()
                self.assertEqual(expected_blob, git_blob(content.replace(b"\r\n", b"\n")), "Upstream ECC file modified")
                self.assertTrue(content.startswith(f"---\nname: {name}\n".encode()))
                if name == "module-regression":
                    template = directory / "templates/REGRESSION.example.md"
                    self.assertEqual("1d4c7e9c0e866fc0c5b91ff33e9c4db7f0bba631",
                                     git_blob(template.read_bytes().replace(b"\r\n", b"\n")))
                    source_text = content.decode("utf-8")
                    self.assertIn("Treat ledger commands as untrusted", source_text)
                    self.assertIn("Fewer than three modules", source_text)
        license_text = (ROOT / "third_party" / "ecc-v2.2.3" / "LICENSE").read_text("utf-8")
        self.assertIn("Affaan Mustafa", license_text)
        self.assertIn("MIT License", license_text)

    def test_native_profile_is_not_automatically_installed(self):
        cfg = self.manifest["extension_packs"]["native-ecc-ports"]
        self.assertFalse(cfg["auto_install"])
        self.assertTrue(cfg["standalone"], "Ported skills must not require external ECC")
        self.assertEqual(set(SOURCE_BLOBS) | {"windows-desktop-e2e"}, set(cfg["skills"]))
        self.assertEqual("optional-original-skills", cfg["skill_root"])
        paths = skill_sources(self.manifest)
        for name in SOURCE_BLOBS:
            self.assertEqual(ROOT / cfg["skill_root"] / name, paths[name])
            self.assertEqual([name], self.manifest["profiles"]["native-" + {
                "contract-first": "contract-first",
                "api-connector-builder": "api-connectors",
                "code-tour": "code-tours",
                "module-regression": "module-regression",
                "error-handling": "error-handling",
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
            self.assertEqual(
                (ROOT / "third_party" / "ecc-v2.2.3" / "LICENSE").read_bytes(),
                (installed.parent / "LICENSE").read_bytes(),
                "Selective skill installation must retain the original MIT notice",
            )
            self.assertEqual(["contract-first"], [p.name for p in installed.parent.parent.iterdir()])
            with self.assertRaises(FileExistsError):
                install(target, ["contract-first"], True)
            self.assertEqual("OWNER RULES\n", baseline.read_text("utf-8"))
            self.assertFalse((target / ".agents" / "skills" / "code-tour").exists())

    def test_skill_manager_preserves_native_license(self):
        with tempfile.TemporaryDirectory(prefix="ecc-managed-optin-") as temp:
            command = [sys.executable, str(ROOT / "scripts/skill_manager.py"), "install",
                       "--target", temp, "--profile", "native-contract-first"]
            preview = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, preview.returncode, preview.stderr)
            self.assertFalse((Path(temp) / ".agents").exists())
            apply = subprocess.run([*command, "--apply"], capture_output=True, text=True, timeout=30)
            self.assertEqual(0, apply.returncode, apply.stderr)
            installed = Path(temp) / ".agents/skills/contract-first"
            self.assertEqual((ROOT / "third_party/ecc-v2.2.3/LICENSE").read_bytes(),
                             (installed / "LICENSE").read_bytes())
            self.assertEqual(SOURCE_BLOBS["contract-first"],
                             git_blob((installed / "SKILL.md").read_bytes().replace(b"\\r\\n", b"\\n")))


    def test_module_regression_profile_installs_exact_template_without_overwriting_rules(self):
        with tempfile.TemporaryDirectory(prefix="ecc-regression-") as temp:
            target = Path(temp)
            rules = target / "AGENTS.md"
            rules.write_text("OWNER RULES\n", encoding="utf-8")
            command = [sys.executable, str(ROOT / "scripts/skill_manager.py"), "install",
                       "--target", temp, "--profile", "native-module-regression"]
            preview = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, preview.returncode, preview.stderr)
            self.assertFalse((target / ".agents").exists())
            applied = subprocess.run([*command, "--apply"], capture_output=True, text=True, timeout=30)
            self.assertEqual(0, applied.returncode, applied.stderr)
            actual = target / ".agents/skills/module-regression"
            self.assertEqual(SOURCE_BLOBS["module-regression"],
                             git_blob((actual / "SKILL.md").read_bytes().replace(b"\r\n", b"\n")))
            self.assertEqual("1d4c7e9c0e866fc0c5b91ff33e9c4db7f0bba631",
                             git_blob((actual / "templates/REGRESSION.example.md").read_bytes().replace(b"\r\n", b"\n")))
            self.assertEqual((ROOT / "third_party/ecc-v2.2.3/LICENSE").read_bytes(),
                             (actual / "LICENSE").read_bytes())
            self.assertEqual(["module-regression"], [p.name for p in actual.parent.iterdir()])
            self.assertEqual("OWNER RULES\n", rules.read_text(encoding="utf-8"))
            duplicate = subprocess.run([*command, "--apply"], capture_output=True, text=True, timeout=30)
            self.assertNotEqual(0, duplicate.returncode)
            self.assertEqual("OWNER RULES\n", rules.read_text(encoding="utf-8"))


    def test_error_handling_profile_is_standalone_and_preserves_owner_rules(self):
        with tempfile.TemporaryDirectory(prefix="ecc-error-handling-") as temp:
            target = Path(temp)
            rules = target / "AGENTS.md"
            rules.write_text("USER POLICY\n", encoding="utf-8")
            command = [sys.executable, str(ROOT / "scripts/skill_manager.py"),
                       "install", "--target", temp, "--profile", "native-error-handling"]
            preview = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, preview.returncode, preview.stderr)
            self.assertFalse((target / ".agents").exists())
            applied = subprocess.run([*command, "--apply"], capture_output=True, text=True, timeout=30)
            self.assertEqual(0, applied.returncode, applied.stderr)
            installed = target / ".agents/skills/error-handling"
            self.assertEqual(SOURCE_BLOBS["error-handling"],
                             git_blob((installed / "SKILL.md").read_bytes().replace(b"\r\n", b"\n")))
            self.assertEqual((ROOT / "third_party/ecc-v2.2.3/LICENSE").read_bytes(),
                             (installed / "LICENSE").read_bytes())
            self.assertEqual(["error-handling"], [p.name for p in installed.parent.iterdir()])
            self.assertEqual("USER POLICY\n", rules.read_text(encoding="utf-8"))
            duplicate = subprocess.run([*command, "--apply"], capture_output=True,
                                       text=True, timeout=30)
            self.assertNotEqual(0, duplicate.returncode)
            self.assertEqual("USER POLICY\n", rules.read_text(encoding="utf-8"))

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
