"""Deterministic acceptance-contract regression tests for beginner journeys (#49).

These tests do not execute an AI model, application or human usability study.
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/beginner_journeys.json"
STAGES = ["understand", "scope", "explain", "act", "verify", "report", "next"]
PERSONAS = {"create-app", "repair-defect", "connect-toolkit"}
GUARDS = {
    "missing-project", "no-filesystem", "no-terminal", "unsupported-client",
    "unclear-goal", "unmanaged-collision", "owner-lock", "no-test-environment",
    "failed-test", "no-independent-review", "unapproved-publication",
    "unapproved-payment", "plan-is-not-code",
}
STATUSES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED", "NOT_APPLICABLE"}
DECISIONS = {"REQUEST_INPUT", "PREPARE_ONLY", "STOP", "SAFE_ASSUMPTION", "REPORT_LIMIT"}
METHODS = {"manual", "unit", "review", "integration", "command"}
DANGEROUS = {
    "unapproved-publication": "PUBLISH",
    "unapproved-payment": "PURCHASE",
    "unmanaged-collision": "OVERWRITE_UNMANAGED",
    "owner-lock": "BYPASS_OWNER_LOCK",
    "plan-is-not-code": "CLAIM_IMPLEMENTED",
    "no-filesystem": "CLAIM_CHANGED",
    "no-terminal": "CLAIM_TEST_PASS",
    "no-test-environment": "CLAIM_VERIFIED",
    "failed-test": "CLAIM_TEST_PASS",
    "no-independent-review": "CLAIM_INDEPENDENT_PASS",
    "unsupported-client": "CLAIM_ACTIVATED",
    "missing-project": "CLAIM_ROOT_CAUSE",
}


def validate_contract(content: dict, root: Path = ROOT) -> list[str]:
    issues: list[str] = []
    if content.get("schema_version") != 1 or content.get("stages") != STAGES:
        issues.append("invalid workflow schema or stage ordering")
    personas = content.get("personas")
    if not isinstance(personas, list):
        return issues + ["missing personas"]
    identifiers = [row.get("id") for row in personas if isinstance(row, dict)]
    if len(identifiers) != len(personas) or set(identifiers) != PERSONAS or len(identifiers) != len(set(identifiers)):
        issues.append("invalid persona coverage or duplicates")
    for person in personas:
        if not isinstance(person, dict):
            continue
        pid = person.get("id")
        if not all(isinstance(person.get(x), str) and person[x].strip()
                   for x in ("input", "goal", "no_runtime_result")):
            issues.append(f"{pid}: incomplete user journey")
        if person.get("no_runtime_result") not in {"PREPARED_ONLY", "BLOCKED"}:
            issues.append(f"{pid}: false no-runtime outcome")
        for field in ("minimal_inputs", "known_risks", "exclusions"):
            if not isinstance(person.get(field), list) or not person[field]:
                issues.append(f"{pid}: missing {field}")
        skills = person.get("skill_paths", [])
        if not skills or any(
            not isinstance(name, str) or not name.startswith(".agents/skills/")
            or not (root / name).is_file() or not (root / name).resolve().is_relative_to(root.resolve())
            for name in skills
        ):
            issues.append(f"{pid}: nonexistent or escaping skill reference")
        checks = person.get("acceptance", [])
        expected_prefix = {"create-app": "A", "repair-defect": "B", "connect-toolkit": "C"}.get(pid, "?")
        if len(checks) < 3 or len({c.get("id") for c in checks}) != len(checks):
            issues.append(f"{pid}: missing or duplicate acceptance cases")
        for check in checks:
            if not isinstance(check, dict):
                issues.append(f"{pid}: malformed acceptance case")
                continue
            if (not isinstance(check.get("id"), str)
                    or not check["id"].startswith(expected_prefix)
                    or check.get("method") not in METHODS
                    or not isinstance(check.get("observable"), str)
                    or len(check["observable"].strip()) < 12
                    or check.get("status") != "NOT_RUN"):
                issues.append(f"{pid}: acceptance fixture claims execution or is malformed")

    guards = content.get("negative_cases", [])
    if not isinstance(guards, list):
        return issues + ["missing negative cases"]
    gids = [x.get("id") for x in guards if isinstance(x, dict)]
    if len(gids) != len(guards) or set(gids) != GUARDS or len(set(gids)) != len(gids):
        issues.append("missing, unknown or duplicate negative guard")
    for guard in guards:
        if not isinstance(guard, dict):
            continue
        ident = guard["id"]
        claims = guard.get("forbidden_claims")
        if (guard.get("decision") not in DECISIONS
                or guard.get("check_status") not in STATUSES
                or not isinstance(guard.get("condition"), str)
                or not isinstance(claims, list) or not claims
                or (ident in DANGEROUS and DANGEROUS[ident] not in claims)):
            issues.append(f"{ident}: unsafe negative guard")
        if ident in {"unapproved-publication", "unapproved-payment", "owner-lock",
                     "unmanaged-collision", "unsupported-client"} and guard.get("decision") != "STOP":
            issues.append(f"{ident}: missing stop gate")
        if ident == "failed-test" and guard.get("check_status") != "FAIL":
            issues.append("failed test presented as success")
        if ident in {"no-filesystem", "no-terminal", "plan-is-not-code"} and guard.get("check_status") != "NOT_RUN":
            issues.append(f"{ident}: unexecuted check misreported")

    boundaries = {row["client_id"]: row for row in content.get("client_boundaries", [])}
    if set(boundaries) != {"codex", "claude-code", "hermes"}:
        issues.append("incomplete client boundary matrix")
    else:
        for client, row in boundaries.items():
            if row.get("live_discovery") != "NOT_TESTED" or row.get("effectiveness") != "NOT_MEASURED":
                issues.append(f"{client}: invented activation/effectiveness evidence")
            if row.get("manager") != ("UNSUPPORTED" if client == "hermes" else "VERIFIED"):
                issues.append(f"{client}: manager contract mismatch")
    report = content.get("example_report", {})
    checks = report.get("checks", [])
    if (report.get("result") != "PREPARED_ONLY" or report.get("changes_applied") is not False
            or report.get("independent_acceptance") != "NOT_TESTED"
            or not checks):
        issues.append("example falsely claims implemented or independently reviewed")
    for check in checks:
        if check.get("status") not in STATUSES:
            issues.append("invalid check status")
        elif check["status"] == "PASS" and not check.get("evidence"):
            issues.append("PASS without executed evidence")
        elif check["status"] in {"NOT_RUN", "BLOCKED"} and check.get("evidence"):
            issues.append("unexecuted check has claimed evidence")
    return issues


class BeginnerJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_real_contract(self):
        self.assertEqual(validate_contract(self.data), [])

    def test_missing_persona_rejected(self):
        case = copy.deepcopy(self.data)
        case["personas"].pop()
        self.assertTrue(validate_contract(case))

    def test_broken_skill_reference_rejected(self):
        case = copy.deepcopy(self.data)
        case["personas"][0]["skill_paths"] = [".agents/skills/not-a-real-skill/SKILL.md"]
        self.assertTrue(any("skill reference" in problem for problem in validate_contract(case)))

    def test_claiming_executed_acceptance_rejected(self):
        case = copy.deepcopy(self.data)
        case["personas"][0]["acceptance"][0]["status"] = "PASS"
        self.assertTrue(any("claims execution" in problem for problem in validate_contract(case)))

    def test_removing_required_stop_gate_rejected(self):
        case = copy.deepcopy(self.data)
        guard = next(g for g in case["negative_cases"] if g["id"] == "unapproved-publication")
        guard["decision"] = "PREPARE_ONLY"
        self.assertTrue(any("missing stop gate" in problem for problem in validate_contract(case)))

    def test_unmanaged_overwrite_claim_rejected(self):
        case = copy.deepcopy(self.data)
        guard = next(g for g in case["negative_cases"] if g["id"] == "unmanaged-collision")
        guard["forbidden_claims"].remove("OVERWRITE_UNMANAGED")
        self.assertTrue(any("unsafe negative guard" in problem for problem in validate_contract(case)))

    def test_unrun_test_cannot_claim_pass(self):
        case = copy.deepcopy(self.data)
        case["example_report"]["checks"][0]["status"] = "PASS"
        self.assertTrue(any("PASS without executed evidence" in problem for problem in validate_contract(case)))

    def test_no_runtime_cannot_claim_implemented(self):
        case = copy.deepcopy(self.data)
        case["example_report"]["changes_applied"] = True
        self.assertTrue(any("falsely claims" in problem for problem in validate_contract(case)))

    def test_fake_client_activation_rejected(self):
        case = copy.deepcopy(self.data)
        case["client_boundaries"][0]["live_discovery"] = "VERIFIED"
        self.assertTrue(any("invented activation" in problem for problem in validate_contract(case)))



class BeginnerTaskRouteTests(unittest.TestCase):
    """Static task-first navigation checks; not an AI-client usability trial."""

    ROUTES = {
        "docs/BEGINNER_START.md": (
            "## Pick your task first",
            ("Code", "QA", "Design", "SEO", "Research", "Maintenance"),
            "## Choose an access route",
            ("Chat without installation", "Installed ChatGPT plugin",
             "Toolkit MCP for Codex or Claude Code",
             "Local managed skills for Codex or Claude Code"),
        ),
        "docs/ru/BEGINNER_START.md": (
            "## Сначала выберите задачу",
            ("Код", "QA", "Дизайн", "SEO", "Исследование", "Сопровождение"),
            "## Выберите способ подключения",
            ("Чат без установки", "Установленный плагин ChatGPT",
             "Toolkit MCP для Codex или Claude Code",
             "Локальные навыки Codex или Claude Code"),
        ),
    }
    PROFILE_MAP = {
        "code": "codex-feature", "qa": "qa-core",
        "design": "ui-orchestra", "seo": "seo-audit",
        "research": "research", "maintenance": "maintenance-support",
    }

    @staticmethod
    def section(content: str, title: str) -> str:
        marker = title + "\n"
        if content.count(marker) != 1:
            raise ValueError("Missing or repeated heading: " + title)
        tail = content.split(marker, 1)[1]
        return tail.split("\n## ", 1)[0]

    @staticmethod
    def rows(section: str) -> list[tuple[str, str]]:
        import re
        matches = []
        for line in section.splitlines():
            match = re.fullmatch(
                r"\| \*\*([^*]+)\*\* \| (.+) \| (.+) \|", line
            )
            if match:
                matches.append((match.group(1), match.group(2) + " " + match.group(3)))
        return matches

    def test_first_result_three_step_route_and_evidence(self):
        for path, heading, prompt_marker in (
            ("docs/BEGINNER_START.md", "## Your first result in three steps",
             "**One copyable example:**"),
            ("docs/ru/BEGINNER_START.md", "## Первый результат за три шага",
             "**Один готовый пример:**"),
        ):
            with self.subTest(path=path):
                page = (ROOT / path).read_text(encoding="utf-8")
                section = self.section(page, heading)
                numbered = [line for line in section.splitlines()
                            if line.startswith(("1. ", "2. ", "3. "))]
                self.assertEqual(["1. ", "2. ", "3. "],
                                 [line[:3] for line in numbered])
                self.assertIn(prompt_marker, section)
                self.assertIn("(BEGINNER_WORKFLOW.md)", section)
                self.assertIn("NOT_RUN", section)
                self.assertIn("PASS/FAIL", section)
                self.assertIn("file", section.lower() if path.endswith("/BEGINNER_START.md")
                              and "/ru/" not in path else section.lower().replace("файл", "file"))
                self.assertTrue(any(word in section.lower() for word in
                                    ("permission", "authorized", "разрешени")))
                self.assertNotIn("model_tokens=PASS", section)
                # Deliberate negative mutation: no evidence labels means no acceptance.
                broken = section.replace("NOT_RUN", "UNVERIFIED")
                self.assertNotIn("NOT_RUN", broken)

    def test_all_six_tasks_and_four_routes_exist_in_both_languages(self):
        for path, (task_heading, labels, access_heading, access_labels) in self.ROUTES.items():
            with self.subTest(path=path):
                content = (ROOT / path).read_text(encoding="utf-8")
                tasks = self.rows(self.section(content, task_heading))
                access = self.rows(self.section(content, access_heading))
                self.assertEqual(tuple(name for name, _ in tasks), labels)
                self.assertEqual(tuple(name for name, _ in access), access_labels)
                for _, value in tasks + access:
                    self.assertGreater(len(value), 65)
                self.assertIn("NOT_TESTED", self.section(content, access_heading))
                self.assertIn("--apply", self.section(content, access_heading))

    def test_links_are_safe_existing_local_files(self):
        import re
        from urllib.parse import unquote
        for path, (task_heading, _, access_heading, _) in self.ROUTES.items():
            document = ROOT / path
            content = document.read_text(encoding="utf-8")
            for title in (task_heading, access_heading):
                block = self.section(content, title)
                links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", block)
                self.assertGreaterEqual(len(links), 5)
                for link in links:
                    with self.subTest(doc=path, link=link):
                        target = unquote(link.split("#", 1)[0])
                        if not target:
                            self.assertTrue(link.startswith("#"))
                            continue
                        self.assertFalse(target.startswith(("/", "\\")))
                        self.assertNotIn(":", target)
                        file = (document.parent / target).resolve()
                        self.assertTrue(file.is_relative_to(ROOT.resolve()))
                        self.assertTrue(file.is_file())
                        self.assertFalse((document.parent / target).is_symlink())

    def test_profiles_come_from_existing_manifest(self):
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertTrue(set(self.PROFILE_MAP.values()) <= set(manifest["profiles"]))

    def test_missing_task_or_repeated_heading_fails_contract(self):
        doc = (ROOT / "docs/BEGINNER_START.md").read_text(encoding="utf-8")
        title, _, _, _ = self.ROUTES["docs/BEGINNER_START.md"]
        block = self.section(doc, title)
        rows = self.rows(block)
        self.assertEqual(6, len(rows))
        removed = block.replace("**SEO**", "**Other**", 1)
        self.assertNotEqual([name for name, _ in self.rows(removed)],
                            list(self.ROUTES["docs/BEGINNER_START.md"][1]))
        with self.assertRaises(ValueError):
            self.section(doc + "\n" + title + "\n", title)



if __name__ == "__main__":
    unittest.main()
