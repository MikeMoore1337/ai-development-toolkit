#!/usr/bin/env python3
"""Fail-closed structural checks using the independently installed official skills-ref.

Install from the pinned *upstream Git commit* documented in AGENT_SKILLS_SPEC.md.
This command never downloads dependencies, invokes agents, or executes skill scripts.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIMEOUT = 15


def skill_directories(root: Path = ROOT, scope: str = "all") -> list[Path]:
    """Require one real SKILL.md per declared skill, with no unlisted directories."""
    if scope not in ("core", "all"):
        raise ValueError(f"Unsupported scope: {scope}")
    root = root.resolve()
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    core_root = root / ".agents" / "skills"
    core_names = manifest["core_skills"] + manifest.get("extension_skills", [])
    collections = [(core_root, core_names, "core")]
    if scope == "all":
        for pack_name, pack in manifest.get("extension_packs", {}).items():
            collections.append((root / pack["skill_root"], pack["skills"], pack_name))
        legacy_root = root / "optional-original-skills"
        legacy = sorted(p.name for p in legacy_root.iterdir() if p.is_dir()) if legacy_root.is_dir() else []
        expected_legacy = manifest.get("original_skills_bundled_as_opt_in", 0)
        if len(legacy) != expected_legacy:
            raise ValueError(f"Optional original inventory mismatch: expected {expected_legacy}, found {len(legacy)}")
        if legacy:
            collections.append((legacy_root, legacy, "optional-original"))
    directories = []
    used_names = set()
    for base, names, label in collections:
        if not isinstance(names, list) or not all(isinstance(name, str) and name and name not in (".", "..")
                                                and "/" not in name and "\\" not in name for name in names):
            raise ValueError(f"Invalid skill names in {label} manifest")
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate skills in {label} manifest")
        actual = sorted(p.name for p in base.iterdir() if p.is_dir()) if base.is_dir() else []
        missing_names = sorted(set(names) - set(actual))
        if missing_names:
            raise FileNotFoundError(f"Missing declared skill directories in {label}: {missing_names}")
        if actual != sorted(names):
            raise ValueError(f"{label} skill inventory mismatch: declared={sorted(names)}, present={actual}")
        for name in names:
            if name in used_names:
                raise ValueError(f"Duplicate skill name across packs: {name}")
            used_names.add(name)
            folder = base / name
            skill_md = folder / "SKILL.md"
            if folder.is_symlink() or skill_md.is_symlink() or not folder.resolve().is_relative_to(root):
                raise ValueError(f"Unsafe skill path: {folder}")
            if not skill_md.is_file():
                raise FileNotFoundError(f"Missing declared SKILL.md: {skill_md}")
            directories.append(folder)
    if not directories:
        raise ValueError("No skills in selected manifest scope")
    return directories


def run(scope: str = "all", root: Path = ROOT, timeout: float = DEFAULT_TIMEOUT) -> int:
    """Invoke CLI on *every* skill and require its documented success confirmation."""
    try:
        folders = skill_directories(root, scope)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: inventory: {exc}", file=sys.stderr)
        print("UPSTREAM CHECKS: total=0 passed=0 failed=1 (inventory)", file=sys.stderr)
        return 1
    binary = shutil.which("skills-ref")
    if binary is None:
        print("FAIL: official skills-ref not on PATH (no checks executed)", file=sys.stderr)
        print(f"UPSTREAM CHECKS: total={len(folders)} passed=0 failed={len(folders)}", file=sys.stderr)
        return 2
    if timeout <= 0:
        print("FAIL: timeout must be positive", file=sys.stderr)
        return 2

    failures = []
    for folder in folders:
        try:
            proc = subprocess.run(
                [binary, "validate", str(folder)],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=timeout, check=False,
            )
            # The pinned official CLI emits this exact line on successful validation.
            # A stub/no-op command returning 0 without validating must not pass.
            expected = f"Valid skill: {folder}"
            if proc.returncode != 0 or proc.stdout.strip() != expected:
                failures.append((folder, f"exit={proc.returncode}; stdout={proc.stdout.strip()!r}; stderr={proc.stderr.strip()!r}"))
        except subprocess.TimeoutExpired:
            failures.append((folder, f"validator timed out after {timeout:g}s"))
        except OSError as exc:
            failures.append((folder, f"validator execution error: {exc}"))
    for folder, why in failures:
        print(f"FAIL: {folder.relative_to(root.resolve())}: {why}", file=sys.stderr)
    passed = len(folders) - len(failures)
    print(f"UPSTREAM CHECKS: total={len(folders)} passed={passed} failed={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("core", "all"), default="all")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Timeout per skill in seconds")
    args = parser.parse_args()
    sys.exit(run(args.scope, timeout=args.timeout))
