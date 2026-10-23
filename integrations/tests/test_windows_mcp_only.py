"""Windows upgrade smoke: real PowerShell, no Codex CLI or user-home modifications."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "integrations" / "personal-mcp" / "adt-personal"


@unittest.skipUnless(os.name == "nt", "Requires Windows PowerShell")
class TestMcpOnlyUpgrade(unittest.TestCase):
    def test_upgrades_only_module_pair_and_is_idempotent(self):
        with tempfile.TemporaryDirectory(prefix="adt-mcp-only-") as temp:
            home = Path(temp)
            installed = home / "ADT-Personal" / "mcp"
            installed.mkdir(parents=True)
            launcher = installed / "adt_mcp.py"
            launcher.write_text("# 0.1.6 old entrypoint\n", encoding="utf-8")
            original = launcher.read_bytes()
            config = home / "codex" / "config.toml"
            config.parent.mkdir()
            config.write_text('[mcp_servers.other]\ncommand="python"\n', encoding="utf-8")
            env = {**os.environ, "LOCALAPPDATA": str(home),
                   "CODEX_HOME": str(config.parent)}
            command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                       "-File", str(PACKAGE / "Install-ADT-Personal.ps1"),
                       "-McpOnly", "-ToolkitPath", str(ROOT)]

            preview = subprocess.run(command + ["-WhatIf"], env=env,
                                     capture_output=True, text=True, timeout=30)
            self.assertEqual(preview.returncode, 0, preview.stderr + preview.stdout)
            self.assertEqual(launcher.read_bytes(), original)
            self.assertFalse((installed / "adt_discovery.py").exists())

            applied = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(applied.returncode, 0, applied.stderr + applied.stdout)
            self.assertIn("Installed MCP module pair:", applied.stdout)
            for name in ("adt_mcp.py", "adt_discovery.py"):
                self.assertEqual((installed / name).read_bytes(),
                                 (PACKAGE / "mcp" / name).read_bytes())
            self.assertTrue(list(installed.glob("adt_mcp.py.adt-backup-*")))
            self.assertEqual(config.read_text(encoding="utf-8"),
                             '[mcp_servers.other]\ncommand="python"\n')
            self.assertFalse((config.parent / "AGENTS.md").exists())

            backup_count = len(list(installed.glob("*.adt-backup-*")))
            second = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
            self.assertEqual(backup_count, len(list(installed.glob("*.adt-backup-*"))))

    def test_missing_launcher_refuses_new_registration(self):
        with tempfile.TemporaryDirectory(prefix="adt-mcp-only-missing-") as temp:
            env = {**os.environ, "LOCALAPPDATA": temp}
            cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                   "-File", str(PACKAGE / "Install-ADT-Personal.ps1"),
                   "-McpOnly", "-ToolkitPath", str(ROOT)]
            run = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=20)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("requires an existing MCP launcher", run.stderr + run.stdout)
            self.assertFalse((Path(temp) / "ADT-Personal" / "mcp").exists())


if __name__ == "__main__":
    unittest.main()
