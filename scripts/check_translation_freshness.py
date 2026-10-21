#!/usr/bin/env python3
"""Report stale Russian documentation sources without blocking unrelated changes.

Only exact, safe, repository-local source/translation pairs are accepted.
Existing entries default to an English source; source_language='ru' selects
a Russian original and its docs/en/ counterpart.
This checks revision age, not translation meaning, skill activation, or rights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISIONS = Path("docs/ru/SOURCE_REVISIONS.json")
CHECKSUM = re.compile(r"^[0-9a-f]{64}$")
EN_PATH = re.compile(r"^docs/[A-Z0-9_]+\.md$")


def check(root: Path = ROOT) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    root = root.resolve()
    try:
        info = json.loads((root / REVISIONS).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"L10N007: cannot read source revision metadata ({type(exc).__name__})"], []

    if (not isinstance(info, dict) or info.get("schema_version") != 1
            or not isinstance(info.get("pairs"), list) or not info["pairs"]):
        return ["L10N007: invalid source revision metadata"], []

    seen: set[str] = set()
    for entry in info["pairs"]:
        if not isinstance(entry, dict):
            errors.append("L10N007: invalid revision entry")
            continue
        source = entry.get("source")
        translated = entry.get("translation")
        expected = entry.get("source_sha256")
        source_language = entry.get("source_language", "en")
        destination_language = {"en": "ru", "ru": "en"}.get(source_language)
        if (not isinstance(source, str) or not EN_PATH.fullmatch(source)
                or destination_language is None
                or translated != source.replace("docs/", f"docs/{destination_language}/", 1)
                or not isinstance(expected, str) or not CHECKSUM.fullmatch(expected)
                or source in seen):
            errors.append("L10N007: unsafe, duplicate or malformed revision entry")
            continue
        seen.add(source)
        original = root / source
        localized = root / translated
        if original.is_symlink() or localized.is_symlink() or not original.is_file() or not localized.is_file():
            errors.append(f"L10N007: missing or linked translation pair {source}")
            continue
        data = original.read_bytes().replace(b"\r\n", b"\n")
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            warnings.append(f"L10N008: review translation {translated} because {source} changed")
    return errors, warnings



def coverage(root: Path = ROOT) -> tuple[int, int, list[str]]:
    """Return deterministic filename coverage; this does not verify translation meaning.

    Russian-first sources may have their counterpart in docs/en/. Historical
    and specialized sources without translations are gaps, not CI failures.
    """
    base = root.resolve() / "docs"
    if base.is_symlink() or not base.is_dir():
        raise ValueError("Missing or linked docs directory")
    sources = sorted(base.glob("*.md"), key=lambda path: path.name)
    paired = 0
    gaps: list[str] = []
    for source in sources:
        if source.is_symlink() or not source.is_file():
            gaps.append(source.relative_to(root.resolve()).as_posix())
            continue
        if any(
            not directory.is_symlink()
            and (directory / source.name).is_file()
            and not (directory / source.name).is_symlink()
            for directory in (base / "ru", base / "en")
        ):
            paired += 1
        else:
            gaps.append(source.relative_to(root.resolve()).as_posix())
    return len(sources), paired, gaps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--strict", action="store_true",
                        help="Fail on stale sources (manual pre-publication check only)")
    parser.add_argument("--coverage", action="store_true",
                        help="Print all untranslated documentation filenames without failing CI")
    args = parser.parse_args()
    errors, warnings = check(args.root)
    for item in errors:
        print("ERROR: " + item)
    for item in warnings:
        print("WARNING: " + item)
    if not errors and not warnings:
        print("RU translation sources: current revisions (not semantic verification)")
    if args.coverage:
        try:
            total, paired, gaps = coverage(args.root)
        except (OSError, ValueError) as exc:
            print(f"ERROR: L10N_COVERAGE: {type(exc).__name__}")
            return 1
        print(f"DOCUMENTATION_COVERAGE: root={total} paired={paired} unpaired={len(gaps)}")
        for path in gaps:
            print(f"UNPAIRED_DOC: {path}")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
