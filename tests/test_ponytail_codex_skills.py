"""Offline tests: no real user skill directories and no Codex CLI invocations."""
import hashlib
import json
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

    def test_foreign_file_blocks_uninstall(self):
        self.run_action("install")
        (self.target / "ponytail" / "MY_FILE").write_text("keep")
        with self.assertRaisesRegex(host.Hold, "unexpected installed files"):
            self.run_action("uninstall")
        self.assertTrue((self.target / "ponytail" / "MY_FILE").exists())

    def test_source_symlink_refused(self):
        (self.source / "ponytail" / "SKILL.md").unlink()
        try:
            (self.source / "ponytail" / "SKILL.md").symlink_to(self.source / "ponytail-review" / "SKILL.md")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(host.Hold, "linked"):
            self.run_action("install")


if __name__ == "__main__":
    unittest.main()
