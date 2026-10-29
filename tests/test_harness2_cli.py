"""Source-only smoke contracts for the original Harness2 CLI bridge."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "integrations" / "harness2" / "cli.sh"


class OriginalCliBridgeTests(unittest.TestCase):
    def test_exact_pin_and_no_model_execution(self):
        data = TOOL.read_text(encoding="utf-8")
        self.assertIn("1cfe254e8d25b15f37048c3730134686abe60335", data)
        self.assertIn('"$BIN/harness2-check"', data)
        self.assertIn('"$BIN/harness2-report"', data)
        self.assertIn('"$BIN/harness2-setup"', data)
        self.assertIn("--dry-run", data)
        self.assertNotIn('exec "$BIN/harness2-judge"', data)
        self.assertNotIn('exec "$BIN/harness2" "$@"', data)

    def test_artifact_discovery_uses_original_upstream_runs_dir_not_fork(self):
        source = TOOL.read_text(encoding="utf-8")
        self.assertIn("from harness2 import config; print(config.RUNS)", source)
        self.assertIn("HARNESS2_RUNS_DIR", source)
        self.assertIn("runs_root", source)
        self.assertNotIn('find -P "$SRC/runs"', source)
        self.assertIn("upstream runs root must be inside user home", source)
        self.assertIn('find -P "$runs_root"', source)

    @unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "POSIX Bash required")
    def test_syntax_help_no_install_and_refusal(self):
        result = subprocess.run(["bash", "-n", str(TOOL)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp}
            help_result = subprocess.run(["bash", str(TOOL), "--help"], env=env,
                                         capture_output=True, text=True, timeout=10)
            self.assertEqual(help_result.returncode, 0)
            for action in ("status", "check", "setup", "report", "run"):
                result = subprocess.run(["bash", str(TOOL), action], env=env,
                                        capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("not installed", result.stderr)


if __name__ == "__main__":
    unittest.main()
