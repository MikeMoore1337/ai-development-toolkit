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
        self.assertEqual(1, len(catalog["plugins"]))
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
            self.assertIn("PUBLIC_DIRECTORY_NOT_SUBMITTED", text)
            self.assertIn("REPO_MARKETPLACE_READY_FOR_CLIENT_TEST", text)
            powershell = text.split("~~~powershell\n", 1)[1].split("\n~~~", 1)[0]
            shell = text.split("~~~sh\n", 1)[1].split("\n~~~", 1)[0]
            self.assertEqual(1, len(powershell.splitlines()))
            self.assertEqual(1, len(shell.splitlines()))
            commands.append((powershell, shell))
        self.assertEqual(commands[0], commands[1])

    def test_installers_are_reused_not_duplicated(self):
        package = ROOT / "integrations/personal-mcp/adt-personal"
        for name in ("Install-ADT-Personal.ps1", "Install-ADT-Personal.sh", "mcp/adt_mcp.py", "mcp/adt_discovery.py"):
            self.assertTrue((package / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
