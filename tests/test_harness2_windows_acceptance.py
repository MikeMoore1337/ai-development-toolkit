"""Offline fail-closed contract for the opt-in WSL2 Harness2 acceptance entrypoint."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "integrations" / "harness2" / "acceptance.ps1"
UPSTREAM_SHA = "1cfe254e8d25b15f37048c3730134686abe60335"


class Harness2WindowsAcceptanceContract(unittest.TestCase):
    def test_only_invokes_existing_upstream_bridge(self):
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("$installer = \"$sourceDirectory/install.sh\"", script)
        self.assertIn("$bridge = \"$sourceDirectory/cli.sh\"", script)
        self.assertIn("Invoke-WSLChecked", script)
        self.assertIn("wslpath -a $PSCommandPath", script)
        self.assertIn("MODEL_EXECUTION=DISABLED", script)
        self.assertNotIn("harness2-demo", script)
        for unsafe in ("Invoke-Expression", "iex ", "codex exec", "claude -p", "harness2-judge"):
            self.assertNotIn(unsafe, script)

    def test_setup_is_explicitly_confirmed_before_any_process(self):
        script = SCRIPT.read_text(encoding="utf-8")
        gate = script.index("HARNESS2_SETUP_REQUIRES_NETWORK_CONFIRMATION")
        wsl = script.index("Get-Command wsl.exe")
        self.assertLess(gate, wsl)
        self.assertIn("'--confirm-network-downloads'", script)
        self.assertIn("HARNESS2_UNEXPECTED_NETWORK_CONFIRMATION", script)
        self.assertIn("HARNESS2_REMOVE_REQUIRES_CONFIRMATION", script)
        self.assertIn("'remove', '--confirm'", script)
        self.assertIn("[ValidateSet('lab', 'jb', 'wb')]", script)
        self.assertIn("[ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')]", script)

    def test_preflight_is_read_only_and_requires_unprivileged_wsl2_python312(self):
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("grep -qi microsoft /proc/sys/kernel/osrelease", script)
        self.assertIn('[[ "$(id -u)" != 0 ]]', script)
        self.assertIn("command -v python3.12", script)
        self.assertIn("command -v git", script)
        self.assertIn("if ($Action -eq 'Preflight')", script)
        self.assertIn("UV=MISSING_FOR_SETUP", script)
        self.assertIn("NPM=MISSING_FOR_SETUP", script)

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"), "Windows PowerShell required")
    def test_native_powershell_parser_and_setup_rejection(self):
        # Parse the complete script rather than rely on a Linux-only string fixture.
        environment = {**os.environ, "HARNESS2_ACCEPTANCE_PS1": str(SCRIPT)}
        cmd = (
            "$tokens=$null; $errors=$null; "
            "[System.Management.Automation.Language.Parser]::ParseFile("
            "$env:HARNESS2_ACCEPTANCE_PS1,[ref]$tokens,[ref]$errors) | Out-Null; "
            "if ($errors.Count -ne 0) { $errors | Out-String | Write-Error; exit 1 }"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", cmd],
            text=True, capture_output=True, check=False, timeout=20, env=environment,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        denied = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(SCRIPT), "-Action", "Setup", "-Benchmark", "lab"],
            text=True, capture_output=True, check=False, timeout=20, env=environment,
        )
        self.assertNotEqual(denied.returncode, 0)
        self.assertIn("HARNESS2_SETUP_REQUIRES_NETWORK_CONFIRMATION", denied.stderr)


if __name__ == "__main__":
    unittest.main()
