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
    "docs/ru/GETTING_STARTED.md",
    "docs/ru/GLOSSARY.md",
)
RU_PAGES = PAGES[2:]
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\s]+)")
LANGUAGE_LINKS = {
    "README.md": "(README.ru.md)",
    "README.ru.md": "(README.md)",
    "docs/ru/README.md": "(../../README.md)",
}


def validate(root: Path) -> list[str]:
    """Return deterministic, machine-readable rule identifiers and locations."""
    errors: list[str] = []
    root = root.resolve()
    for relative in PAGES:
        if not (root / relative).is_file():
            errors.append(f"L10N001 {relative}: missing required page")

    for relative in RU_PAGES:
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
        for path in ("docs/ru/README.md", "docs/ru/GETTING_STARTED.md"):
            if f"({path})" not in content:
                errors.append(f"L10N004 README.ru.md: missing localized entry {path}")

    intro = root / "docs/ru/README.md"
    if intro.is_file():
        content = intro.read_text(encoding="utf-8")
        for path in ("GETTING_STARTED.md", "GLOSSARY.md"):
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
