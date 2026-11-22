"""Offline tests: no real user skill directories and no Codex CLI invocations."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ponytail_codex_skills as host


class PonytailHostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.target = self.root / "home" / ".agents" / "skills"
        self.legacy = self.root / "home" / ".codex" / "skills"
        self.source.mkdir()
        blobs = {}
        for name in host.BLOBS:
            directory = self.source / name
            directory.mkdir()
            data = f"---\nname: {name}\n---\n".encode()
            (directory / "SKILL.md").write_bytes(data)
            blobs[name] = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        self.pin = patch.object(host, "BLOBS", blobs)
        self.pin.start()
        self.addCleanup(self.pin.stop)

    def run_action(self, action):
        return host.execute(action, source=self.source, destination=self.target, codex_root=self.legacy)

    def test_round_trip_and_idempotency(self):
        self.assertEqual("NOT_INSTALLED", self.run_action("status"))
        self.assertEqual("INSTALLED", self.run_action("install"))
        self.assertEqual("ALREADY_INSTALLED", self.run_action("install"))
        self.assertEqual("INSTALLED", self.run_action("status"))
        self.assertEqual(host.PIN, json.loads((self.target / host.MARKER).read_text())["commit"])
        self.assertEqual("UNINSTALLED", self.run_action("uninstall"))
        self.assertEqual("NOT_INSTALLED", self.run_action("status"))

    def test_conflict_does_not_overwrite(self):
        name = next(iter(host.BLOBS))
        dest = self.target / name
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text("other source")
        with self.assertRaisesRegex(host.Hold, "unowned skill collision"):
            self.run_action("install")
        self.assertEqual("other source", (dest / "SKILL.md").read_text())

    def test_unfinished_staging_blocks_status_and_install(self):
        stage = self.target / ".adt-ponytail-stage-interrupted"
        stage.mkdir(parents=True)
        (stage / "foreign.txt").write_text("keep")
        for action in ("status", "install"):
            with self.subTest(action=action), self.assertRaisesRegex(host.Hold, "unfinished staging"):
                self.run_action(action)
        self.assertEqual("keep", (stage / "foreign.txt").read_text())

    def test_legacy_duplicate_blocks_install(self):
        (self.legacy / "ponytail").mkdir(parents=True)
        with self.assertRaisesRegex(host.Hold, "possible duplicate"):
            self.run_action("install")

    def test_source_integrity_gate(self):
        (self.source / "ponytail" / "SKILL.md").write_text("modified")
        with self.assertRaisesRegex(host.Hold, "Git blob SHA mismatch"):
            self.run_action("install")
        self.assertFalse(self.target.exists())

    def test_changed_install_blocks_uninstall(self):
        self.run_action("install")
        (self.target / "ponytail" / "SKILL.md").write_text("modified")
        with self.assertRaisesRegex(host.Hold, "installed skill changed"):
            self.run_action("uninstall")
        self.assertTrue((self.target / host.MARKER).exists())

    def test_partial_uninstall_fails_closed(self):
        self.run_action("install")
        unlink = Path.unlink
        calls = 0

        def fail_on_second(file, *args, **kwargs):
            nonlocal calls
            if file.name == "SKILL.md":
                calls += 1
                if calls == 2:
                    raise OSError("simulated failure")
            return unlink(file, *args, **kwargs)

        with patch.object(Path, "unlink", new=fail_on_second):
            with self.assertRaises(OSError):
                self.run_action("uninstall")
        for action in ("status", "uninstall"):
            with self.subTest(action=action), self.assertRaisesRegex(host.Hold, "incomplete"):
                self.run_action(action)
        self.assertTrue((self.target / "ponytail-review" / "SKILL.md").is_file())
        self.assertTrue((self.target / host.MARKER).is_file())

    def test_foreign_file_blocks_uninstall(self):
        self.run_action("install")
        (self.target / "ponytail" / "MY_FILE").write_text("keep")
        with self.assertRaisesRegex(host.Hold, "unexpected installed files"):
            self.run_action("uninstall")
        self.assertTrue((self.target / "ponytail" / "MY_FILE").exists())

    def test_failed_install_does_not_delete_foreign_file(self):
        rename = os.rename
        calls = 0

        def fail_after_foreign_file(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                (self.target / "ponytail" / "MY_FILE").write_text("keep")
                raise OSError("simulated failure")
            rename(source, destination)

        with patch.object(host.os, "rename", side_effect=fail_after_foreign_file):
            with self.assertRaises(OSError):
                self.run_action("install")
        self.assertEqual("keep", (self.target / "ponytail" / "MY_FILE").read_text())

    def test_failed_install_removes_unchanged_files(self):
        rename = os.rename
        calls = 0

        def fail_on_second(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated failure")
            rename(source, destination)

        with patch.object(host.os, "rename", side_effect=fail_on_second):
            with self.assertRaises(OSError):
                self.run_action("install")
        self.assertEqual("NOT_INSTALLED", self.run_action("status"))

    def test_failed_install_preserves_foreign_file_in_stage(self):
        def fail_with_foreign_file(source, destination):
            (source.parent / "foreign.txt").write_text("keep")
            raise OSError("simulated failure")

        with patch.object(host.os, "rename", side_effect=fail_with_foreign_file):
            with self.assertRaises(OSError):
                self.run_action("install")
        stages = list(self.target.glob(".adt-ponytail-stage-*"))
        self.assertEqual(1, len(stages))
        self.assertEqual("keep", (stages[0] / "foreign.txt").read_text())

    def test_source_symlink_refused(self):
        (self.source / "ponytail" / "SKILL.md").unlink()
        try:
            (self.source / "ponytail" / "SKILL.md").symlink_to(self.source / "ponytail-review" / "SKILL.md")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(host.Hold, "linked"):
            self.run_action("install")

    def test_linked_destination_ancestor_refused(self):
        linked = host.linked
        with patch.object(host, "linked", side_effect=lambda path: path == self.root / "home" or linked(path)):
            with self.assertRaisesRegex(host.Hold, "symlink or junction"):
                self.run_action("install")
        self.assertFalse(self.target.exists())

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_real_junction_ancestor_refused(self):
        home = self.root / "home"
        home.mkdir()
        junction = self.root / "junction"
        result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(home)],
                                capture_output=True, text=True, check=False)
        if result.returncode:
            self.skipTest("Windows junction creation unavailable")
        try:
            with self.assertRaisesRegex(host.Hold, "symlink or junction"):
                host.execute("install", source=self.source, destination=junction / ".agents" / "skills",
                             codex_root=self.legacy)
            self.assertFalse((home / ".agents").exists())
        finally:
            junction.rmdir()


if __name__ == "__main__":
    unittest.main()
