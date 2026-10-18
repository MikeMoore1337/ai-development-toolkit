#!/usr/bin/env python3
"""Read-only, conservative profile suggestions for an existing project.

This tool examines well-known file names, not private source contents.
It never installs anything or contacts a network service.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ("feature", "ui", "qa", "ci", "release", "docs", "agent")


def recommend(target: Path, task: str, manifest: dict) -> dict:
    if not target.is_dir():
        raise ValueError("Target must be an existing directory")
    if task not in TASKS:
        raise ValueError(f"Unsupported task: {task}")
    python_markers = ("pyproject.toml", "pytest.ini", "setup.py", "requirements.txt")
    js_markers = ("package.json", "tsconfig.json", "vite.config.ts")
    playwright_markers = ("playwright.config.ts", "playwright.config.js", "playwright.config.mjs")
    has_py = any((target / marker).is_file() for marker in python_markers)
    has_js = any((target / marker).is_file() for marker in js_markers)
    has_playwright = any((target / marker).is_file() for marker in playwright_markers)
    observed = {
        "python": has_py,
        "javascript": has_js,
        "playwright_config": has_playwright,
        "go": (target / "go.mod").is_file(),
    }
    if task == "qa":
        if has_py and has_js:
            chosen, why = "qa-fullstack", "Python and JavaScript configuration detected"
        elif has_py:
            chosen, why = "qa-python", "Python configuration detected"
        elif has_js and has_playwright:
            chosen, why = "qa-ui", "JavaScript and Playwright configuration detected"
        else:
            chosen, why = "qa-core", "No supported language-specific QA stack confidently detected"
    else:
        chosen, why = {
            "feature": ("codex-feature", "General-purpose implementation workflow"),
            "ui": ("ui-fix", "User-selected interface work"),
            "ci": ("qa-ci", "User-selected CI or flaky-test diagnosis"),
            "release": ("qa-release", "User-selected release quality review"),
            "docs": ("editorial", "User-selected documentation editing"),
            "agent": ("agent-architecture", "User-selected agent architecture work"),
        }[task]
    profiles = manifest.get("profiles", {})
    if chosen not in profiles:
        raise ValueError(f"Profile missing from MANIFEST.json: {chosen}")
    return {
        "task": task,
        "profile": chosen,
        "skills": profiles[chosen],
        "reason": why,
        "detected": observed,
        "read_only": True,
        "confidence": "heuristic",
        "note": "Verify project rules and choose explicitly before running install.py --apply.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--task", choices=TASKS, required=True)
    args = parser.parse_args()
    try:
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        result = recommend(args.target.expanduser(), args.task, manifest)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
