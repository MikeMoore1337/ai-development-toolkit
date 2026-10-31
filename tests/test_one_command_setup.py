"""Offline contracts for the one-paste MCP instructions and local plugin catalog."""
from __future__ import annotations
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/MikeMoore1337/ai-development-toolkit.git"


class OneCommandDistributionTests(unittest.TestCase):
    def test_marketplace_points_to_existing_portable_plugin(self):
        catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual("ai-development-toolkit-local", catalog["name"])
        self.assertEqual(3, len(catalog["plugins"]))
        entry = catalog["plugins"][0]
        self.assertEqual("local", entry["source"]["source"])
        relative = entry["source"]["path"]
        self.assertTrue(relative.startswith("./"))
        root = (ROOT / relative).resolve()
        self.assertTrue(root.is_relative_to(ROOT.resolve()))
        self.assertEqual("AVAILABLE", entry["policy"]["installation"])
        self.assertEqual("ON_INSTALL", entry["policy"]["authentication"])
        plugin = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], entry["name"])
        self.assertGreater(len(list((root / "skills").glob("*/SKILL.md"))), 0)
        self.assertFalse((root / "mcp.json").exists())

        # ECC stays original, pinned, optional and cannot execute on catalog read.
        ecc = catalog["plugins"][1]
        self.assertEqual("ecc", ecc["name"])
        self.assertEqual(
            {
                "source": "url",
                "url": "https://github.com/affaan-m/ECC.git",
                "sha": "25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b",
            },
            ecc["source"],
        )
        self.assertEqual(
            {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            ecc["policy"],
        )
        self.assertEqual("Productivity", ecc["category"])
        self.assertNotIn("hooks", ecc)
        self.assertNotIn("mcpServers", ecc)
        self.assertNotIn("postinstall", ecc)

        # The full original Codex plugin is available to install, never auto-enabled.
        ponytail = catalog["plugins"][2]
        self.assertEqual("ponytail", ponytail["name"])
        self.assertEqual(
            {
                "source": "url",
                "url": "https://github.com/DietrichGebert/ponytail.git",
                "sha": "16352ac229eb08a9598dcae48fe9f2b342567d86",
            },
            ponytail["source"],
        )
        self.assertEqual(
            {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            ponytail["policy"],
        )
        self.assertNotIn("hooks", ponytail)
        self.assertNotIn("postinstall", ponytail)

    def test_ru_en_one_paste_commands_have_same_safe_source(self):
        commands = []
        for relative in ("docs/ONE_COMMAND_SETUP.md", "docs/ru/ONE_COMMAND_SETUP.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("~~~powershell\n& {", text)
            self.assertIn("~~~sh\nsh -c", text)
            self.assertIn(REPO, text)
            self.assertIn("remote get-url origin", text)
            self.assertIn("status --porcelain", text)
            self.assertIn("Refusing linked Toolkit source", text)
            self.assertIn("Install-ADT-Personal.ps1", text)
            self.assertIn("Install-ADT-Personal.sh", text)
            self.assertIn("-ToolkitPath $d -Codex", text)
            self.assertIn("--source \"$d\"", text)
            self.assertNotIn("ExecutionPolicy Bypass", text)
            self.assertNotIn(" | iex", text.lower())
            self.assertIn("REPO_SELF_INSTALL_SOURCE_READY", text)
            self.assertIn("LIVE_DESKTOP_INSTALL_NOT_VERIFIED", text)
            self.assertIn("codex plugin marketplace add MikeMoore1337/ai-development-toolkit", text)
            self.assertIn("codex plugin marketplace list", text)
            self.assertNotIn("PUBLIC_DIRECTORY_NOT_SUBMITTED", text)
            self.assertNotIn("submission and review", text)
            powershell = text.split("~~~powershell\n", 1)[1].split("\n~~~", 1)[0]
            shell = text.split("~~~sh\n", 1)[1].split("\n~~~", 1)[0]
            self.assertEqual(1, len(powershell.splitlines()))
            self.assertEqual(1, len(shell.splitlines()))
            commands.append((powershell, shell))
        self.assertEqual(commands[0], commands[1])

    def test_plugin_repo_install_documented_without_public_publication(self):
        for relative in ("integrations/chatgpt-plugin/README.md", "integrations/chatgpt-plugin/README.ru.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("codex plugin marketplace add MikeMoore1337/ai-development-toolkit", text)
            self.assertIn("AI Development Toolkit (local)", text)
            self.assertIn("0.1.4", text)

    def test_installers_are_reused_not_duplicated(self):
        package = ROOT / "integrations/personal-mcp/adt-personal"
        for name in ("Install-ADT-Personal.ps1", "Install-ADT-Personal.sh", "mcp/adt_mcp.py", "mcp/adt_discovery.py"):
            self.assertTrue((package / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
