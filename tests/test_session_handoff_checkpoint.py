"""#374 local-only session checkpoint security regression tests."""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "session_handoff_checkpoint.py"
spec = importlib.util.spec_from_file_location("session_handoff_checkpoint", MODULE_PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ISSUE = "https://github.com/MikeMoore1337/ai-development-toolkit/issues/374"


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        def git(*args):
            subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)
        git("init", "-b", "main")
        git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "--allow-empty", "-m", "baseline")

    def test_round_trip(self):
        p = m.make_packet(self.root, ISSUE)
        self.assertEqual(m.verify_packet(self.root, p)["decision"], "PASS")
        self.assertNotIn(str(self.root), str(p))

    def test_change_head_is_stale(self):
        p = m.make_packet(self.root, ISSUE)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "--allow-empty", "-m", "new"], check=True, capture_output=True)
        self.assertEqual(m.verify_packet(self.root, p)["reason"], "commit")

    def test_change_dirty_status_is_stale(self):
        p = m.make_packet(self.root, ISSUE)
        (self.root / "tracked.txt").write_text("one")
        subprocess.run(["git", "-C", str(self.root), "add", "tracked.txt"], check=True, capture_output=True)
        self.assertEqual(m.verify_packet(self.root, p)["decision"], "STALE")

    def test_forged_repo_is_blocked(self):
        p = m.make_packet(self.root, ISSUE)
        p["repo_id"] = "f" * 64
        self.assertEqual(m.verify_packet(self.root, p)["reason"], "repo_id")

    def test_invalid_issue_fails(self):
        with self.assertRaises(ValueError):
            m.make_packet(self.root, "https://private.local/token")

    def test_malformed_packet_fails_closed(self):
        self.assertEqual(m.verify_packet(self.root, {"schema": 1})["decision"], "BLOCKED")

    def test_no_chat_raw_metadata(self):
        p = m.make_packet(self.root, ISSUE)
        self.assertEqual(set(p), {"schema", "source", "issue_url", "repo_id", "branch", "commit", "status_sha256", "dirty"})


if __name__ == "__main__":
    unittest.main()
