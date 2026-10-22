"""Read-only adoption preflight across empty, existing and conflicting projects."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import adt
import project_adoption_preflight as adoption


def snapshot(root: Path) -> dict:
    result = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink() or p.is_junction():
            result[rel] = ("link",)
        elif p.is_file():
            result[rel] = ("file", hashlib.sha256(p.read_bytes()).hexdigest())
        else:
            result[rel] = ("directory",)
    return result


class ProjectAdoptionTests(unittest.TestCase):
    def setUp(self):
        context = tempfile.TemporaryDirectory()
        self.addCleanup(context.cleanup)
        self.target = Path(context.name) / "project"
        self.target.mkdir()
        self.manifest = adt.manifest_data()

    def report(self, *, task="qa", layout="codex", archetype="generic"):
        return adoption.inspect(self.target, layout, task, archetype,
                                manifest=self.manifest)

    def test_empty_project_is_read_only_and_not_an_installed_client(self):
        before = snapshot(self.target)
        report = self.report()
        self.assertEqual(before, snapshot(self.target))
        self.assertEqual("READY_FOR_HUMAN_REVIEW", report["result"])
        self.assertEqual("NOT_TESTED", report["client_skill_discovery_L4"])
        self.assertEqual("NOT_TESTED", report["client_skill_use_L5"])
        self.assertEqual("NOT_TESTED", report["client_task_benefit_L6"])
        self.assertFalse(report["marker_contents_read"])
        self.assertEqual("NOT_REQUESTED", report["installation"])
        self.assertTrue(report["proposed_skills"])
        self.assertFalse((self.target / ".adt").exists())

    def test_existing_project_policy_bytes_not_read_or_changed(self):
        sentinel = b"PRIVATE_PROJECT_RULES_8476_TOKEN_DO_NOT_DISCLOSE\n"
        (self.target / "AGENTS.md").write_bytes(sentinel)
        (self.target / "README.md").write_text("# Project", encoding="utf-8")
        (self.target / "pyproject.toml").write_text("[project]\nname='sample'\n",
                                                    encoding="utf-8")
        before = snapshot(self.target)
        for archetype in adoption.ARCHETYPES:
            with self.subTest(archetype=archetype):
                report = self.report(task="backend", archetype=archetype)
                self.assertEqual(before, snapshot(self.target))
                self.assertEqual("PRESENT_UNREAD", report["observed_marker_names_only"]["AGENTS.md"])
                self.assertEqual("REQUIRED", report["source_of_truth_review"])
                self.assertNotIn("PRIVATE_PROJECT_RULES_8476", json.dumps(report))
                self.assertEqual(archetype, report["archetype"])
                self.assertTrue(report["archetype_is_user_declared"])

    def test_user_owned_skill_collision_blocks_without_ownership_claim(self):
        selected = adt.choose(self.target, self.manifest, None, "feature")
        name = selected["skills"][0]
        own = self.target / ".agents" / "skills" / name
        own.mkdir(parents=True)
        (own / "SKILL.md").write_text("user-owned and should remain", encoding="utf-8")
        before = snapshot(self.target)
        result = self.report(task="feature")
        self.assertEqual(before, snapshot(self.target))
        self.assertEqual("BLOCKED", result["result"])
        self.assertIn(name, result["conflicts"])
        self.assertIn(name, result["user_owned_skills"])
        self.assertFalse((self.target / ".adt").exists())

    def test_other_client_layout_is_not_assumed(self):
        (self.target / "CLAUDE.md").write_text("do not change", encoding="utf-8")
        before = snapshot(self.target)
        result = self.report(layout="claude", task="qa", archetype="hermes")
        self.assertEqual(before, snapshot(self.target))
        self.assertEqual("claude", result["client_layout"])
        self.assertTrue(any("CLAUDE.md" in s for s in result["warnings"]))
        self.assertEqual("NOT_TESTED", result["client_skill_discovery_L4"])

    def test_missing_project_fails_closed(self):
        target = self.target / "not-a-project"
        result = adoption.inspect(target, "codex", "qa", "generic", manifest=self.manifest)
        self.assertEqual("BLOCKED", result["result"])
        self.assertIsNone(result["selected_profile"])
        self.assertEqual([], result["proposed_skills"])

    def test_invalid_archetype_client_and_task_rejected(self):
        for changes in (("unknown", "codex", "qa"),
                        ("generic", "chatgpt", "qa"),
                        ("generic", "codex", "external-script")):
            with self.subTest(changes=changes):
                with self.assertRaises(adoption.AdoptionError):
                    adoption.inspect(self.target, changes[1], changes[2],
                                     changes[0], manifest=self.manifest)

    def test_cli_json_no_project_policy_leak_and_no_writes(self):
        secret = "SECRET_NEVER_LEAK_23"
        (self.target / "AGENTS.md").write_text(secret, encoding="utf-8")
        before = snapshot(self.target)
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = adoption.main(["--target", str(self.target), "--task", "backend",
                                  "--archetype", "second-brain"])
        self.assertEqual(0, code, stderr.getvalue())
        self.assertEqual(before, snapshot(self.target))
        self.assertNotIn(secret, stdout.getvalue() + stderr.getvalue())
        self.assertEqual("second-brain", json.loads(stdout.getvalue())["archetype"])
        self.assertFalse((self.target / ".adt").exists())

    def test_linked_governance_marker_blocks_if_supported(self):
        source = self.target / "actual.md"
        source.write_text("private", encoding="utf-8")
        alias = self.target / "AGENTS.md"
        try:
            alias.symlink_to(source)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink unavailable on this environment")
        before = snapshot(self.target)
        result = self.report()
        self.assertEqual("BLOCKED", result["result"])
        self.assertEqual("UNSAFE_LINK", result["observed_marker_names_only"]["AGENTS.md"])
        self.assertEqual(before, snapshot(self.target))


if __name__ == "__main__":
    unittest.main()
