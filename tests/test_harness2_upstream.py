"""Source-only checks for the opt-in unmodified Harness2 installer (no network)."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "integrations" / "harness2" / "install.sh"
UPSTREAM_SHA = "1cfe254e8d25b15f37048c3730134686abe60335"


@unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "POSIX Bash required; Windows Git Bash paths are unsupported")
class OriginalHarness2InstallerContract(unittest.TestCase):
    def invoke(self, *args: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "HOME": directory}
            return subprocess.run(
                ["bash", str(INSTALLER), *args],
                text=True, capture_output=True, check=False, timeout=10, env=env,
            )

    def test_installer_passes_bash_syntax_check(self):
        result = subprocess.run(
            ["bash", "-n", str(INSTALLER)],
            capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_help_does_not_install_or_run_models(self):
        result = self.invoke("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("pinned", result.stdout.lower())

    def test_status_without_checkout_fails_closed(self):
        result = self.invoke("status")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not installed", result.stderr)

    def test_remove_requires_explicit_confirmation(self):
        result = self.invoke("remove")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--confirm", result.stderr)

    def test_unknown_command_is_rejected(self):
        result = self.invoke("benchmark")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown command", result.stderr)

    def test_pinned_unmodified_upstream_not_demo(self):
        text = INSTALLER.read_text(encoding="utf-8")
        self.assertIn(UPSTREAM_SHA, text)
        self.assertIn("https://github.com/google-research/harness2.git", text)
        self.assertIn('git clone --no-checkout', text)
        self.assertIn('checkout --detach', text)
        self.assertNotIn("harness2-demo", text)
        self.assertNotIn("codex exec", text)
        self.assertNotIn("claude -p", text)


if __name__ == "__main__":
    unittest.main()
