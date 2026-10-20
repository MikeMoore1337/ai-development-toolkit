"""Offline no-terminal onboarding contracts (#51).

A contract test is not an AI client trial or a human usability study.
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/no_terminal_acceptance.json"
EN = ROOT / "docs/BEGINNER_START.md"
RU = ROOT / "docs/ru/BEGINNER_START.md"

CLIENTS = {
    "codex": (".agents/skills", "OPTIONAL"),
    "chatgpt": (None, "NOT_REQUIRED_FOR_CHAT"),
    "claude-code": (".claude/skills", "OPTIONAL"),
    "claude": (None, "NOT_REQUIRED_FOR_CHAT"),
}
SCENARIOS = set("ABCDE")
EXPECTED_NEGATIVES = {
    "no-command-tool": ("REPORT_LIMIT", "NOT_RUN", "CLAIM_TEST_PASS"),
    "project-absent": ("REQUEST_ARTIFACT", "BLOCKED", "CLAIM_REPOSITORY_AUDITED"),
    "chatgpt-codex-skills": ("REPORT_LIMIT", "NOT_TESTED", "CLAIM_ACTIVATED"),
    "unapproved-deploy": ("STOP", "BLOCKED", "DEPLOY"),
    "unavailable-paid-feature": ("PREPARE_ONLY", "NOT_RUN", "INCUR_CHARGE"),
    "no-terminal": ("PREPARE_ONLY", "NOT_RUN", "CLAIM_INSTALLED"),
    "generated-untested-code": ("REPORT_LIMIT", "NOT_RUN", "CLAIM_WORKING_APP"),
    "no-repo-permissions": ("REQUEST_ARTIFACT", "BLOCKED", "CLAIM_FILE_EDIT"),
    "unsupported-skill-layout": ("STOP", "NOT_TESTED", "CLAIM_DISCOVERED"),
    "unmanaged-collision": ("STOP", "BLOCKED", "OVERWRITE_UNMANAGED"),
    "unavailable-monitoring": ("PREPARE_ONLY", "NOT_RUN", "CLAIM_CONTINUOUS_MONITORING"),
}
FIELDS = {
    "en": ("Goal", "Input", "Result", "Limit", "Check", "Blocked"),
    "ru": ("Цель", "Входные данные", "Результат", "Ограничения", "Проверка", "При блокировке"),
}
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\s]+)")
HEADING = re.compile(r"(?m)^### ([A-E])\. (.+)$")
COMMAND = re.compile(r"(?m)^python scripts/adt\.py (.+)$")


def validate_contract(data: dict) -> list[str]:
    """Validate choices and safe outcomes, not simply that keywords exist."""
    issues: list[str] = []
    if data.get("schema_version") != 1:
        issues.append("unknown schema")
    clients = data.get("clients", [])
    ids = [row.get("id") for row in clients if isinstance(row, dict)]
    if set(ids) != set(CLIENTS) or len(ids) != len(CLIENTS):
        issues.append("client coverage")
    for row in clients:
        if not isinstance(row, dict) or row.get("id") not in CLIENTS:
            issues.append("invalid client")
            continue
        layout, terminal = CLIENTS[row["id"]]
        if (row.get("local_layout"), row.get("terminal")) != (layout, terminal):
            issues.append(f"{row['id']}: invented managed layout or terminal requirement")
        if (row.get("live_discovery"), row.get("use"), row.get("effectiveness")) != (
            "NOT_TESTED", "NOT_TESTED", "NOT_MEASURED"
        ):
            issues.append(f"{row['id']}: claimed real agent evidence")
        if not row.get("mode") or not row.get("heading"):
            issues.append(f"{row['id']}: missing mode")
    rows = data.get("scenarios", [])
    names = [row.get("id") for row in rows if isinstance(row, dict)]
    if set(names) != SCENARIOS or len(names) != len(SCENARIOS):
        issues.append("five journeys incomplete")
    for row in rows:
        if not isinstance(row, dict):
            issues.append("malformed journey")
            continue
        if not all(isinstance(row.get(k), str) and row[k].strip()
                   for k in ("en", "ru", "input")):
            issues.append(f"{row.get('id')}: missing input or title")
        if (row.get("result_if_no_execution") not in {"PREPARED_ONLY", "BLOCKED"}
                or row.get("verification") != "NOT_RUN"):
            issues.append(f"{row.get('id')}: fictional executed result")
    guards = data.get("negative_cases", [])
    guard_ids = [row.get("id") for row in guards if isinstance(row, dict)]
    if set(guard_ids) != set(EXPECTED_NEGATIVES) or len(guard_ids) != len(EXPECTED_NEGATIVES):
        issues.append("negative coverage")
    for row in guards:
        if not isinstance(row, dict) or row.get("id") not in EXPECTED_NEGATIVES:
            issues.append("malformed negative case")
            continue
        case = row["id"]
        expected = EXPECTED_NEGATIVES[case]
        if tuple(row.get(k) for k in ("decision", "check", "forbid")) != expected:
            issues.append(f"{case}: unsafe outcome")
        if (not isinstance(row.get("given"), str) or len(row["given"]) < 20
                or not isinstance(row.get("next"), str) or len(row["next"]) < 20):
            issues.append(f"{case}: missing scenario or recovery")
    evidence = data.get("evidence", {})
    if evidence != {
        "offline_docs": "NOT_RUN",
        "live_discovery": "NOT_TESTED",
        "live_activation": "NOT_TESTED",
        "model_effectiveness": "NOT_MEASURED",
        "human_usability": "NOT_TESTED",
    }:
        issues.append("fake evidence")
    return issues


def sections(text: str) -> dict[str, str]:
    matches = list(HEADING.finditer(text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(1)] = text[match.end():end]
    return result


class NoTerminalOnboardingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_acceptance_fixture_contract(self):
        self.assertEqual(validate_contract(self.fixture), [])

    def test_negative_missing_or_unsafe_guard_is_rejected(self):
        case = copy.deepcopy(self.fixture)
        case["negative_cases"].pop()
        self.assertIn("negative coverage", validate_contract(case))
        case = copy.deepcopy(self.fixture)
        next(item for item in case["negative_cases"] if item["id"] == "unapproved-deploy")["decision"] = "PREPARE_ONLY"
        self.assertTrue(any("unapproved-deploy: unsafe" in item for item in validate_contract(case)))

    def test_no_fake_agent_evidence(self):
        case = copy.deepcopy(self.fixture)
        case["clients"][0]["live_discovery"] = "VERIFIED"
        self.assertTrue(any("claimed real agent evidence" in x for x in validate_contract(case)))
        case = copy.deepcopy(self.fixture)
        case["scenarios"][0]["verification"] = "PASS"
        self.assertTrue(any("fictional executed" in x for x in validate_contract(case)))

    def test_four_client_sections_and_six_required_fields(self):
        for lang, path in (("en", EN), ("ru", RU)):
            text = path.read_text(encoding="utf-8")
            for client in self.fixture["clients"]:
                self.assertRegex(text, rf"(?m)^### {re.escape(client['heading'])}$")
            for row in self.fixture["scenarios"]:
                self.assertIn(f"### {row['id']}. {row[lang]}", text)
            parsed = sections(text)
            self.assertEqual(set(parsed), SCENARIOS)
            for key, body in parsed.items():
                with self.subTest(lang=lang, scenario=key):
                    self.assertEqual(body.count("```text"), 1, "one copy-ready prompt")
                    self.assertGreaterEqual(body.count("```"), 2)
                    for label in FIELDS[lang]:
                        self.assertIn(f"**{label}:**", body)
                    self.assertIn("NOT_RUN", body if key == "A" else text)

    def test_local_links_really_resolve(self):
        for path in (EN, RU, ROOT / "README.md", ROOT / "README.ru.md",
                     ROOT / "docs/ru/README.md", ROOT / "docs/ru/GETTING_STARTED.md"):
            text = path.read_text(encoding="utf-8")
            for raw in LINK.findall(text):
                parsed = urlsplit(raw)
                if parsed.scheme or parsed.netloc or raw.startswith("#"):
                    continue
                resolved = (path.parent / unquote(parsed.path)).resolve()
                with self.subTest(path=path.name, target=raw):
                    self.assertTrue(resolved.is_relative_to(ROOT))
                    self.assertTrue(resolved.is_file(), f"broken local link {path}: {raw}")

    def test_single_visible_english_and_russian_entrypoint(self):
        en = (ROOT / "README.md").read_text(encoding="utf-8")
        ru = (ROOT / "README.ru.md").read_text(encoding="utf-8")
        self.assertIn("(docs/BEGINNER_START.md)", en)
        self.assertIn("(docs/ru/BEGINNER_START.md)", ru)
        self.assertLess(en.index("(docs/BEGINNER_START.md)"), en.index("## What's inside?"))
        self.assertLess(ru.index("(docs/ru/BEGINNER_START.md)"), ru.index("## Что входит"))
        self.assertIn("(BEGINNER_START.md)", (ROOT / "docs/ru/README.md").read_text(encoding="utf-8"))
        self.assertIn("(../BEGINNER_START.md)", RU.read_text(encoding="utf-8"))
        self.assertIn("(ru/BEGINNER_START.md)", EN.read_text(encoding="utf-8"))
        self.assertIn("(docs/ru/GETTING_STARTED.md)", ru)  # technical route retained

    def test_explicit_sources_safety_and_evidence_levels(self):
        for page in (EN, RU):
            contents = page.read_text(encoding="utf-8")
            self.assertIn("2026-10-20" if page == EN else "20.10.2026", contents)
            for host in ("learn.chatgpt.com", "help.openai.com", "code.claude.com",
                         "support.claude.com"):
                self.assertIn("https://" + host, contents)
            for status in ("NOT_TESTED", "NOT_MEASURED", "NOT_RUN"):
                self.assertIn(status, contents)
            for token in ("--apply", ".agents/skills", ".claude/skills", "SKILL.md",
                          "feature-delivery", "Make Feature"):
                self.assertIn(token, contents)
            self.assertIn("Customize > Skills", contents)
            self.assertIn("ZIP", contents)

    def test_real_cli_documented_read_only_examples(self):
        """Execute the actual documented command shapes, excluding --apply."""
        for page in (EN, RU):
            content = page.read_text(encoding="utf-8")
            command_section = content.split("## Optional local managed install", 1)[-1] if page == EN else (
                content.split("## Необязательная локальная установка", 1)[-1]
            )
            commands = [command for command in COMMAND.findall(command_section)
                        if "--apply" not in command]
            self.assertEqual(len(commands), 5)  # list, doctor, plan, init preview, status
            with tempfile.TemporaryDirectory() as folder:
                before = sorted(Path(folder).rglob("*"))
                for command in commands:
                    args = command.split()
                    args = [folder if part == "/path/to/project" else part for part in args]
                    result = subprocess.run(
                        [sys.executable, str(ROOT / "scripts/adt.py"), *args],
                        cwd=ROOT, text=True, capture_output=True, timeout=30, check=False,
                    )
                    self.assertEqual(result.returncode, 0, (page, command, result.stderr))
                self.assertEqual(before, sorted(Path(folder).rglob("*")),
                                 "documented preview must not write to project")


if __name__ == "__main__":
    unittest.main()
