"""Offline contract for external-reference Toolkit onboarding (#52/#95/#100).

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



class ChatGPTPersonalLiveProtocolTests(unittest.TestCase):
    """Offline source, compatibility and fallback contract, not real ChatGPT execution."""

    def test_live_protocol_is_bounded_read_only_and_versioned(self):
        import re
        live = MANIFEST["chatgpt_personal_live"]
        self.assertEqual(live["schema_version"], 2)
        self.assertEqual(live["protocol_generation"], 2)
        self.assertEqual(live["canonical_repository"], "MikeMoore1337/ai-development-toolkit")
        self.assertEqual(live["tracked_branch"], "main")
        self.assertEqual(live["commit_resolution"], "exact_sha_required")
        self.assertTrue(re.fullmatch(r"\d+\.\d+\.\d+", live["min_plugin_version"]))
        self.assertGreaterEqual(tuple(map(int, live["min_plugin_version"].split("."))), (0, 1, 5))
        self.assertEqual(live["fallback"], "BUNDLED_ROUTER")
        self.assertEqual(live["activation"], "best_effort_per_task_read_only")
        self.assertIs(live["install_upgrade_automatic"], False)
        self.assertTrue(1 <= live["max_retrieved_sources_per_batch"] <= 8)
        self.assertNotIn("max_retrieved_sources_per_task", live)

    def test_exact_head_ci_matrix_required(self):
        live = MANIFEST["chatgpt_personal_live"]
        self.assertEqual(live["required_ci_checks"], [
            "tests (ubuntu-latest, 3.12)",
            "tests (ubuntu-latest, 3.13)",
            "tests (windows-latest, 3.14)",
        ])
        matrix = [
            {"name": check, "status": "completed", "conclusion": "success"}
            for check in live["required_ci_checks"]
        ]
        def passes(given):
            values = {c["name"]: c for c in given}
            return all(name in values and values[name]["status"] == "completed"
                       and values[name]["conclusion"] == "success"
                       for name in live["required_ci_checks"])
        self.assertTrue(passes(matrix))
        for changed in (
            matrix[:-1],
            [dict(x, conclusion="failure") if i == 0 else x for i, x in enumerate(matrix)],
            [dict(x, status="in_progress", conclusion=None) if i == 0 else x
             for i, x in enumerate(matrix)],
        ):
            self.assertFalse(passes(changed))

    def assert_safe_source_sets(self, source_sets):
        from pathlib import PurePosixPath
        for values in source_sets.values():
            self.assertIsInstance(values, list)
            self.assertGreater(len(values), 0)
            self.assertEqual(len(values), len(set(values)))
            for filename in values:
                path = PurePosixPath(filename)
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)
                self.assertTrue((ROOT / filename).is_file(), filename)
                self.assertTrue((ROOT / filename).resolve().is_relative_to(ROOT.resolve()))

    def test_source_file_allowlist_does_not_escape_toolkit(self):
        live = MANIFEST["chatgpt_personal_live"]
        self.assertEqual(live["integrity_manifest"], "SHA256SUMS.txt")
        self.assertTrue((ROOT / live["integrity_manifest"]).is_file())
        self.assertIn("ui-orchestra", live["source_sets"])
        self.assertIn("AGENT_START.ru.md", live["source_sets"]["entry"])
        self.assert_safe_source_sets(live["source_sets"])

    def test_safe_source_set_can_span_multiple_batches(self):
        live = MANIFEST["chatgpt_personal_live"]
        paths = list(dict.fromkeys(path for group in live["source_sets"].values() for path in group))
        self.assertGreater(len(paths), live["max_retrieved_sources_per_batch"])
        self.assert_safe_source_sets({"composite": paths})
        with self.assertRaises(AssertionError):
            self.assert_safe_source_sets({"unsafe": ["../README.md"]})

    def test_bilingual_docs_reject_silent_upgrade_claims(self):
        guides = (EN, RU, ROOT / "docs/CLIENT_COMPATIBILITY.md",
                  ROOT / "docs/ru/CLIENT_COMPATIBILITY.md")
        for path in guides:
            contents = path.read_text(encoding="utf-8")
            for keyword in ("chatgpt_personal_live", "FALLBACK_BUNDLED", "SHELL_UPDATE_REQUIRED"):
                self.assertIn(keyword, contents, (path, keyword))
            self.assertIn("SHA", contents, path)




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
            for token in ("scripts/skill_manager.py ensure", "--apply", "--layout claude",
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
                      "GUIDANCE_ONLY", "10 минут", "двух необходимых уточнений", "локально открытый"):
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
            self.assertTrue((target / ".claude/skills/ux-ui-design-orchestra/SKILL.md").is_file())
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
             "## Дополнительный сценарий: ссылки на репозитории", "Toolkit"),
            (EN, "## Primary path: open IDE project + Toolkit URL, without manual installation",
             "## Optional path: remote repository links", "Toolkit"),
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

    def test_task_required_setup_is_default_with_reference_only_opt_out(self):
        for path in (EN, RU):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("scripts/skill_manager.py ensure", text)
                self.assertIn("USER_HOME", text)
                self.assertIn("reference-only", text)
                self.assertIn("BLOCKED", text)
                self.assertIn("--apply", text)
        policy = MANIFEST["required_setup_policy"]
        self.assertEqual("INSTALL_MISSING_FOR_CURRENT_TASK", policy["mode"])
        self.assertTrue(policy["reference_only_opt_out"])


    def test_primary_prompt_uses_toolkit_url_without_installation(self):
        for source, first, later in (
            (RU, "## Основной сценарий: проект открыт в IDE",
             "## Дополнительный сценарий: ссылки на репозитории"),
            (EN, "## Primary path: open IDE project + Toolkit URL, without manual installation",
             "## Optional path: remote repository links"),
        ):
            text = source.read_text(encoding="utf-8")
            primary = text.split(first, 1)[1].split(later, 1)[0]
            self.assertIn("https://github.com/MikeMoore1337/ai-development-toolkit", primary)
            self.assertNotIn("https://github.com/OWNER/PROJECT", primary)
            self.assertNotIn("adt.py init", primary, "No setup instructions in default prompt")
            self.assertNotIn("--apply", primary)
            self.assertIn("GUIDANCE_ONLY", text)
            self.assertIn("READ_ONLY", text)
            self.assertIn("NOT_VERIFIED", text)
            for forbidden in (".agents/skills/", ".claude/skills/", ".adt/", "reports/", "tmp/"):
                self.assertIn(forbidden, text)

    def test_report_destinations_are_external_by_contract(self):
        en = EN.read_text(encoding="utf-8")
        ru = RU.read_text(encoding="utf-8")
        protocol = (ROOT / "docs/ru/ACCEPTANCE.md").read_text(encoding="utf-8")
        for doc in (en, ru):
            self.assertIn("GUIDANCE_ONLY", doc)
            self.assertIn("NOT_VERIFIED", doc)
            self.assertIn("BLOCKED", doc)
            self.assertIn("git status", doc)
            self.assertIn("AGENTS.md", doc)
            self.assertIn("CLAUDE.md", doc)
        for marker in ("GUIDANCE_ONLY", "Отчёт: чат", "игнорируемые",
                       "без установки", "URL Toolkit", "NOT_TESTED"):
            self.assertIn(marker, protocol)
        self.assertIn("https://github.com/MikeMoore1337/ai-development-toolkit",
                      (ROOT / "docs/ru/BEGINNER_START.md").read_text(encoding="utf-8"))
        self.assertIn("https://github.com/MikeMoore1337/ai-development-toolkit",
                      (ROOT / "docs/BEGINNER_START.md").read_text(encoding="utf-8"))

    def test_cli_read_only_preflights_preserve_ignored_and_hidden_files(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "my-project"
            target.mkdir()
            (target / ".gitignore").write_text("reports/\\n.cache/\\n", encoding="utf-8")
            existing_report = target / "reports" / "user-report.md"
            existing_report.parent.mkdir()
            existing_report.write_text("pre-existing report\\n", encoding="utf-8")
            existing_cache = target / ".cache" / "keep"
            existing_cache.parent.mkdir()
            existing_cache.write_bytes(b"private user data")
            def snapshot():
                return {p.relative_to(target).as_posix(): p.read_bytes()
                        for p in target.rglob("*") if p.is_file()}
            before = snapshot()
            for args in (
                ("doctor", "--target", str(target)),
                ("profile", "plan", "--target", str(target), "--task", "qa"),
                ("init", "--target", str(target), "--task", "qa"),
            ):
                result = run_cli(*args)
                self.assertIn(result.returncode, (0, 2), result.stderr)
                self.assertEqual(before, snapshot(), "Read-only preflight wrote project files")


    def test_optional_local_install_does_not_leave_unrequested_reports(self):
        """Opt-in CLI writes managed files only; an unrelated local project has no Git remote."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "standalone"
            target.mkdir()
            (target / "README.md").write_bytes(b"Independent README\\n")
            (target / ".gitignore").write_text(".cache/\\nreports/\\n", encoding="utf-8")
            private = target / ".cache" / "keep.bin"
            private.parent.mkdir()
            private.write_bytes(b"existing ignored file")
            def outside_managed():
                return {p.relative_to(target).as_posix(): p.read_bytes()
                        for p in target.rglob("*") if p.is_file()
                        and p.relative_to(target).parts[0] not in (".adt", ".agents")}
            untouched = outside_managed()
            preview = run_cli("init", "--target", str(target), "--task", "feature")
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(outside_managed(), untouched)
            self.assertFalse((target / ".adt").exists())
            installed = run_cli("init", "--target", str(target), "--task", "feature", "--apply")
            self.assertEqual(installed.returncode, 0, installed.stderr)
            self.assertTrue(json.loads(installed.stdout)["applied"])
            self.assertEqual(outside_managed(), untouched)
            self.assertFalse((target / ".git").exists())
            self.assertTrue((target / ".agents/skills/task-scoping/SKILL.md").is_file())
            self.assertTrue((target / ".adt/skills-lock.json").is_file())
            managed = {p.relative_to(target).as_posix(): p.read_bytes()
                       for p in target.rglob("*") if p.is_file()}
            for step in (("status", "--target", str(target)),
                         ("init", "--target", str(target), "--task", "feature", "--apply")):
                result = run_cli(*step)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(managed,
                                 {p.relative_to(target).as_posix(): p.read_bytes()
                                  for p in target.rglob("*") if p.is_file()})
            self.assertFalse(any("report" in p.lower() or "audit" in p.lower()
                                 for p in managed if p not in untouched))

    def test_status_of_missing_local_project_never_creates_a_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing-local-workspace"
            status = run_cli("status", "--target", str(missing))
            self.assertEqual(status.returncode, 2)
            self.assertFalse(missing.exists())

    def test_human_protocol_tracks_distinct_evidence_and_measured_metrics(self):
        protocol = (ROOT / "docs/ru/ACCEPTANCE.md").read_text(encoding="utf-8")
        for phrase in ("Матрица независимых доказательств", "Независимое освоение новичком",
                       "Время до первого осмысленного действия", "Время до результата",
                       "Число вопросов агента", "Число ошибок",
                       "самостоятельных восстановлений", "NOT_MEASURED",
                       "Клиент только с чатом", "Понял ли участник разницу"):
            self.assertIn(phrase, protocol)
        self.assertIn("NOT_TESTED", protocol)
        self.assertIn("NOT_RUN", protocol)


if __name__ == "__main__":
    unittest.main()
