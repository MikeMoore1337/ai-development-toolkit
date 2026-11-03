"""Offline fail-closed contract for the opt-in WSL2 Harness2 acceptance entrypoint."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "integrations" / "harness2" / "acceptance.ps1"
PREFLIGHT = ROOT / "integrations" / "harness2" / "preflight.sh"
ATTRIBUTES = ROOT / ".gitattributes"
UPSTREAM_SHA = "1cfe254e8d25b15f37048c3730134686abe60335"


class Harness2WindowsAcceptanceContract(unittest.TestCase):
    def test_only_invokes_existing_upstream_bridge(self):
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("$installer = \"$sourceDirectory/install.sh\"", script)
        self.assertIn("$bridge = \"$sourceDirectory/cli.sh\"", script)
        self.assertIn("Invoke-WSLChecked", script)
        self.assertIn("wslpath -a $PSCommandPath", script)
        self.assertIn("$preflightScript = \"$sourceDirectory/preflight.sh\"", script)
        self.assertIn("Invoke-WSLChecked -Arguments @('bash', $preflightScript)", script)
        self.assertIn("MODEL_EXECUTION=DISABLED", PREFLIGHT.read_text(encoding="utf-8"))
        self.assertNotIn("bash', '-c'", script)
        self.assertNotIn("$preflight = @'", script)
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
        preflight = PREFLIGHT.read_text(encoding="utf-8")
        self.assertIn("grep -qi microsoft /proc/sys/kernel/osrelease", preflight)
        self.assertIn('[[ "$(id -u)" != 0 ]]', preflight)
        self.assertIn("command -v python3.12", preflight)
        self.assertIn("command -v git", preflight)
        self.assertIn("if ($Action -eq 'Preflight')", script)
        self.assertIn("UV=MISSING_FOR_SETUP", preflight)
        self.assertIn("NPM=MISSING_FOR_SETUP", preflight)

    def test_default_distribution_is_auto_detected_without_docker(self):
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("[string]$Distribution = 'auto'", script)
        self.assertIn("wsl.exe --list --quiet", script)
        self.assertIn("HARNESS2_UBUNTU_DISTRO_MISSING", script)
        self.assertIn("HARNESS2_DOCKER_INTERNAL_DISTRO_REFUSED", script)
        self.assertIn("HARNESS2_WSL_DISTRO_NOT_FOUND", script)
        self.assertIn("HARNESS2_WSL_DISTRIBUTION=", script)

    def test_preflight_is_checked_in_and_lf_only(self):
        self.assertTrue(PREFLIGHT.is_file())
        script = PREFLIGHT.read_bytes()
        self.assertNotIn(b"\r", script)
        self.assertTrue(script.startswith(b"#!/usr/bin/env bash\n"))
        self.assertIn("integrations/harness2/*.sh text eol=lf",
                      ATTRIBUTES.read_text(encoding="utf-8"))

    # Git Bash from Windows Python cannot reliably parse a native drive path.
    # Ubuntu/macOS validate Bash syntax; Windows separately tests PowerShell/WSL argv.
    @unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "POSIX Bash required for shell syntax test")
    def test_bash_preflight_syntax(self):
        result = subprocess.run(["bash", "-n", str(PREFLIGHT)],
                                text=True, capture_output=True, check=False, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(
        os.name == "posix" and shutil.which("bash") and shutil.which("python3.12")
        and hasattr(os, "geteuid") and os.geteuid() != 0,
        "Unprivileged POSIX Bash and Python 3.12 required",
    )
    def test_native_node_required_even_if_npm_is_on_path(self):
        # WSL inherits Windows npm from /mnt/c, but npm alone is not usable.
        with tempfile.TemporaryDirectory() as directory:
            binaries = Path(directory) / "bin"
            binaries.mkdir()
            for name in ("id", "git", "python3.12"):
                executable = shutil.which(name)
                self.assertIsNotNone(executable, name)
                (binaries / name).symlink_to(executable)
            grep = binaries / "grep"
            grep.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            grep.chmod(0o755)
            npm = binaries / "npm"
            npm.write_text("#!/bin/sh\necho 11.19.1\n", encoding="utf-8")
            npm.chmod(0o755)
            env = {**os.environ, "PATH": str(binaries)}
            command = [shutil.which("bash"), str(PREFLIGHT)]
            missing_node = subprocess.run(
                command, env=env, capture_output=True, text=True, timeout=10,
                check=False,
            )
            self.assertEqual(missing_node.returncode, 0, missing_node.stderr)
            self.assertIn("NPM=MISSING_FOR_SETUP", missing_node.stdout)

            node = binaries / "node"
            node.write_text("#!/bin/sh\necho v24.22.2\n", encoding="utf-8")
            node.chmod(0o755)
            native_node = subprocess.run(
                command, env=env, capture_output=True, text=True, timeout=10,
                check=False,
            )
            self.assertEqual(native_node.returncode, 0, native_node.stderr)
            self.assertIn("NPM=PRESENT", native_node.stdout)

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"), "Windows PowerShell required")
    def test_windows_wsl_auto_discovery_and_missing_distro_with_stub(self):
        # A function shadowing wsl.exe exercises Windows PowerShell 5.1 command
        # discovery and NUL-separated output without launching a real distro.
        environment = {**os.environ, "HARNESS2_ACCEPTANCE_PS1": str(SCRIPT)}
        mock = r"""
