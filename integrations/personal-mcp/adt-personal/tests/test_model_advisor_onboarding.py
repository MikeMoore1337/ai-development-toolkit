"""#401: proactive Codex advisor is opt-in once, not a per-task pasted prompt.

Source-only tests run on Linux/macOS. PowerShell lifecycle tests run on Windows.
No Codex CLI, subagent, account or remote provider is invoked.
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "Enable-ADT-Model-Advisor.ps1"
BEGIN = "<!-- ADT-MODEL-ADVISOR BEGIN -->"
END = "<!-- ADT-MODEL-ADVISOR END -->"


class AdvisorSourceContract(unittest.TestCase):
    def test_one_time_opt_in_not_default_install(self):
        src = SCRIPT.read_text(encoding="utf-8")
        installer = SCRIPT.with_name("Install-ADT-Personal.ps1").read_text(encoding="utf-8")
        self.assertIn("[CmdletBinding(SupportsShouldProcess=$true)]", src)
        self.assertIn("[switch]$Disable", src)
        self.assertIn("[switch]$Check", src)
        self.assertIn("$env:CODEX_HOME", src)
        self.assertIn("MASKED_BY_GLOBAL_OVERRIDE", src)
        self.assertIn("SOURCE_PRESENT_CLIENT_UNVERIFIED", src)
        self.assertIn("Backup:", src)
        self.assertIn(BEGIN, src)
        self.assertIn(END, src)
        self.assertNotIn("Enable-ADT-Model-Advisor.ps1", installer)

    def test_normal_prompt_triggers_advice(self):
        src = SCRIPT.read_text(encoding="utf-8")
        for token in (
            "For ordinary software", "without",
            "toolkit_prepare_task", "once per task",
            "SINGLE_MODEL", "RECOMMEND_WITH_CONFIRMATION", "AUTO_OPT_IN",
            "No separate template prompt", "current Codex chat",
        ):
            self.assertIn(token, src)

    def test_simple_tasks_not_interrupted_and_refusal_is_final(self):
        src = SCRIPT.read_text(encoding="utf-8")
        for token in (
            "For simple, routine or self-contained changes",
            "Do NOT present the advisor choice on every turn",
            "No reply means NO permission",
            "Honor a user's refusal",
            "Never call subagents simply because this instruction block",
            "model availability", "Never invent entitlement",
            "current primary model",
        ):
            self.assertIn(token, src)

    def test_existing_policy_and_cost_gates_remain(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("Respect real cost gates", src)
        self.assertIn("project AGENTS.md", src)
        self.assertIn("toolkit_codex_prepare_delegation", src)
        self.assertIn("toolkit_codex_review_delegation", src)
        self.assertIn("host-owned one-shot claim", src)
        self.assertIn("without retry", src)
        self.assertIn("not claim a native", src)
        self.assertNotIn("codex mcp add", src)
        self.assertNotIn("invoke-webrequest", src.casefold())


@unittest.skipUnless(shutil.which("powershell.exe"), "Requires Windows PowerShell")
class WindowsAdvisorLifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name) / "AGENTS.md"
        self.original = "# Existing global rules\r\n\r\nUse local policy first.\r\n"
        self.path.write_text(self.original, encoding="utf-8", newline="")
        self.original_bytes = self.path.read_bytes()

    def run_script(self, *flags, expect=0):
        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
               "-File", str(SCRIPT), "-InstructionsPath", str(self.path), *flags]
        outcome = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        self.assertEqual(outcome.returncode, expect,
                         f"stdout={outcome.stdout}\nstderr={outcome.stderr}")
        return outcome

    def test_enable_twice_is_idempotent_disable_preserves_other_content(self):
        self.run_script()
        first = self.path.read_bytes()
        self.assertIn(BEGIN.encode(), first)
        self.assertIn(b"Use local policy first.", first)
        self.assertIn(b"RECOMMEND_WITH_CONFIRMATION", first)
        self.run_script()
        self.assertEqual(first, self.path.read_bytes())
        backups = list(self.path.parent.glob("AGENTS.md.adt-model-advisor-backup-*"))
        self.assertEqual(len(backups), 1)
        self.run_script("-Disable")
        body = self.path.read_text(encoding="utf-8")
        self.assertNotIn(BEGIN, body)
        self.assertIn("Use local policy first.", body)
        second = self.path.read_bytes()
        self.run_script("-Disable")
        self.assertEqual(second, self.path.read_bytes())

    def test_whatif_does_not_touch_file_or_create_backups(self):
        self.run_script("-WhatIf")
        self.assertEqual(self.path.read_bytes(), self.original_bytes)
        self.assertEqual(list(self.path.parent.glob("*.adt-model-advisor-backup-*")), [])

    def test_corrupted_existing_marker_fail_closed(self):
        self.path.write_text("# intro\n" + BEGIN + "\n", encoding="utf-8")
        before = self.path.read_bytes()
        self.run_script(expect=1)
        self.assertEqual(before, self.path.read_bytes())

    def test_duplicate_blocks_fail_closed(self):
        self.path.write_text(BEGIN + "\n" + END + "\n" + BEGIN + "\n" + END,
                             encoding="utf-8")
        before = self.path.read_bytes()
        self.run_script(expect=1)
        self.assertEqual(before, self.path.read_bytes())

    def test_whatif_disable_keeps_block(self):
        self.run_script()
        before = self.path.read_bytes()
        self.run_script("-Disable", "-WhatIf")
        self.assertEqual(before, self.path.read_bytes())

    def test_read_only_check_identifies_installed_and_missing_block(self):
        before = self.path.read_bytes()
        result = self.run_script("-Check")
        self.assertIn("NOT_INSTALLED", result.stdout)
        self.assertEqual(before, self.path.read_bytes())
        self.run_script()
        enabled = self.path.read_bytes()
        result = self.run_script("-Check")
        self.assertIn("SOURCE_PRESENT_CLIENT_UNVERIFIED", result.stdout)
        self.assertEqual(enabled, self.path.read_bytes())
        self.assertEqual(len(list(self.path.parent.glob("*.adt-model-advisor-backup-*"))), 1)

    def test_nonempty_override_masks_block_and_refuses_enable(self):
        override = self.path.with_name("AGENTS.override.md")
        override.write_text("# Temporary override\n", encoding="utf-8")
        before = self.path.read_bytes()
        result = self.run_script("-Check")
        self.assertIn("MASKED_BY_GLOBAL_OVERRIDE", result.stdout)
        failure = self.run_script(expect=1)
        self.assertIn("takes precedence", failure.stderr)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(list(self.path.parent.glob("*.adt-model-advisor-backup-*")), [])

    def test_empty_override_does_not_block_enable(self):
        override = self.path.with_name("AGENTS.override.md")
        override.write_text("  \n", encoding="utf-8")
        self.run_script()
        self.assertIn(BEGIN, self.path.read_text(encoding="utf-8"))

    def test_disable_remains_possible_with_active_override(self):
        self.run_script()
        override = self.path.with_name("AGENTS.override.md")
        override.write_text("# Overrides global guidance\n", encoding="utf-8")
        self.run_script("-Disable")
        self.assertNotIn(BEGIN, self.path.read_text(encoding="utf-8"))

    def test_codex_home_environment_is_install_target(self):
        target = pathlib.Path(self.temp.name) / "custom-codex-home"
        target.mkdir()
        env = os.environ.copy()
        env["CODEX_HOME"] = str(target)
        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
               "-File", str(SCRIPT)]
        result = subprocess.run(cmd, capture_output=True, text=True,
                                env=env, timeout=25)
        self.assertEqual(result.returncode, 0, result.stderr)
        new_global = target / "AGENTS.md"
        self.assertTrue(new_global.is_file())
        self.assertIn(BEGIN, new_global.read_text(encoding="utf-8"))
        check = subprocess.run(cmd + ["-Check"], capture_output=True,
                               text=True, env=env, timeout=25)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn("SOURCE_PRESENT_CLIENT_UNVERIFIED", check.stdout)


if __name__ == "__main__":
    unittest.main()
