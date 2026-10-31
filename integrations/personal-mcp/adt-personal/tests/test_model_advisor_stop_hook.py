"""Offline contract tests for inactive optional Codex Desktop Stop-hook."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "hooks" / "model_advisor_stop_hook.py"
spec = importlib.util.spec_from_file_location("adt_model_advisor_stop_hook", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

REPORT_RU = (
    "<!-- ADT-MODEL-ADVISOR-ACTIVE -->\n"
    "Статус: BLOCKED — к выпуску не готово.\n"
    "Подтверждённые риски:\n"
    "1. Откат может уничтожить новую ревизию — reset --hard rollback race.\n"
    "2. Unix установщик копирует updater неатомарно, journal recovery failed.\n"
    "3. Ошибка первой проверки блокирует регистрацию расписания.\n"
)
REPORT_EN = (
    "<!-- ADT-MODEL-ADVISOR-ACTIVE -->\n"
    "Release BLOCKED: confirmed risk: Windows reparse and hardlink "
    "traversal, OS-level stale lock race, interrupted rollback journal."
)


class StopHookTests(unittest.TestCase):
    def event(self, message, **kwargs):
        return {"hook_event_name": "Stop", "stop_hook_active": False,
                "last_assistant_message": message, **kwargs}

    def test_owner_release_blocking_report_triggers_bounded_continuation(self):
        result = module.check_stop(self.event(REPORT_RU))
        self.assertEqual(result.get("decision"), "block")
        self.assertIn("неподтверждённых моделей", result["reason"])
        self.assertIn("не запускай", result["reason"].casefold())
        self.assertNotIn("rollback race", result["reason"])
        self.assertNotIn("reset --hard", result["reason"])

    def test_english_report_triggers_without_claiming_available_models(self):
        result = module.check_stop(self.event(REPORT_EN))
        self.assertEqual(result.get("decision"), "block")
        self.assertIn("Do not name unverified models", result["reason"])
        self.assertNotIn("hardlink traversal", result["reason"])

    def test_non_toolkit_external_controller_does_not_trigger_stop_hook(self):
        for external in ("Original Ponytail", "Harness2", "Graphify", "Claude Agent"):
            message = "Release BLOCKED: confirmed security risk, rollback race and concurrency bug in " + external
            with self.subTest(name=external):
                self.assertEqual(module.check_stop(self.event(message)), {})
        self.assertEqual(module.check_stop(self.event("Quoted tool output:\n" + REPORT_EN)), {})

    def test_noop_on_ordinary_and_nonconfirmed_tasks(self):
        for message in (
            "Updated a README typo, all checks pass.",
            "Security update documentation completed. Ready for release.",
            "No confirmed issues: rollback and concurrency tests passed.",
            "Reviewed rollback documentation; no defects found.",
            "Done.",
            "",
            "Проверил блокировки, обновил инструкцию: нет подтвержденных рисков",
        ):
            with self.subTest(message=message[:50]):
                self.assertEqual(module.check_stop(self.event(message)), {})

    def test_noop_on_repeat_stop_or_already_advised(self):
        self.assertEqual(module.check_stop(self.event(
            REPORT_RU, stop_hook_active=True)), {})
        self.assertEqual(module.check_stop(self.event(
            REPORT_EN + " Independent model review may be helpful.")), {})
        self.assertEqual(module.check_stop(self.event(
            REPORT_RU + " Независимая проверка второй моделью рекомендована.")), {})

    def test_noop_for_invalid_events_and_large_private_text(self):
        for value in (None, [], {}, {"hook_event_name": "UserPromptSubmit"},
                      self.event(None), self.event("x" * 16001)):
            with self.subTest(item=str(value)[:60]):
                self.assertEqual(module.check_stop(value), {})

    def test_stdio_valid_json_no_telemetry_and_fail_open(self):
        for payload, expected in (
            (json.dumps(self.event(REPORT_RU), ensure_ascii=False).encode(), "block"),
            (json.dumps(self.event("Fixed documentation")).encode(), None),
            (b"not json", None),
            (b"x" * 65537, None),
        ):
            with self.subTest(payload_length=len(payload)):
                proc = subprocess.run([sys.executable, "-B", str(SCRIPT)],
                                      input=payload, capture_output=True, timeout=10)
                self.assertEqual(proc.returncode, 0, proc.stderr.decode(errors="replace"))
                self.assertFalse(proc.stderr)
                body = json.loads(proc.stdout.decode("utf-8"))
                self.assertEqual(body.get("decision"), expected)
                self.assertNotIn("tool_input", body)
                self.assertNotIn("tool_response", body)
                self.assertNotIn("last_assistant_message", body)


if __name__ == "__main__":
    unittest.main()