function global:wsl.exe {
    if ($args.Count -ge 1 -and $args[0] -eq '--list') {
        Write-Output 'docker-desktop'
        if ($env:HARNESS2_TEST_DISTRO) {
            Write-Output ($env:HARNESS2_TEST_DISTRO.ToCharArray() -join [char]0)
        }
        $global:LASTEXITCODE = 0
        return
    }
    if ($args[0] -eq '--distribution' -and $args[2] -eq '--exec') {
        if ($args[3] -eq 'wslpath' -and $args[4] -eq '-a') {
            Write-Output '/mnt/d/toolkit/integrations/harness2/acceptance.ps1'
        } elseif ($args.Count -eq 5 -and $args[3] -eq 'bash' -and
                  $args[4] -eq '/mnt/d/toolkit/integrations/harness2/preflight.sh') {
            Write-Output ('MOCK_DISTRO=' + $args[1])
            Write-Output 'HARNESS2_WSL2=READY'
            Write-Output 'MODEL_EXECUTION=DISABLED'
        } else {
            throw 'UNEXPECTED_WSL_COMMAND'
        }
        $global:LASTEXITCODE = 0
        return
    }
    throw 'UNEXPECTED_WSL_CALL'
}
try {
    & $env:HARNESS2_ACCEPTANCE_PS1 -Action Preflight
    exit 0
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 10
}
"""
        command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", mock]
        valid = subprocess.run(
            command, text=True, capture_output=True, check=False, timeout=20,
            env={**environment, "HARNESS2_TEST_DISTRO": "Ubuntu-24.04"},
        )
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertIn("HARNESS2_WSL_DISTRIBUTION=Ubuntu-24.04", valid.stdout)
        self.assertIn("MOCK_DISTRO=Ubuntu-24.04", valid.stdout)

        missing = subprocess.run(
            command, text=True, capture_output=True, check=False, timeout=20,
            env={**environment, "HARNESS2_TEST_DISTRO": ""},
        )
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("HARNESS2_UBUNTU_DISTRO_MISSING", missing.stderr)
        self.assertNotIn("MOCK_DISTRO=", missing.stdout)

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
        # Localized PowerShell 5.1 errors may use the console code page rather
        # than UTF-8; keep ASCII fail-closed markers readable in either case.
        denied = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(SCRIPT), "-Action", "Setup", "-Benchmark", "lab"],
            text=True, capture_output=True, errors="replace",
            check=False, timeout=20, env=environment,
        )
        self.assertNotEqual(denied.returncode, 0)
        self.assertIn("HARNESS2_SETUP_REQUIRES_NETWORK_CONFIRMATION", denied.stderr)


if __name__ == "__main__":
    unittest.main()
