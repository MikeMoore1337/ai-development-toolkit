"""Offline contract for IDE-local-first and optional-URL agent onboarding (#52/#95).

This checks actual managed CLI behavior in disposable target folders, not a live
Codex/Claude session, URL retrieval or empirical model effectiveness.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN = ROOT / "AGENT_START.md"
RU = ROOT / "AGENT_START.ru.md"
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/adt.py"), "--json", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )


class UniversalAgentEntryTests(unittest.TestCase):
    def test_source_and_target_discovery_for_both_languages(self):
        for guide in (EN, RU):
            text = guide.read_text(encoding="utf-8")
            self.assertIn("https://github.com/MikeMoore1337/ai-development-toolkit", text)
            self.assertIn("https://github.com/OWNER/PROJECT", text)  # optional remote path
            self.assertIn("AGENTS.md", text)
            self.assertIn("CLAUDE.md", text)
            self.assertIn("MANIFEST.json", text)
            self.assertIn("docs/INSTALLATION.md", text)
            self.assertIn("AGENT_START", text)

    def test_one_entry_link_in_each_main_readme(self):
        self.assertIn("(AGENT_START.md)", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn("(AGENT_START.ru.md)", (ROOT / "README.ru.md").read_text(encoding="utf-8"))
        self.assertIn("(AGENT_START.ru.md)", EN.read_text(encoding="utf-8"))
        self.assertIn("(AGENT_START.md)", RU.read_text(encoding="utf-8"))

    def test_existing_profile_and_client_layout_contract(self):
        for name in ("general", "codex-feature", "qa-security", "ui-fix", "frontend",
                     "backend", "fullstack", "qa-core", "make-feature"):
            self.assertIn(name, MANIFEST["profiles"])
        for guide in (EN, RU):
            text = guide.read_text(encoding="utf-8")
            for token in ("--task feature", "--apply", "--layout claude",
                          "feature-delivery", "make-feature", "qa-all",
                          "NOT_TESTED", "NOT_RUN", "BLOCKED"):
                self.assertIn(token, text)

    def test_profile_preview_is_read_only_and_task_driven(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            before = list(target.rglob("*"))
            result = run_cli("profile", "plan", "--target", directory, "--task", "feature")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["selection"]["profile"], "codex-feature")
            self.assertFalse(report["applied"])
            self.assertIn(report["result"], ("PREVIEW", "REVIEW_REQUIRED"))
            self.assertEqual(before, list(target.rglob("*")))

    def test_unmanaged_skill_is_not_overwritten_even_on_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / ".agents" / "skills" / "task-scoping"
            folder.mkdir(parents=True)
            original = folder / "SKILL.md"
            original.write_text("user-owned; do not overwrite", encoding="utf-8")
            result = run_cli("init", "--target", directory, "--task", "feature", "--apply")
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["result"], "BLOCKED")
            self.assertFalse(report["applied"])
            self.assertEqual(original.read_text(encoding="utf-8"), "user-owned; do not overwrite")

    def test_repeat_install_is_idempotent_in_disposable_target(self):
        with tempfile.TemporaryDirectory() as directory:
            first = run_cli("init", "--target", directory, "--task", "feature", "--apply")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue(json.loads(first.stdout)["applied"])
            second = run_cli("init", "--target", directory, "--task", "feature", "--apply")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)["result"], "ALREADY_INSTALLED")
            status = run_cli("status", "--target", directory)
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertTrue((Path(directory) / ".agents" / "skills" / "task-scoping" / "SKILL.md").is_file())

    def test_does_not_claim_runtime_activation(self):
        for guide in (EN, RU):
            text = guide.read_text(encoding="utf-8")
            self.assertIn("NOT_TESTED", text)
            self.assertIn("NOT_VERIFIED", text)
            self.assertIn("Python 3.12+", text)
            self.assertIn("ChatGPT", text)
            self.assertIn("Claude Code", text)


    def test_beginner_acceptance_links_and_human_status(self):
        protocol = (ROOT / "docs/ru/ACCEPTANCE.md").read_text(encoding="utf-8")
        self.assertIn("## Сценарий открытого проекта в IDE и необязательных ссылок (Issue #52)", protocol)
        for token in ("AGENT_START.ru.md", "NOT_TESTED", "BLOCKED", "preview",
                      "rollback/recover", "10 минут", "двух необходимых уточнений", "локально открытым проектом"):
            self.assertIn(token, protocol)
        self.assertIn("(docs/ru/ACCEPTANCE.md#", EN.read_text(encoding="utf-8"))
        self.assertIn("(docs/ru/ACCEPTANCE.md#", RU.read_text(encoding="utf-8"))
        self.assertIn("NOT_TESTED", EN.read_text(encoding="utf-8"))
        self.assertIn("NOT_TESTED", RU.read_text(encoding="utf-8"))

    def test_absent_project_never_created_by_init_or_doctor(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "missing"
            for cmd in ("doctor", "init"):
                args = (cmd, "--target", str(target))
                if cmd == "init":
                    args += ("--task", "feature", "--apply")
                response = run_cli(*args)
                self.assertEqual(response.returncode, 2, response.stderr)
                self.assertEqual(json.loads(response.stdout)["result"], "BLOCKED")
                self.assertFalse(target.exists(), "Missing project must remain untouched")

    def test_separate_codex_and_claude_layouts_preserve_project_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            policies = {}
            for name in ("AGENTS.md", "CLAUDE.md"):
                path = target / name
                path.write_text("user-owned policy: do not modify\n", encoding="utf-8")
                policies[name] = path.read_bytes()
            codex = run_cli("init", "--target", directory, "--task", "feature", "--apply")
            self.assertEqual(codex.returncode, 0, codex.stderr)
            claude = run_cli("init", "--target", directory, "--task", "ui",
                             "--layout", "claude", "--apply")
            self.assertEqual(claude.returncode, 0, claude.stderr)
            for name, before in policies.items():
                self.assertEqual((target / name).read_bytes(), before)
            self.assertTrue((target / ".agents/skills/task-scoping/SKILL.md").is_file())
            self.assertTrue((target / ".claude/skills/task-scoping/SKILL.md").is_file())
            for layout in ("codex", "claude"):
                result = run_cli("status", "--target", directory, "--layout", layout)
                self.assertEqual(result.returncode, 0, (layout, result.stderr))

    def test_locally_modified_managed_skill_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            initial = run_cli("init", "--target", directory, "--task", "feature",
                              "--apply")
            self.assertEqual(initial.returncode, 0, initial.stderr)
            skill = Path(directory) / ".agents/skills/task-scoping/SKILL.md"
            skill.write_text(skill.read_text(encoding="utf-8") + "\nlocal owner edit\n",
                             encoding="utf-8")
            before = skill.read_bytes()
            attempt = run_cli("init", "--target", directory, "--task", "feature",
                              "--apply")
            self.assertEqual(attempt.returncode, 2, attempt.stderr)
            self.assertEqual(json.loads(attempt.stdout)["result"], "BLOCKED")
            self.assertEqual(skill.read_bytes(), before)


    def test_local_ide_is_primary_and_remote_urls_optional(self):
        for path, header, footer, wording in (
            (RU, "## Основной сценарий: проект открыт в IDE",
             "## Дополнительный сценарий: ссылки на репозитории", "Используй AI Development Toolkit"),
            (EN, "## Primary path: project already open in your IDE",
             "## Optional path: remote repository links", "Use AI Development Toolkit"),
        ):
            text = path.read_text(encoding="utf-8")
            primary = text.split(header, 1)[1].split(footer, 1)[0]
            remote = text.split(footer, 1)[1]
            self.assertIn(wording, primary)
            self.assertIn("Codex", primary)
            self.assertNotIn("https://github.com/OWNER/PROJECT", primary,
                             "Local workspace must not require target repo URL")
            self.assertIn("https://github.com/OWNER/PROJECT", remote)
            self.assertIn("NOT_TESTED", text)
        for path, link in (
            (ROOT / "README.ru.md", "(AGENT_START.ru.md)"),
            (ROOT / "README.md", "(AGENT_START.md)"),
            (ROOT / "docs/ru/BEGINNER_START.md", "(../../AGENT_START.ru.md)"),
            (ROOT / "docs/BEGINNER_START.md", "(../AGENT_START.md)"),
        ):
            contents = path.read_text(encoding="utf-8")
            self.assertIn("Codex", contents)
            self.assertIn(link, contents)

    def test_workspace_ambiguity_and_missing_access_not_faked(self):
        for path in (EN, RU):
            contents = path.read_text(encoding="utf-8")
            self.assertIn("Git", contents)
            self.assertIn("NOT_VERIFIED", contents)
            self.assertIn("BLOCKED", contents)
            self.assertIn("AGENTS.md", contents)
        # A documented workspace-first contract does not change core CLI:
        # the caller must still resolve an actual, existing target directory.
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "unselected-root"
            result = run_cli("init", "--target", str(missing), "--task", "feature", "--apply")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["result"], "BLOCKED")
            self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
