"""Offline DeepSeek Harness Skills and Cordis bundle contract checks (#413)."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "integrations" / "deepseek-harness"
spec = importlib.util.spec_from_file_location("adt_harness_bundle", INTEGRATION / "prepare_bundle.py")
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)
sys.path.insert(0, str(ROOT / "scripts"))
import verify_client_compatibility as compat


class DeepSeekHarnessTests(unittest.TestCase):
    def test_scaffold_is_disabled_without_machine_specific_path(self):
        manifest = json.loads((INTEGRATION / "package.json").read_text(encoding="utf-8"))
        self.assertEqual("./cordis.patch.yml", manifest["dsh"]["bundle"]["patch"])
        self.assertTrue(manifest["private"])
        for locale in ("en", "ru"):
            name = INTEGRATION / "locale" / f"{locale}.json"
            data = json.loads(name.read_text(encoding="utf-8"))
            self.assertTrue(data["meta"]["title"])
            self.assertTrue(data["meta"]["description"])
        self.assertIn("<svg", (INTEGRATION / "icon.svg").read_text(encoding="utf-8"))
        source = yaml.safe_load((INTEGRATION / "cordis.patch.yml").read_text(encoding="utf-8"))
        self.assertTrue(source[0]["insert"][0]["disabled"])

    def test_preview_apply_and_generated_stdio_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp).resolve() / "bundle"
            source_before = (INTEGRATION / "package.json").read_bytes()
            report = bundle.build(target)
            self.assertEqual("PLAN_ONLY", report["status"])
            self.assertFalse(target.exists())
            result = bundle.build(target, apply=True)
            self.assertEqual("BUNDLE_CREATED", result["status"])
            self.assertTrue(result["applied"])
            self.assertFalse(result["writes_toolkit"])
            self.assertFalse(result["changes_harness_profile"])
            data = yaml.safe_load((target / "cordis.patch.yml").read_text(encoding="utf-8"))
            row = data[0]["insert"][0]
            self.assertEqual("adt-mcp", row["id"])
            self.assertNotIn("disabled", row)
            self.assertEqual("@deepseek-ai/dsh-mcp-client", row["name"])
            config = row["config"]
            self.assertEqual("stdio", config["transport"])
            self.assertEqual(str(Path(sys.executable).absolute()), config["command"])
            self.assertEqual([str(ROOT / "scripts/toolkit_mcp.py"), "serve"], config["args"])
            self.assertTrue(config["failOnStartupError"])
            self.assertEqual(source_before, (INTEGRATION / "package.json").read_bytes())
            self.assertEqual(set(result["files"]),
                             {f.relative_to(target).as_posix() for f in target.rglob("*") if f.is_file()})
            with self.assertRaisesRegex(bundle.BundleError, "exists"):
                bundle.build(target, apply=True)

    def test_refuses_source_and_nonexistent_or_linked_output(self):
        with self.assertRaisesRegex(bundle.BundleError, "inside Toolkit"):
            bundle.build(ROOT / "generated-bundle")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            with self.assertRaisesRegex(bundle.BundleError, "parent"):
                bundle.build(root / "missing-parent" / "bundle")
            real = root / "real"
            real.mkdir()
            link = root / "link"
            try:
                link.symlink_to(real, target_is_directory=True)
            except (OSError, NotImplementedError):
                return
            with self.assertRaisesRegex(bundle.BundleError, "Symlink"):
                bundle.build(link / "bundle")

    def test_project_skill_layouts_and_no_native_invocation_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp).resolve()
            for layout in (".agents/skills", ".dsh/skills"):
                target = project / layout / "smoke"
                target.mkdir(parents=True)
                (target / "SKILL.md").write_text(
                    "---\nname: smoke\ndescription: A portable synthetic test skill.\n---\n"
                    "Read and use the specified smoke guidance.\n", encoding="utf-8"
                )
                check = compat.check_project(project, "deepseek-harness", ["smoke"], layout=layout)
                self.assertEqual("PASS", check["status"])
                self.assertEqual("NOT_TESTED", check["levels"]["L4"])
                self.assertEqual("NOT_TESTED", check["levels"]["L5"])
            with self.assertRaisesRegex(compat.ContractError, "Unsupported layout"):
                compat.check_project(project, "deepseek-harness", ["smoke"],
                                     layout=".claude/skills")


if __name__ == "__main__":
    unittest.main()
