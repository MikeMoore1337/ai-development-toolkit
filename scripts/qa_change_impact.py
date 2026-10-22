#!/usr/bin/env python3
"""Read-only, evidence-limited regression selection for changed paths.

This is a planning tool, NOT a test runner, call graph, or quality gate. It
inspects paths in a supplied list or a local exact-SHA git diff, without
reading proprietary project files or accessing the network.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

MAX_PATHS = 200
MAX_PATH_LENGTH = 300
SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
TOKENS = re.compile(r"[a-z0-9]+", re.I)
SURFACES = {
    "AUTH": ("auth", "oauth", "login", "permission", "policy", "tenant", "jwt",
             "session", "rbac", "acl", "credential"),
    "API": ("api", "openapi", "swagger", "graphql", "endpoint", "router",
            "contract", "schema", "serializer", "dto"),
    "DB": ("database", "migrations", "migration", "models", "sql", "alembic",
           "prisma", "db", "persistence", "repository"),
    "UI": ("frontend", "components", "views", "screens", "react", "ui",
           "widget", "forms", "pages", "app"),
    "ASYNC": ("worker", "queue", "task", "jobs", "events", "consumer",
              "producer", "scheduler", "broker"),
    "CI": ("workflows", "docker", "compose", "deploy", "helm", "kubernetes",
           "ci", "infra", "terraform", "pipeline"),
}
# Each rule is explicit and grounded in a changed path, NOT a claim that an
# API schema or a callsite was actually inspected.
CHECKS = {
    "change-review": ("Source-focused review of changed behavior and callers", "LOW"),
    "targeted-unit": ("Targeted unit and relevant negative regressions", "LOW"),
    "api-contract": ("Producer/consumer API and schema backward compatibility", "HIGH"),
    "api-negative": ("Invalid request, authorization and response error handling", "HIGH"),
    "db-migration": ("Migration forward/backward, schema and integrity assertions", "CRITICAL"),
    "db-rollback": ("Recovery, backup/rollback rehearsal or explicit blocker", "CRITICAL"),
    "auth-boundary": ("Deny-by-default auth, cross-tenant and session regressions", "CRITICAL"),
    "privacy-boundary": ("Unauthorized PII exposure and secrets-handling checks", "CRITICAL"),
    "ui-state": ("UI state, keyboard navigation, restoration and focus tests", "HIGH"),
    "browser-flow": ("Critical user journey and accessibility smoke checks", "HIGH"),
    "async-replay": ("Replay, concurrency, idempotency, retries and ordering", "HIGH"),
    "deployment-safety": ("CI safeguards, deploy policy and rollback dry-run", "CRITICAL"),
    "cross-layer": ("End-to-end check across changed frontend/API/DB boundaries", "HIGH"),
    "unmapped-impact": ("Inspect unknown paths and choose concrete risk tests", "UNKNOWN"),
}
RISK_ORDER = {"LOW": 0, "HIGH": 1, "CRITICAL": 2, "UNKNOWN": 3}
RULE_CHECKS = {
    "AUTH": ("auth-boundary", "privacy-boundary", "api-negative"),
    "API": ("api-contract", "api-negative"),
    "DB": ("db-migration", "db-rollback"),
    "UI": ("ui-state", "browser-flow"),
    "ASYNC": ("async-replay",),
    "CI": ("deployment-safety",),
}
CRITICAL_CHECKS = {"auth-boundary", "privacy-boundary",
                   "db-migration", "db-rollback", "deployment-safety"}


class ImpactInputError(ValueError):
    """Untrusted change metadata failed validation."""


def validate_paths(paths: list[str]) -> list[str]:
    if not isinstance(paths, list) or not 1 <= len(paths) <= MAX_PATHS:
        raise ImpactInputError("Expected 1..200 changed paths")
    normalized = []
    for path in paths:
        if not isinstance(path, str) or not path or len(path) > MAX_PATH_LENGTH:
            raise ImpactInputError("Invalid changed path")
        value = path.replace("\\", "/")
        # Never silently rewrite traversal, absolute paths or nonprintables.
        posix = PurePosixPath(value)
        if (posix.is_absolute() or re.match(r"^[a-zA-Z]:", value)
                or any(segment in ("..", ".", "") for segment in value.split("/"))
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in value)
                or value.startswith("-") or ":" in value):
            raise ImpactInputError("Unsafe path: " + repr(path))
        normalized.append(str(posix))
    return sorted(set(normalized))


def changed_paths_by_git(root: Path, base: str, head: str) -> list[str]:
    if not SHA_RE.fullmatch(base) or not SHA_RE.fullmatch(head):
        raise ImpactInputError("Exact 40-character git revisions required")
    if not (root / ".git").exists():
        raise ImpactInputError("Git metadata unavailable")
    try:
        cmd = subprocess.run(
            ["git", "-C", str(root), "diff", "--no-ext-diff",
             "--name-only", "-z", base, head, "--"],
            capture_output=True, timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ImpactInputError("Local git diff unavailable") from exc
    if cmd.returncode:
        raise ImpactInputError("Cannot verify exact local diff")
    try:
        names = [x.decode("utf-8", errors="strict")
                 for x in cmd.stdout.split(b"\x00") if x]
    except UnicodeDecodeError as exc:
        raise ImpactInputError("Non-UTF8 git paths unsupported") from exc
    return validate_paths(names)


def surface_matches(path: str) -> dict[str, list[str]]:
    tokens = set(TOKENS.findall(path.casefold()))
    matches = {
        kind: sorted(tokens & set(keywords))
        for kind, keywords in SURFACES.items()
        if tokens & set(keywords)
    }
    # The workflow directory is unmistakably CI, independent of filename.
    if path.startswith(".github/workflows/"):
        matches["CI"] = sorted(set(matches.get("CI", [])) | {"workflows"})
    return matches


def plan(paths: list[str], *, repository: str = "UNKNOWN",
         base: str = "UNKNOWN", head: str = "UNKNOWN") -> dict:
    paths = validate_paths(paths)
    if not isinstance(repository, str) or len(repository) > 160:
        raise ImpactInputError("Invalid repository")
    for rev in (base, head):
        if rev != "UNKNOWN" and (not isinstance(rev, str) or not SHA_RE.fullmatch(rev)):
            raise ImpactInputError("Revision must be exact SHA or UNKNOWN")
    mapped: dict[str, list[str]] = {}
    checks: dict[str, set[str]] = {"change-review": set(paths),
                                    "targeted-unit": set(paths)}
    unknown = []
    surfaces: dict[str, set[str]] = {}
    for path in paths:
        evidence = surface_matches(path)
        if not evidence:
            unknown.append(path)
            continue
        mapped[path] = sorted(evidence)
        for surface in evidence:
            surfaces.setdefault(surface, set()).add(path)
            for check in RULE_CHECKS[surface]:
                checks.setdefault(check, set()).add(path)
    # Cross-layer smoke only when distinct source surfaces are present.
    if "UI" in surfaces and ("API" in surfaces or "DB" in surfaces):
        checks["cross-layer"] = surfaces["UI"] | surfaces.get("API", set()) | surfaces.get("DB", set())
    if unknown:
        checks["unmapped-impact"] = set(unknown)
    result = []
    for cid, matching_paths in sorted(checks.items()):
        description, risk = CHECKS[cid]
        result.append({
            "id": cid, "purpose": description, "risk": risk,
            "status": "NOT_RUN",
            "evidence": "PATH_HEURISTIC_ONLY",
            "changed_paths": sorted(matching_paths),
            "test_command": None,
            "execution_receipt": None,
        })
    return {
        "schema_version": 1,
        "classification": "READ_ONLY_TEST_SELECTION",
        "repository": repository, "base_sha": base, "head_sha": head,
        "source_verification": "LOCAL_GIT_DIFF" if base != "UNKNOWN" and head != "UNKNOWN"
                               else "SUPPLIED_PATH_LIST",
        "changed_paths": paths,
        "surfaces": {surface: sorted(items) for surface, items in sorted(surfaces.items())},
        "unmapped_paths": unknown,
        "required_critical_check_ids": sorted(cid for cid in checks if cid in CRITICAL_CHECKS),
        "recommendations": result,
        "gate": "INSUFFICIENT_EVIDENCE",
        "executed_tests": 0,
        "client_effectiveness": "NOT_TESTED",
        "limitations": [
            "Path matches are heuristics: contracts, consumers and test availability not inspected",
            "Recommended checks are NOT_RUN, never PASS; no CI, browser or production evidence",
            "Project policy, actual source diff, change intent and reviewers can require more checks",
            "No writes to target repository, installation, provider calls or paid APIs",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--paths", nargs="+", help="Explicit changed relative file paths")
    group.add_argument("--git-base", help="Exact SHA of baseline revision")
    p.add_argument("--git-head", help="Exact SHA of changed revision, only with --git-base")
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--repository", default="UNKNOWN")
    p.add_argument("--output", type=Path, help="Write a new report file (never overwrite)")
    args = p.parse_args(argv)
    try:
        if bool(args.git_base) != bool(args.git_head):
            raise ImpactInputError("--git-base and --git-head must be supplied together")
        paths = (changed_paths_by_git(args.root.resolve(), args.git_base, args.git_head)
                 if args.git_base else validate_paths(args.paths))
        report = plan(paths, repository=args.repository,
                      base=args.git_base or "UNKNOWN", head=args.git_head or "UNKNOWN")
        payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output is None:
            print(payload, end="")
        else:
            with args.output.open("x", encoding="utf-8") as file:
                file.write(payload)
    except (ImpactInputError, OSError, TypeError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
