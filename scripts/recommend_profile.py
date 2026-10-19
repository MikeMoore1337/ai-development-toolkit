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
TASKS = ("feature", "ui", "qa", "ci", "release", "docs", "agent",
         "backend", "frontend", "fullstack", "research", "provider",
         "docs-edit", "docs-verify")

# Explicit, non-installing suggestions; the primary profile stays minimal.
OPTIONAL_SKILLS = {
    "backend": ("data-access", "database-migrations", "background-processing",
                "authentication-authorization", "contract-testing",
                "database-validation", "release-safety"),
    "frontend": ("state-management", "forms-validation", "frontend-performance",
                 "screenshot-fidelity", "motion-quality", "playwright-testing"),
    "fullstack": ("cross-layer-debugging", "contract-testing", "e2e-testing"),
    "agent": ("security-boundaries", "external-skill-review"),
    "research": ("codebase-knowledge-map", "provider-reality-check"),
    "provider": ("architecture-decisions",),
    "docs": ("clear-voice",),
    "docs-verify": ("clear-voice",),
}
OPTIONAL_PROFILES = {
    "qa": ("qa-ci",),
    "frontend": ("ui-fix", "ui-motion"),
    "fullstack": ("qa-fullstack",),
    "agent": ("provider-research",),
    "research": ("provider-research",),
}


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
    has_pytest_config = (target / "pytest.ini").is_file()
    observed = {
        "python": has_py,
        "javascript": has_js,
        "playwright_config": has_playwright,
        "pytest_config": has_pytest_config,
        "pytest_installed": "NOT_VERIFIED",
        "playwright_installed": "NOT_VERIFIED",
        "go": (target / "go.mod").is_file(),
    }
    warnings = []
    alternatives = []
    if task == "qa":
        if has_py and has_js and has_playwright:
            chosen, why = "qa-fullstack", "Python, JavaScript and Playwright config markers detected"
            warnings.append("Playwright configuration does not confirm that Playwright is installed.")
            warnings.append("pytest availability is NOT_VERIFIED; a Python marker alone is insufficient.")
            alternatives.append("qa-core")
        elif has_py:
            chosen, why = "qa-python", "Python project markers detected; browser QA not assumed"
            warnings.append("pytest availability is NOT_VERIFIED; pytest-test-design needs pytest.")
            alternatives.append("qa-core")
            if has_js:
                warnings.append("JavaScript does not prove Playwright support; qa-fullstack was not selected.")
        elif has_js and has_playwright:
            chosen, why = "qa-ui", "JavaScript and Playwright config markers detected"
            warnings.append("Playwright config does not prove that the dependency is installed.")
            alternatives.append("qa-core")
        else:
            chosen, why = "qa-core", "No supported language-specific QA stack confidently detected"
            if has_js:
                warnings.append("JavaScript project alone is not evidence of Playwright.")
    else:
        chosen, why = {
            "feature": ("codex-feature", "General-purpose implementation workflow"),
            "ui": ("ui-fix", "User-selected interface work"),
            "ci": ("qa-ci", "User-selected CI or flaky-test diagnosis"),
            "release": ("qa-release", "User-selected release quality review"),
            "docs": ("docs-technical", "Technical documentation maintenance and factual checks"),
            "docs-edit": ("editorial", "Language editing only; not technical verification"),
            "docs-verify": ("docs-technical", "Verify technical documentation against source evidence"),
            "agent": ("agent-architecture", "User-selected agent architecture work"),
            "backend": ("backend", "User-selected backend implementation and review"),
            "frontend": ("frontend", "User-selected frontend implementation; no framework inferred"),
            "fullstack": ("fullstack", "User-selected cross-layer feature work; no technology inferred"),
            "research": ("research", "User-selected technical research and source verification"),
            "provider": ("provider-research", "User-selected LLM API or provider comparison"),
        }[task]
    profiles = manifest.get("profiles", {})
    if chosen not in profiles:
        raise ValueError(f"Profile missing from MANIFEST.json: {chosen}")
    available = set(manifest["core_skills"]) | set(manifest.get("extension_skills", ()))
    for cfg in manifest.get("extension_packs", {}).values():
        available.update(cfg["skills"])
    optional_skills = [name for name in OPTIONAL_SKILLS.get(task, ())
                       if name not in profiles[chosen] and name in available]
    optional_profiles = [name for name in OPTIONAL_PROFILES.get(task, ())
                         if name in profiles and name != chosen]
    return {
        "optional_skills": optional_skills,
        "optional_profiles": optional_profiles,
        "task": task,
        "profile": chosen,
        "skills": profiles[chosen],
        "reason": why,
        "warnings": warnings,
        "alternatives": alternatives,
        "detected": observed,
        "read_only": True,
        "confidence": "heuristic",
        "note": "Heuristic only. Inspect the manager preview before explicit --apply; no dependency was installed or executed.",
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
