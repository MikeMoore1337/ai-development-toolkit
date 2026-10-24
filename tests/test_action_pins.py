"""Synthetic negative oracles for pinned GitHub Actions and CI dependencies."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_action_pins as action_pins  # noqa: E402


class ActionPinTests(unittest.TestCase):
    def test_all_workflows_have_reviewed_commit_pins(self):
        errors, count = action_pins.validate_directory(ROOT / ".github" / "workflows")
        self.assertEqual([], errors)
        self.assertGreaterEqual(count, 15)

    def test_reject_mutable_tag_short_sha_unknown_and_unreviewed_commit(self):
        for text, code in [
            ("- uses: actions/checkout@v7", "UNPINNED_ACTION"),
            ("- uses: actions/checkout@3d3c42", "UNPINNED_ACTION"),
            ("- uses: unknown/setup@{}" .format("a" * 40), "UNREVIEWED_ACTION_SHA"),
            ("- uses: actions/checkout@{}" .format("a" * 40), "UNREVIEWED_ACTION_SHA"),
            ("- uses: actions/checkout", "UNPINNED_ACTION"),
        ]:
            with self.subTest(text=text):
                errors, checked = action_pins.validate_text(text, "synthetic.yml")
                self.assertEqual(1, checked)
                self.assertTrue(any(code in value for value in errors))

    def test_known_hash_valid_but_local_actions_do_not_count_as_external(self):
        sample = "- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7\n- uses: ./local/action"
        self.assertEqual(([], 1), action_pins.validate_text(sample, "good.yml"))

    def test_empty_or_missing_workflow_dir_fails_closed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            errors, count = action_pins.validate_directory(path / "nope")
            self.assertEqual(0, count)
            self.assertIn("WORKFLOWS_MISSING", errors)
            (path / "workflows").mkdir()
            errors, _ = action_pins.validate_directory(path / "workflows")
            self.assertIn("WORKFLOWS_EMPTY", errors)

    def test_dev_dependency_is_fixed_and_binary_only_in_ci(self):
        self.assertEqual("PyYAML==6.0.3",
                         (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").strip())
        workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
        self.assertIn("--only-binary=:all: -r requirements-dev.txt", workflow)
        self.assertIn("python scripts/validate_action_pins.py", workflow)


if __name__ == "__main__":
    unittest.main()
