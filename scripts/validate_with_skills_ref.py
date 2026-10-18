#!/usr/bin/env python3
"""Validate every bundled skill with the separately installed official skills-ref.

The upstream reference implementation describes itself as demonstrative, not a
production security scanner. This tool never downloads or executes an installer.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def skill_directories(root: Path = ROOT, scope: str = "all") -> list[Path]:
    """Discover declared skills, including QA and Make Feature extension packs."""
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    paths = [
        root / ".agents" / "skills" / name
        for name in manifest["core_skills"] + manifest.get("extension_skills", [])
    ]
    if scope == "all":
        for pack in manifest.get("extension_packs", {}).values():
            paths.extend(root / pack["skill_root"] / name for name in pack["skills"])
        paths.extend(sorted((root / "optional-original-skills").glob("*/SKILL.md")))
    if scope not in ("core", "all"):
        raise ValueError(f"Unsupported scope: {scope}")
    directories = [p.parent if p.name == "SKILL.md" else p for p in paths]
    if len(directories) != len({str(p) for p in directories}):
        raise ValueError("Duplicate skills in declared inventory")
    missing = [str(p) for p in directories if not (p / "SKILL.md").is_file()]
    if missing:
        raise FileNotFoundError(f"Missing declared SKILL.md files: {missing}")
    return directories


def run(scope: str = "all", root: Path = ROOT) -> int:
    binary = shutil.which("skills-ref")
    if binary is None:
        print("NOT RUN: upstream skills-ref not on PATH", file=sys.stderr)
        return 2
    try:
        folders = skill_directories(root, scope)
    except (OSError, ValueError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    failures = []
    for folder in folders:
        try:
            proc = subprocess.run(
                [binary, "validate", str(folder)],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=30, check=False,
            )
            if proc.returncode:
                failures.append((folder.name, proc.stdout.strip(), proc.stderr.strip()))
        except (OSError, subprocess.TimeoutExpired) as exc:
            failures.append((folder.name, "", str(exc)))
    for name, stdout, stderr in failures:
        print(f"FAIL: {name}: {stdout} {stderr}")
    print(f"UPSTREAM CHECKS: {len(folders) - len(failures)}/{len(folders)} passed")
    return int(bool(failures))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=["core", "all"], default="all")
    args = parser.parse_args()
    sys.exit(run(args.scope))
