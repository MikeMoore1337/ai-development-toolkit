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
            env = {**os.environ, "ADT_MCP_TEST_LOCAL": str(home),
                   "CODEX_HOME": str(config.parent)}
            # PowerShell 5.1 may depend on the real LOCALAPPDATA to auto-load
            # Microsoft.PowerShell.Utility (Get-FileHash). Load it FIRST,
            # then isolate the installer target within this subprocess.
            installer = str(PACKAGE / "Install-ADT-Personal.ps1").replace("'", "''")
            toolkit = str(ROOT).replace("'", "''")
            base = ("$ErrorActionPreference='Stop'; "
                    "Import-Module Microsoft.PowerShell.Utility -ErrorAction Stop; "
                    "$env:LOCALAPPDATA=$env:ADT_MCP_TEST_LOCAL; "
                    f"& '{installer}' -McpOnly -ToolkitPath '{toolkit}'")
            def execute(extra=""):
                ps = base + extra
                return subprocess.run(
                    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                     "-Command", ps], env=env,
                    capture_output=True, text=True, timeout=35)

            preview = execute(" -WhatIf")
            self.assertEqual(preview.returncode, 0, preview.stderr + preview.stdout)
            self.assertEqual(launcher.read_bytes(), original)
            self.assertFalse((installed / "adt_discovery.py").exists())

            applied = execute()
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
            second = execute()
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
            self.assertEqual(backup_count, len(list(installed.glob("*.adt-backup-*"))))

    def test_installed_self_check_failure_restores_both_old_modules(self):
        # Real PowerShell on a disposable Windows runner only. Trigger a
        # deterministic failure AFTER both new modules are copied, without
        # introducing test-only branches in the production installer.
        import shutil
        original_py = shutil.which("py")
        if not original_py:
            self.skipTest("Windows Python launcher unavailable")

        with tempfile.TemporaryDirectory(prefix="adt-mcp-only-rollback-") as temp:
            root = Path(temp)
            installed = root / "ADT-Personal" / "mcp"
            installed.mkdir(parents=True)
            old_server = b"# old MCP 0.1.6 entrypoint\r\n"
            old_discovery = b"# old companion (synthetic)\r\n"
            (installed / "adt_mcp.py").write_bytes(old_server)
            (installed / "adt_discovery.py").write_bytes(old_discovery)

            # Emulate an existing unrelated Codex user configuration;
            # install -McpOnly must not touch it, even on failure.
            config = root / "codex" / "config.toml"
            config.parent.mkdir()
            original_config = b'[mcp_servers.other]\ncommand="python"\n'
            config.write_bytes(original_config)

            shim_dir = root / "shim"
            shim_dir.mkdir()
            shim = shim_dir / "py.cmd"
            # Fail only on the *installed* launcher check, not the initial
            # source package or staged self-check. No injected paid tooling.
            shim.write_text(
                "@echo off\n"
                'echo %* | findstr /I /L /C:"\\ADT-Personal\\mcp\\adt_mcp.py" >nul\n'
                "if not errorlevel 1 exit /b 87\n"
                f'"{original_py}" %*\n',
                encoding="ascii",
            )
            env = {**os.environ,
                   "ADT_MCP_TEST_LOCAL": str(root),
                   "CODEX_HOME": str(config.parent),
                   "PATH": str(shim_dir) + os.pathsep + os.environ["PATH"]}
            installer = str(PACKAGE / "Install-ADT-Personal.ps1").replace("'", "''")
            toolkit = str(ROOT).replace("'", "''")
            command = (
                "$ErrorActionPreference='Stop'; "
                "Import-Module Microsoft.PowerShell.Utility -ErrorAction Stop; "
                "$env:LOCALAPPDATA=$env:ADT_MCP_TEST_LOCAL; "
                f"& '{installer}' -McpOnly -ToolkitPath '{toolkit}'"
            )
            run = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", command],
                env=env, capture_output=True, text=True, timeout=45)
            output = run.stdout + run.stderr
            self.assertNotEqual(run.returncode, 0, output)
            self.assertIn("Installed MCP module pair self-check failed", output)
            self.assertEqual((installed / "adt_mcp.py").read_bytes(), old_server)
            self.assertEqual((installed / "adt_discovery.py").read_bytes(), old_discovery)
            self.assertEqual(config.read_bytes(), original_config)
            self.assertFalse(list(installed.glob(".adt-stage-*")))
            self.assertTrue(list(installed.glob("adt_mcp.py.adt-backup-*")))
            self.assertTrue(list(installed.glob("adt_discovery.py.adt-backup-*")))

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
