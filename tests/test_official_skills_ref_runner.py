"""Negative tests for fail-closed official CLI invocation (offline, mocked CLI)."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("official_runner", ROOT / "scripts" / "validate_with_skills_ref.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def make_pack(tmp: Path, *, broken: bool = False) -> None:
    (tmp / ".agents" / "skills" / "good-skill").mkdir(parents=True)
    (tmp / ".agents" / "skills" / "good-skill" / "SKILL.md").write_text(
        "---\nname: good-skill\ndescription: A useful test skill.\n---\n", encoding="utf-8"
    )
    qa = tmp / "extensions" / "qa" / "skills" / "qa-skill"
    qa.mkdir(parents=True)
    (qa / "SKILL.md").write_text(
        "---\nname: qa-skill\ndescription: QA skill.\n---\n", encoding="utf-8"
    )
    mf = tmp / "extensions" / "make-feature" / "skills" / "make-feature"
    mf.mkdir(parents=True)
    (mf / "SKILL.md").write_text(
        "---\nname: make-feature\ndescription: Feature delivery.\n---\n", encoding="utf-8"
    )
    manifest = {
        "core_skills": ["good-skill"], "extension_skills": [],
        "original_skills_bundled_as_opt_in": 0,
        "extension_packs": {
            "qa": {"skill_root": "extensions/qa/skills", "skills": ["qa-skill"]},
            "make-feature": {
                "skill_root": "extensions/make-feature/skills", "skills": ["make-feature"]
            },
        },
    }
    (tmp / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    if broken:
        (mf / "SKILL.md").unlink()


class OfficialRunnerTests(unittest.TestCase):
    def test_all_extension_packs_invoked_and_counted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_pack(root)
            visited = []
            def fake_run(cmd, **kwargs):
                visited.append(Path(cmd[-1]).name)
                return subprocess.CompletedProcess(cmd, 0, f"Valid skill: {cmd[-1]}\n", "")
            with patch.object(runner.shutil, "which", return_value="/fake/skills-ref"), \
                 patch.object(runner.subprocess, "run", side_effect=fake_run):
                self.assertEqual(0, runner.run(root=root))
            self.assertEqual({"good-skill", "qa-skill", "make-feature"}, set(visited))
            self.assertEqual(3, len(visited))

    def test_missing_validator_fails_without_invocation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_pack(root)
            with patch.object(runner.shutil, "which", return_value=None), \
                 patch.object(runner.subprocess, "run") as invoke:
                self.assertEqual(2, runner.run(root=root))
                invoke.assert_not_called()

    def test_nonzero_exit_fails(self):
        self.assert_failure(subprocess.CompletedProcess([], 1, "", "Invalid YAML"))

    def test_noop_zero_exit_without_success_line_fails(self):
        self.assert_failure(subprocess.CompletedProcess([], 0, "", ""))

    def test_wrong_success_line_fails(self):
        self.assert_failure(subprocess.CompletedProcess([], 0, "Valid skill: ignored\n", ""))

    def test_timeout_fails(self):
        self.assert_failure(subprocess.TimeoutExpired(cmd="skills-ref", timeout=0.01))

    def test_execution_error_fails(self):
        self.assert_failure(OSError("permission denied"))

    def assert_failure(self, outcome):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_pack(root)
            with patch.object(runner.shutil, "which", return_value="/fake/skills-ref"), \
                 patch.object(runner.subprocess, "run", side_effect=outcome if isinstance(outcome, Exception) else None,
                              return_value=None if isinstance(outcome, Exception) else outcome):
                self.assertEqual(1, runner.run(root=root))

    def test_missing_declared_skill_file_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_pack(root, broken=True)
            with self.assertRaises(FileNotFoundError):
                runner.skill_directories(root)

    def test_unlisted_skill_directory_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_pack(root)
            (root / "extensions" / "qa" / "skills" / "forgotten").mkdir()
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                runner.skill_directories(root)

    def test_removed_pack_skill_from_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_pack(root)
            manifest_path = root / "MANIFEST.json"
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["extension_packs"]["qa"]["skills"] = []
            manifest_path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                runner.skill_directories(root)

    def test_real_manifest_contains_all_declared_packs(self):
        paths = runner.skill_directories(ROOT)
        self.assertEqual(76, len(paths))
        self.assertEqual(23, sum(".agents/skills/" in p.as_posix() for p in paths))
        self.assertEqual(27, sum("extensions/qa/" in p.as_posix() for p in paths))
        self.assertEqual(1, sum("extensions/make-feature/" in p.as_posix() for p in paths))
        self.assertEqual(5, sum("extensions/frontend/" in p.as_posix() for p in paths))
        self.assertEqual(6, sum("extensions/backend/" in p.as_posix() for p in paths))
        self.assertEqual(3, sum("extensions/fullstack/" in p.as_posix() for p in paths))
        self.assertEqual(1, sum("extensions/product/" in p.as_posix() for p in paths))
        self.assertEqual(1, sum("extensions/design/" in p.as_posix() for p in paths))
        self.assertEqual(1, sum("extensions/performance/" in p.as_posix() for p in paths))


if __name__ == "__main__":
    unittest.main()
