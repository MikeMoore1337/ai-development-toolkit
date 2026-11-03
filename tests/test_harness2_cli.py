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
        self.assertIn('realpath -m -- "$runs_root"', source)
        self.assertIn('find -P "$canonical_runs"', source)

    @unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "POSIX Bash required")
    def test_artifact_listing_rejects_symlink_parent_escape(self):
        # Offline fixture exercises Toolkit path confinement, not an upstream model.
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            root = home / ".local" / "share" / "ai-development-toolkit" / (
                "harness2-1cfe254e8d25b15f37048c3730134686abe60335"
            )
            (root / "source").mkdir(parents=True)
            bin_dir = root / ".venv" / "bin"
            bin_dir.mkdir(parents=True)
            (root / ".adt-original-harness2").write_text(
                "1cfe254e8d25b15f37048c3730134686abe60335\n", encoding="utf-8",
            )
            for exe in ("harness2-setup", "harness2-check", "harness2",
                        "harness2-judge", "harness2-report"):
                script = bin_dir / exe
                script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                script.chmod(0o755)
            py_stub = bin_dir / "python"
            py_stub.write_text(
                '#!/bin/sh\ncase "$*" in *"from harness2 import config"*) '
                'printf "%s\\n" "$HARNESS2_RUNS_DIR";; esac\n',
                encoding="utf-8",
            )
            py_stub.chmod(0o755)
            fake_bin = base / "mock-bin"
            fake_bin.mkdir()
            fake_git = fake_bin / "git"
            fake_git.write_text(
                '#!/bin/sh\nif [ "$3" = rev-parse ]; then '
                'echo 1cfe254e8d25b15f37048c3730134686abe60335; '
                'elif [ "$3" = remote ]; then '
                'echo https://github.com/google-research/harness2.git; fi\n',
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            env = {**os.environ, "HOME": str(home),
                   "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"}

            safe = home / "real-runs"
            safe.mkdir()
            (safe / "judged.json").write_text("{}", encoding="utf-8")
            ok = subprocess.run(
                ["bash", str(TOOL), "artifacts"],
                env={**env, "HARNESS2_RUNS_DIR": str(safe)},
                text=True, capture_output=True, check=False, timeout=10,
            )
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertIn(str(safe / "judged.json"), ok.stdout)

            outside = base / "outside"
            target = outside / "run1"
            target.mkdir(parents=True)
            (target / "judged.json").write_text("{}", encoding="utf-8")
            (home / "alias").symlink_to(outside, target_is_directory=True)
            escaped = subprocess.run(
                ["bash", str(TOOL), "artifacts"],
                env={**env, "HARNESS2_RUNS_DIR": str(home / "alias" / "run1")},
                text=True, capture_output=True, check=False, timeout=10,
            )
            self.assertNotEqual(escaped.returncode, 0, escaped.stdout)
            self.assertIn("HARNESS2_REFUSED", escaped.stderr)

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
