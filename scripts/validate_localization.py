#!/usr/bin/env python3
"""Offline checks for the Russian documentation entry and first-run commands.

These checks validate paths and documented CLI shapes, not translation quality,
client discovery, live activation, release rights, or semantic equivalence.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "README.md",
    "README.ru.md",
    "docs/ru/README.md",
    "docs/ru/BUSINESS_SYSTEM_ANALYSIS.md",
    "docs/BUSINESS_SYSTEM_ANALYSIS.md",
    "docs/UX_UI_DESIGN.md",
    "docs/ru/UX_UI_DESIGN.md",
    "docs/ru/GETTING_STARTED.md",
    "docs/ru/GLOSSARY.md",
    "docs/ru/INSTALLATION.md",
    "docs/ru/SKILLS_CATALOG.md",
    "docs/ru/CURATED_SKILL_PACKS.md",
    "docs/ru/CLIENT_MIGRATION.md",
    "docs/ru/CLIENT_COMPATIBILITY.md",
    "docs/ru/PUBLICATION_POLICY.md",
    "docs/ru/ACCEPTANCE.md",
    "docs/ru/MAKE_FEATURE_INTEGRATION.md",
    "docs/ru/LANGUAGE_POLICY.md",
    "docs/ru/BEGINNER_WORKFLOW.md",
    "docs/ru/QUALITY_RUBRIC.md",
    "docs/ru/CLEAR_VOICE_INTEGRATION.md",
    "docs/ru/UNIVERSAL_ENGINEERING.md",
    "docs/ru/SKILL_QUALITY_V2.md",
    "docs/ru/SKILL_QUALITY_METRICS.md",
    "docs/ru/AGENT_SKILLS_SPEC.md",
    "docs/ru/RELEASE_PROCESS.md",
    "docs/en/SOURCE_EVALUATION.md",
    "docs/INSTALLATION.md",
    "docs/SKILLS_CATALOG.md",
    "docs/CURATED_SKILL_PACKS.md",
    "docs/CLIENT_MIGRATION.md",
    "docs/CLIENT_COMPATIBILITY.md",
    "docs/PUBLICATION_POLICY.md",
    "docs/MAKE_FEATURE_INTEGRATION.md",
    "docs/LANGUAGE_POLICY.md",
    "docs/BEGINNER_WORKFLOW.md",
    "docs/QUALITY_RUBRIC.md",
    "docs/CLEAR_VOICE_INTEGRATION.md",
    "docs/UNIVERSAL_ENGINEERING.md",
    "docs/SKILL_QUALITY_V2.md",
    "docs/SKILL_QUALITY_METRICS.md",
    "docs/AGENT_SKILLS_SPEC.md",
    "docs/RELEASE_PROCESS.md",
    "docs/SOURCE_EVALUATION.md",
    "docs/ADAPTATION.md",
    "docs/INTEGRATION_MATRIX.md",
    "docs/PORTABILITY_EVAL_SCENARIOS.md",
    "docs/TASK_PROMPT_TEMPLATE.md",
    "docs/en/ADAPTATION.md",
    "docs/en/INTEGRATION_MATRIX.md",
    "docs/en/PORTABILITY_EVAL_SCENARIOS.md",
    "docs/en/TASK_PROMPT_TEMPLATE.md",
)
TRANSLATED_PAGES = tuple(page for page in PAGES if page.startswith(("docs/ru/", "docs/en/")))
CATALOG_SKILLS = re.compile(r"^\| \[`([^`]+)`\]\([^)]+\) \|", re.M)
CATALOG_PROFILES = re.compile(r"^\| `([a-z][a-z0-9-]*)` \|", re.M)
CATALOG_ROLES = re.compile(r"^\| (?:Core|QA) \| `([a-z][a-z0-9-]*)` \|", re.M)
SAMPLE_COMMANDS = re.compile(
    r"^\s*(?:python|py -3) scripts/(?:skill_manager|recommend_profile|profile_metrics|install)\.py(?: .*)?$",
    re.M,
)
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\s]+)")
LANGUAGE_LINKS = {
    "README.md": "(README.ru.md)",
    "README.ru.md": "(README.md)",
    "docs/ru/README.md": "(../../README.md)",
    "docs/INSTALLATION.md": "(ru/INSTALLATION.md)",
    "docs/SKILLS_CATALOG.md": "(ru/SKILLS_CATALOG.md)",
    "docs/BUSINESS_SYSTEM_ANALYSIS.md": "(ru/BUSINESS_SYSTEM_ANALYSIS.md)",
    "docs/UX_UI_DESIGN.md": "(ru/UX_UI_DESIGN.md)",
    "docs/ru/UX_UI_DESIGN.md": "(../UX_UI_DESIGN.md)",
    "docs/ru/BUSINESS_SYSTEM_ANALYSIS.md": "(../BUSINESS_SYSTEM_ANALYSIS.md)",
    "docs/CURATED_SKILL_PACKS.md": "(ru/CURATED_SKILL_PACKS.md)",
    "docs/CLIENT_MIGRATION.md": "(ru/CLIENT_MIGRATION.md)",
    "docs/CLIENT_COMPATIBILITY.md": "(ru/CLIENT_COMPATIBILITY.md)",
    "docs/PUBLICATION_POLICY.md": "(ru/PUBLICATION_POLICY.md)",
    "docs/MAKE_FEATURE_INTEGRATION.md": "(ru/MAKE_FEATURE_INTEGRATION.md)",
    "docs/LANGUAGE_POLICY.md": "(ru/LANGUAGE_POLICY.md)",
    "docs/BEGINNER_WORKFLOW.md": "(ru/BEGINNER_WORKFLOW.md)",
    "docs/QUALITY_RUBRIC.md": "(ru/QUALITY_RUBRIC.md)",
    "docs/CLEAR_VOICE_INTEGRATION.md": "(ru/CLEAR_VOICE_INTEGRATION.md)",
    "docs/UNIVERSAL_ENGINEERING.md": "(ru/UNIVERSAL_ENGINEERING.md)",
    "docs/SKILL_QUALITY_V2.md": "(ru/SKILL_QUALITY_V2.md)",
    "docs/SKILL_QUALITY_METRICS.md": "(ru/SKILL_QUALITY_METRICS.md)",
    "docs/AGENT_SKILLS_SPEC.md": "(ru/AGENT_SKILLS_SPEC.md)",
    "docs/RELEASE_PROCESS.md": "(ru/RELEASE_PROCESS.md)",
    "docs/SOURCE_EVALUATION.md": "(en/SOURCE_EVALUATION.md)",
    "docs/en/SOURCE_EVALUATION.md": "(../SOURCE_EVALUATION.md)",
    "docs/ADAPTATION.md": "(en/ADAPTATION.md)",
    "docs/INTEGRATION_MATRIX.md": "(en/INTEGRATION_MATRIX.md)",
    "docs/PORTABILITY_EVAL_SCENARIOS.md": "(en/PORTABILITY_EVAL_SCENARIOS.md)",
    "docs/TASK_PROMPT_TEMPLATE.md": "(en/TASK_PROMPT_TEMPLATE.md)",
    "docs/en/ADAPTATION.md": "(../ADAPTATION.md)",
    "docs/en/INTEGRATION_MATRIX.md": "(../INTEGRATION_MATRIX.md)",
    "docs/en/PORTABILITY_EVAL_SCENARIOS.md": "(../PORTABILITY_EVAL_SCENARIOS.md)",
    "docs/en/TASK_PROMPT_TEMPLATE.md": "(../TASK_PROMPT_TEMPLATE.md)",
    "docs/ru/INSTALLATION.md": "(../INSTALLATION.md)",
    "docs/ru/SKILLS_CATALOG.md": "(../SKILLS_CATALOG.md)",
    "docs/ru/CURATED_SKILL_PACKS.md": "(../CURATED_SKILL_PACKS.md)",
    "docs/ru/CLIENT_MIGRATION.md": "(../CLIENT_MIGRATION.md)",
    "docs/ru/CLIENT_COMPATIBILITY.md": "(../CLIENT_COMPATIBILITY.md)",
    "docs/ru/PUBLICATION_POLICY.md": "(../PUBLICATION_POLICY.md)",
    "docs/ru/MAKE_FEATURE_INTEGRATION.md": "(../MAKE_FEATURE_INTEGRATION.md)",
    "docs/ru/LANGUAGE_POLICY.md": "(../LANGUAGE_POLICY.md)",
    "docs/ru/BEGINNER_WORKFLOW.md": "(../BEGINNER_WORKFLOW.md)",
    "docs/ru/QUALITY_RUBRIC.md": "(../QUALITY_RUBRIC.md)",
    "docs/ru/CLEAR_VOICE_INTEGRATION.md": "(../CLEAR_VOICE_INTEGRATION.md)",
    "docs/ru/UNIVERSAL_ENGINEERING.md": "(../UNIVERSAL_ENGINEERING.md)",
    "docs/ru/SKILL_QUALITY_V2.md": "(../SKILL_QUALITY_V2.md)",
    "docs/ru/SKILL_QUALITY_METRICS.md": "(../SKILL_QUALITY_METRICS.md)",
    "docs/ru/AGENT_SKILLS_SPEC.md": "(../AGENT_SKILLS_SPEC.md)",
    "docs/ru/RELEASE_PROCESS.md": "(../RELEASE_PROCESS.md)",
}


def validate(root: Path) -> list[str]:
    """Return deterministic, machine-readable rule identifiers and locations."""
    errors: list[str] = []
    root = root.resolve()
    for relative in PAGES:
        if not (root / relative).is_file():
            errors.append(f"L10N001 {relative}: missing required page")

    for relative in TRANSLATED_PAGES:
        page = root / relative
        if not page.is_file():
            continue
        for match in LINK.finditer(page.read_text(encoding="utf-8")):
            raw = match.group(1)
            url = urlsplit(raw)
            if url.scheme or url.netloc or raw.startswith("#"):
                continue
            path = unquote(url.path)
            if not path:
                continue
            target = (page.parent / path).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                errors.append(f"L10N002 {relative}: invalid local link {raw}")

    for relative, expected in LANGUAGE_LINKS.items():
        file = root / relative
        if file.is_file() and expected not in file.read_text(encoding="utf-8"):
            errors.append(f"L10N004 {relative}: missing reverse language link")

    russian_readme = root / "README.ru.md"
    if russian_readme.is_file():
        content = russian_readme.read_text(encoding="utf-8")
        for path in ("docs/ru/README.md", "docs/ru/GETTING_STARTED.md",
                     "docs/ru/INSTALLATION.md", "docs/ru/SKILLS_CATALOG.md",
                     "docs/ru/ACCEPTANCE.md", "docs/ru/MAKE_FEATURE_INTEGRATION.md",
                     "docs/ru/LANGUAGE_POLICY.md",
                     "docs/ru/BEGINNER_WORKFLOW.md",
                     "docs/ru/CLEAR_VOICE_INTEGRATION.md",
                     "docs/ru/SKILL_QUALITY_V2.md",
                     "docs/ru/UNIVERSAL_ENGINEERING.md",
                     "docs/ru/AGENT_SKILLS_SPEC.md", "docs/ru/RELEASE_PROCESS.md"):
            if f"({path})" not in content:
                errors.append(f"L10N004 README.ru.md: missing localized entry {path}")

    intro = root / "docs/ru/README.md"
    if intro.is_file():
        content = intro.read_text(encoding="utf-8")
        for path in ("GETTING_STARTED.md", "GLOSSARY.md", "INSTALLATION.md",
                     "SKILLS_CATALOG.md", "CURATED_SKILL_PACKS.md",
                     "CLIENT_MIGRATION.md", "CLIENT_COMPATIBILITY.md",
                     "PUBLICATION_POLICY.md", "ACCEPTANCE.md",
                     "MAKE_FEATURE_INTEGRATION.md", "LANGUAGE_POLICY.md",
                     "BEGINNER_WORKFLOW.md", "QUALITY_RUBRIC.md",
                     "CLEAR_VOICE_INTEGRATION.md",
                     "UNIVERSAL_ENGINEERING.md", "SKILL_QUALITY_V2.md",
                     "SKILL_QUALITY_METRICS.md",
                     "AGENT_SKILLS_SPEC.md", "RELEASE_PROCESS.md",
                     "../en/SOURCE_EVALUATION.md"):
            if f"({path})" not in content:
                errors.append(f"L10N004 docs/ru/README.md: missing {path}")

    start = root / "docs/ru/GETTING_STARTED.md"
    if start.is_file():
        content = start.read_text(encoding="utf-8")
        for python, target in (("python", "../toolkit-demo"), ("py -3", r"..\toolkit-demo")):
            prefix = f"{python} scripts/skill_manager.py"
            commands = (
                f"{prefix} catalog",
                f"{prefix} install --target {target} --profile general",
                f"{prefix} install --target {target} --profile general --apply",
                f"{prefix} status --target {target}",
            )
            positions = [content.find(command + "\n") for command in commands]
            if any(position < 0 for position in positions) or not (
                positions[1] < positions[2] < positions[3]
            ):
                errors.append(f"L10N003 docs/ru/GETTING_STARTED.md: broken preview/apply/status for {python}")
        for token in ("Python", "Codex", "Claude Code", "AGENTS.md", "CLAUDE.md", "--layout claude"):
            if token not in content:
                errors.append(f"L10N003 docs/ru/GETTING_STARTED.md: missing safety/context token {token}")
    # Inventories are canonical in English. This checks presence of every
    # documented identifier, not whether its Russian description is accurate.
    source = root / "docs/SKILLS_CATALOG.md"
    translated = root / "docs/ru/SKILLS_CATALOG.md"
    if source.is_file() and translated.is_file():
        en = source.read_text(encoding="utf-8")
        ru = translated.read_text(encoding="utf-8")
        for rule, pattern in (
            ("skills", CATALOG_SKILLS),
            ("roles", CATALOG_ROLES),
            ("profiles", CATALOG_PROFILES),
        ):
            # Profile names appear exclusively in the profiles section.
            section_en = en.split("## Profiles", 1)[-1] if rule == "profiles" else en
            section_ru = ru.split("## Профили", 1)[-1] if rule == "profiles" else ru
            before = pattern.findall(section_en)
            after = pattern.findall(section_ru)
            if len(after) != len(before) or sorted(after) != sorted(before):
                errors.append(f"L10N005 docs/ru/SKILLS_CATALOG.md: {rule} differ from English")

    for name in ("INSTALLATION.md", "CURATED_SKILL_PACKS.md", "CLIENT_MIGRATION.md",
                 "MAKE_FEATURE_INTEGRATION.md", "BEGINNER_WORKFLOW.md",
                 "CLEAR_VOICE_INTEGRATION.md", "UNIVERSAL_ENGINEERING.md"):
        source = root / "docs" / name
        target = root / "docs/ru" / name
        if source.is_file() and target.is_file():
            original_commands = set(SAMPLE_COMMANDS.findall(source.read_text(encoding="utf-8")))
            translated_commands = set(SAMPLE_COMMANDS.findall(target.read_text(encoding="utf-8")))
            if not original_commands.issubset(translated_commands):
                errors.append(f"L10N006 docs/ru/{name}: executable examples differ from English")

    # The metrics guide has its own read-only CLI examples, not covered by
    # the general installer command matcher. Compare their exact shapes.
    metrics_source = root / "docs/SKILL_QUALITY_METRICS.md"
    metrics_ru = root / "docs/ru/SKILL_QUALITY_METRICS.md"
    if metrics_source.is_file() and metrics_ru.is_file():
        regex = re.compile(r"^\s*python scripts/skill_quality_metrics\.py(?: .*)?$", re.M)
        before = {line.strip() for line in regex.findall(metrics_source.read_text(encoding="utf-8"))}
        after = {line.strip() for line in regex.findall(metrics_ru.read_text(encoding="utf-8"))}
        if not before.issubset(after):
            errors.append("L10N006 docs/ru/SKILL_QUALITY_METRICS.md: metrics CLI examples differ from English")

    # Examples and high-risk caveats must not disappear during translation.
    source = root / "docs/CLIENT_COMPATIBILITY.md"
    translation = root / "docs/ru/CLIENT_COMPATIBILITY.md"
    cmd = re.compile(r"^\s*python scripts/verify_client_compatibility\.py(?: .*)?$", re.M)
    if source.is_file() and translation.is_file():
        before = {command.strip() for command in cmd.findall(source.read_text(encoding="utf-8"))}
        after = {command.strip() for command in cmd.findall(translation.read_text(encoding="utf-8"))}
        if not before.issubset(after):
            errors.append("L10N006 docs/ru/CLIENT_COMPATIBILITY.md: executable examples differ from English")

    required_tokens = {
        "CLIENT_MIGRATION.md": ("--apply", "rollback", "recover", "AGENTS.md", "CLAUDE.md"),
        "CLIENT_COMPATIBILITY.md": ("L4", "L5", "L6", "NOT_TESTED", "UNSUPPORTED"),
        "PUBLICATION_POLICY.md": ("ID1337", "--mode release", "SHA256"),
        "ACCEPTANCE.md": ("NOT_TESTED", "preview", "apply", "status"),
        "MAKE_FEATURE_INTEGRATION.md": ("--apply", "feature-delivery", "NOT_TESTED",
                                        "INDEPENDENT_REVIEW", "Artemiy Miller"),
        "LANGUAGE_POLICY.md": ("SKILL.md", "Make Feature", "SOURCE_REVISIONS.json"),
        "BEGINNER_WORKFLOW.md": ("NOT_RUN", "BLOCKED", "NOT_TESTED", "NOT_MEASURED",
                               "feature-delivery", "make-feature", "--apply", "EXTERNAL",
                               "UNSUPPORTED", "NOT_DONE"),
        "CLEAR_VOICE_INTEGRATION.md": ("--apply", "NOT_TESTED", "SKILL.md",
                                       "ru-primary-en-secondary", "права"),
        "UNIVERSAL_ENGINEERING.md": ("NOT_MEASURED", "WF001", "feature-delivery",
                                      "make-feature", "--apply", "AGENTS.md", "CLAUDE.md"),
        "SKILL_QUALITY_METRICS.md": ("NOT_MEASURED", "NOT_APPLICABLE",
                                     "--check-repeat", "--json-report",
                                     "model_tokens", "51/51", "skills-ref"),
        "SKILL_QUALITY_V2.md": ("NOT_MEASURED", "NOT_APPLICABLE", "EVIDENCE001",
                                "source_revision", "reviewed_by", "observed_at",
                                "INDEPENDENT_REVIEW_PENDING", "Issue #11"),
        "AGENT_SKILLS_SPEC.md": ("skills-ref", "--scope all", "MANIFEST.json",
                                 "76", "0.1.0", "3.11"),
        "RELEASE_PROCESS.md": ("ID1337", "--mode release", "BLOCKED",
                               "NOT_VERIFIED", "SHA256SUMS.txt", "MANIFEST.json"),
        "QUALITY_RUBRIC.md": ("verified", "unknown", "failed", "BLOCKER", "WARNING",
                              "NOT_MEASURED", "--mode inventory", "--mode release",
                              "0.17.1", "1.7.12"),
    }
    for name, tokens in required_tokens.items():
        target = root / "docs/ru" / name
        if target.is_file():
            content = target.read_text(encoding="utf-8")
            if any(token not in content for token in tokens):
                errors.append(f"L10N009 docs/ru/{name}: missing safety or evidence boundary")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    issues = validate(args.root)
    for issue in issues:
        print(issue)
    if issues:
        return 1
    print("RU onboarding localization: PASS (paths/navigation/CLI samples only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
