#!/usr/bin/env python3
"""Read-only, deterministic PR change-impact test advisor (never executes tests)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
# Paths are untrusted: patterns are conservative; ambiguous changes add reviews.
RULES = {
    "authorization": {
        "patterns": [r"(^|/)(auth|security|permissions?)(/|_|\.)", r"(oauth|session|token|access_control|rbac)"],
        "checks": ["authorization-negative", "cross-user-denial", "session-expiry"],
        "risk": "CRITICAL",
        "reason": "Access-control regressions may expose another user's data.",
    },
    "database": {
        "patterns": [r"(migration|alembic|schema|\.sql$|db/|database/)"],
        "checks": ["migration-forward", "migration-rollback", "data-integrity"],
        "risk": "CRITICAL",
        "reason": "Schema changes may irreversibly corrupt or lose data.",
    },
    "api-contract": {
        "patterns": [r"(^|/)(api|routes?|endpoints?)(/|_|\.)", r"(openapi|swagger|\.proto$|contract|event_schema)"],
        "checks": ["api-contract-compatibility", "invalid-request-negative"],
        "risk": "HIGH",
        "reason": "Changed interfaces may break downstream consumers.",
    },
    "frontend": {
        "patterns": [r"(^|/)(ui|frontend|components?|pages?|screens?)(/|_|\.)", r"\.(tsx|jsx|vue|svelte)$"],
        "checks": ["ui-state-regression", "keyboard-accessibility"],
        "risk": "MEDIUM",
        "reason": "Visual/state changes require interaction and accessibility checks.",
    },
    "background": {
        "patterns": [r"(workers?|queue|jobs?|scheduler|tasks?)(/|_|\.)", r"(retry|idempotenc|consumer|producer)"],
        "checks": ["duplicate-delivery", "retry-and-recovery"],
        "risk": "HIGH",
        "reason": "Event retries and replays may duplicate side effects.",
    },
    "deployment": {
        "patterns": [r"(^|/)(deploy|infra|terraform|helm|k8s|compose|\.github/workflows)(/|_|\.)", r"(dockerfile|\.ya?ml$)"],
        "checks": ["deployment-dry-run", "rollback-readiness"],
        "risk": "HIGH",
        "reason": "Infrastructure changes can affect availability and rollback.",
    },
}
RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
CHECKS = {check for rule in RULES.values() for check in rule["checks"]} | {"targeted-unit-regression", "integration-boundary", "change-scope-review"}


def analyze(changed_files: list[str]) -> dict:
    if not isinstance(changed_files, list) or not changed_files:
        raise ValueError("Nonempty changed_files list required")
    if len(changed_files) > 1000:
        raise ValueError("Too many changed files")
    seen = set()
    changed = []
    for p in changed_files:
        if not isinstance(p, str) or not p or len(p) > 512 or "\\ " in p:
            raise ValueError("Invalid file path")
        path = p.replace("\\", "/")
        if path.startswith("/") or ".." in path.split("/") or "\x00" in path:
            raise ValueError("Unsafe changed file path")
        if path not in seen:
            seen.add(path)
            changed.append(path)
    identified, checks, reasons = {}, set(), {}
    for path in changed:
        matched = []
        for category, rule in RULES.items():
            if any(re.search(pattern, path, re.I) for pattern in rule["patterns"]):
                matched.append(category)
                checks.update(rule["checks"])
                for check in rule["checks"]:
                    reasons.setdefault(check, set()).add(path)
        identified[path] = matched
    unknown = [path for path, categories in identified.items() if not categories]
    if unknown:
        checks.add("change-scope-review")
        reasons["change-scope-review"] = set(unknown)
    # Changes to executable code still require scoped unit tests.
    if any(p.endswith((".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java")) for p in changed):
        checks.add("targeted-unit-regression")
        reasons["targeted-unit-regression"] = set(changed)
    if sum(bool(v) for v in identified.values()) > 1 or any(len(v) > 1 for v in identified.values()):
        checks.add("integration-boundary")
        reasons["integration-boundary"] = set(changed)
    risk = max((RULES[cat]["risk"] for cats in identified.values() for cat in cats), key=RANK.get, default="LOW")
    return {
        "classification": "OFFLINE_CHANGE_IMPACT_ADVICE",
        "execution": "NOT_RUN",
        "ci_evidence": "NOT_OBSERVED",
        "production_evidence": "NOT_OBSERVED",
        "changed_files": changed,
        "risk": risk,
        "matched_surfaces": identified,
        "recommended_checks": [
            {"check": check, "execution": "NOT_RUN", "evidence": sorted(reasons.get(check, []))}
            for check in sorted(checks)
        ],
        "unknown_scope": sorted(unknown),
        "limitations": [
            "Filename heuristics do not inspect source content, imports or runtime callers.",
            "Recommendations are not evidence that pytest, Playwright, CI or deployment ran.",
            "Unknown callers and external consumers require manual review.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths-json", type=Path, required=True, help="JSON list of changed relative paths")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.paths_json.read_text(encoding="utf-8"))
        result = analyze(data)
    except (OSError, ValueError, TypeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
