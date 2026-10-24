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
            "contract", "schema", "serializer", "dto", "server", "http",
            "routes"),
    "DB": ("database", "migrations", "migration", "models", "sql", "alembic",
           "prisma", "db", "persistence", "repository"),
    "UI": ("frontend", "components", "views", "screens", "react", "ui",
           "widget", "forms", "pages", "web"),
    "ASYNC": ("worker", "queue", "tasks", "jobs", "events", "consumer",
              "producer", "scheduler", "broker"),
    "PRIVACY": ("security", "secret", "secrets", "pii", "vault", "personal", "gdpr"),
    "CI": ("workflows", "docker", "compose", "deploy", "helm", "kubernetes",
           "ci", "infra", "terraform", "pipeline"),
}
# Each rule is explicit and grounded in a changed path, NOT a claim that an
# API schema or a callsite was actually inspected.
CHECKS = {
    "change-review": ("Source-focused review of changed behavior and callers", "LOW"),
    "targeted-unit": ("Targeted unit and relevant negative regressions", "LOW"),
    "documentation-review": ("Documentation, links, instructions and policy consistency", "LOW"),
    "test-review": ("Review test oracles, fixtures and regressions introduced by changed tests", "LOW"),
    "api-contract": ("Producer/consumer API and schema backward compatibility", "HIGH"),
    "api-negative": ("Invalid request, authorization and response error handling", "HIGH"),
    "db-migration": ("Migration forward/backward, schema and integrity assertions", "CRITICAL"),
    "db-rollback": ("Recovery, backup/rollback rehearsal or explicit blocker", "CRITICAL"),
    "auth-boundary": ("Deny-by-default auth, cross-tenant and session regressions", "CRITICAL"),
    "privacy-boundary": ("Unauthorized PII exposure and secrets-handling checks", "CRITICAL"),
    "ui-state": ("UI state, keyboard navigation, restoration and focus tests", "HIGH"),
    "browser-flow": ("Critical user journey and accessibility smoke checks", "HIGH"),
    "async-replay": ("Replay, concurrency, idempotency, retries and ordering", "HIGH"),
    "state-integrity": ("Version/persistence invariants, no-op writes and transitions", "HIGH"),
    "consumer-review": ("Manually trace direct API/service/client consumers beyond the changed diff", "HIGH"),
    "deployment-safety": ("CI safeguards, deploy policy and rollback dry-run", "CRITICAL"),
    "cross-layer": ("End-to-end check across changed frontend/API/DB boundaries", "HIGH"),
    "unmapped-impact": ("Inspect unknown paths and choose concrete risk tests", "UNKNOWN"),
}
# Catalog-backed skills only; recommendations never prove client activation.
CHECK_GUIDANCE = {
    "change-review": ("qa-core", "change-impact-analysis", "Review changed lines and direct callers; flag missing context."),
    "targeted-unit": ("qa-core", "test-analysis-design", "Exercise changed behavior and a rejected/invalid-input case."),
    "documentation-review": ("docs-technical", "documentation-maintenance", "Check local links, procedures and corresponding translations."),
    "test-review": ("qa-core", "test-review", "Ensure the edited test fails against a known-bad mutation."),
    "api-contract": ("qa-contract", "contract-testing", "Compare request/response fields across the change."),
    "api-negative": ("qa-contract", "api-testing", "Reject invalid or unauthorized requests without side effects."),
    "db-migration": ("data-engineering", "database-validation", "Verify data preservation and schema invariants."),
    "db-rollback": ("data-engineering", "database-validation", "Rehearse rollback or report the unsupported recovery case."),
    "auth-boundary": ("qa-security", "security-testing", "Deny cross-tenant and unauthorized access without leaking records."),
    "privacy-boundary": ("qa-security", "security-testing", "Ensure restricted fields and secrets stay out of responses."),
    "ui-state": ("qa-ui", "playwright-testing", "Verify focus, field state, scroll and restoration."),
    "browser-flow": ("qa-ui", "e2e-testing", "Exercise a critical journey including one negative case."),
    "async-replay": ("reliability-testing", "background-processing", "Repeat an event and check idempotency and ordering."),
    "state-integrity": ("data-engineering", "database-validation", "Verify no-op writes preserve state and versions."),
    "consumer-review": ("qa-contract", "contract-testing", "Inspect direct consumers and their version/error expectations."),
    "deployment-safety": ("devops-infrastructure", "release-safety", "Check release safeguards and documented rollback."),
    "cross-layer": ("qa-fullstack", "integration-testing", "Verify UI to API to stored-state behavior."),
    "unmapped-impact": ("qa-core", "change-impact-analysis", "Identify the subsystem and owners before specifying tests."),
}


def guidance_for_check(check_id: str) -> dict:
    """Deterministic source guidance, not an executable test or activation."""
    profile, skill, scenario = CHECK_GUIDANCE[check_id]
    return {
        "profile_hint": profile, "skill_hint": skill,
        "candidate_test_scenario": scenario,
        "source": "STATIC_MANIFEST_CATALOG_HINT",
        "client_skill_activation": "NOT_VERIFIED",
        "test_execution": "NOT_RUN",
    }


RISK_ORDER = {"LOW": 0, "HIGH": 1, "CRITICAL": 2, "UNKNOWN": 3}
RULE_CHECKS = {
    "AUTH": ("auth-boundary", "privacy-boundary", "api-negative"),
    "PRIVACY": ("privacy-boundary", "auth-boundary"),
    "API": ("api-contract", "api-negative", "consumer-review"),
    "DB": ("db-migration", "db-rollback"),
    "UI": ("ui-state", "browser-flow"),
    "ASYNC": ("async-replay",),
    "PERSISTED_STATE": ("state-integrity", "async-replay", "consumer-review"),
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


def is_documentation_path(path: str) -> bool:
    """Documentation is a separate review surface, not evidence of executable code."""
    return PurePosixPath(path).suffix.lower() in {".md", ".mdx", ".rst", ".adoc"}


def is_test_path(path: str) -> bool:
    """Narrow test naming conventions; names alone never assert execution."""
    parts = path.casefold().split("/")
    name = parts[-1]
    return (any(part in {"test", "tests", "__tests__", "spec", "specs", "qa"}
                for part in parts[:-1])
            or name.startswith(("test_", "spec_"))
            or any(part in name for part in (".test.", ".spec.", "_test.", "_spec.")))


MAPPING_MAX_BYTES = 131072
ID_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9_.-]{0,79}\Z")
TEST_REF_PATTERN = re.compile(r"[a-zA-Z0-9_./:-]{1,160}\Z")


def load_test_map(path: Path) -> dict:
    """Load bounded JSON; neither infer nor execute any test command."""
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAPPING_MAX_BYTES + 1)
        if len(raw) > MAPPING_MAX_BYTES:
            raise ImpactInputError("Test map too large")
        data = json.loads(raw.decode("utf-8"))
    except ImpactInputError:
        raise
    except (OSError, UnicodeError, ValueError) as exc:
        raise ImpactInputError("Test map is unreadable or invalid JSON") from exc
    return validate_test_map(data)


def validate_test_map(data: dict) -> dict:
    """Fail closed for optional project-owned mapping, including direct callers."""
    if not isinstance(data, dict) or set(data) != {"schema_version", "entries"}:
        raise ImpactInputError("Invalid test map schema")
    entries = data["entries"]
    if type(data["schema_version"]) is not int or data["schema_version"] != 1 or not isinstance(entries, list) or len(entries) > 100:
        raise ImpactInputError("Invalid test map version or count")
    seen = set()
    for item in entries:
        if not isinstance(item, dict) or set(item) != {
            "id", "prefix", "check_ids", "test_ids", "requirement_ids"
        }:
            raise ImpactInputError("Invalid test mapping entry")
        name, prefix = item["id"], item["prefix"]
        if not isinstance(name, str) or not ID_PATTERN.fullmatch(name) or name in seen:
            raise ImpactInputError("Invalid or duplicate mapping id")
        seen.add(name)
        if not isinstance(prefix, str) or not prefix.endswith("/"):
            raise ImpactInputError("Mapping prefix must be a directory")
        validate_paths([prefix[:-1]])
        for key, allowed, max_count in (
            ("check_ids", set(CHECKS), 12),
            ("test_ids", None, 12),
            ("requirement_ids", None, 12),
        ):
            vals = item[key]
            if not isinstance(vals, list) or not vals or len(vals) > max_count:
                raise ImpactInputError("Invalid or empty " + key)
            if any(not isinstance(v, str) for v in vals) or len(set(vals)) != len(vals):
                raise ImpactInputError("Invalid or duplicate " + key)
            if allowed is not None and any(v not in allowed for v in vals):
                raise ImpactInputError("Unknown QA check id")
            if allowed is None and any(not TEST_REF_PATTERN.fullmatch(v)
                                       or ".." in v or v.startswith("/") for v in vals):
                raise ImpactInputError("Unsafe or invalid test/requirement reference")
    return data


def select_declared_tests(changed_paths: list[str], check_ids: set[str],
                          declared: dict) -> list[dict]:
    """Use exact path-prefix matches; do not assert that tests exist or run."""
    selected = []
    for item in declared["entries"]:
        paths = sorted(p for p in changed_paths if p.startswith(item["prefix"]))
        if not paths:
            continue
        for check_id in item["check_ids"]:
            if check_id not in check_ids:
                continue
            for test_id in item["test_ids"]:
                selected.append({
                    "mapping_id": item["id"], "check_id": check_id,
                    "test_id": test_id, "requirement_ids": item["requirement_ids"],
                    "matched_paths": paths, "status": "NOT_RUN",
                    "source": "OWNER_DECLARED_NOT_VERIFIED",
                    "execution_receipt": None,
                })
    return sorted(selected, key=lambda x: (
        x["check_id"], x["test_id"], x["mapping_id"]))


def plan(paths: list[str], *, repository: str = "UNKNOWN",
         base: str = "UNKNOWN", head: str = "UNKNOWN",
         source: str = "SUPPLIED_PATH_LIST", test_map: dict | None = None) -> dict:
    paths = validate_paths(paths)
    if source not in ("SUPPLIED_PATH_LIST", "LOCAL_GIT_DIFF"):
        raise ImpactInputError("Unknown change source")
    if source == "LOCAL_GIT_DIFF" and (base == "UNKNOWN" or head == "UNKNOWN"):
        raise ImpactInputError("Git evidence requires exact SHA pair")
    if not isinstance(repository, str) or len(repository) > 160:
        raise ImpactInputError("Invalid repository")
    for rev in (base, head):
        if rev != "UNKNOWN" and (not isinstance(rev, str) or not SHA_RE.fullmatch(rev)):
            raise ImpactInputError("Revision must be exact SHA or UNKNOWN")
    mapped: dict[str, list[str]] = {}
    checks: dict[str, set[str]] = {"change-review": set(paths)}
    executable = {path for path in paths if not is_documentation_path(path)}
    if executable:
        checks["targeted-unit"] = executable
    unknown = []
    surfaces: dict[str, set[str]] = {}
    for path in paths:
        if is_documentation_path(path):
            checks.setdefault("documentation-review", set()).add(path)
            continue
        test_path = is_test_path(path)
        if test_path:
            checks.setdefault("test-review", set()).add(path)
        evidence = surface_matches(path)
        if not evidence:
            if not test_path:
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
            "guidance": guidance_for_check(cid),
        })
    declared_tests = (select_declared_tests(paths, set(checks), validate_test_map(test_map))
                      if test_map is not None else [])
    mapped_checks = {x["check_id"] for x in declared_tests}
    return {
        "schema_version": 1,
        "classification": "READ_ONLY_TEST_SELECTION",
        "repository": repository, "base_sha": base, "head_sha": head,
        "source_verification": source,
        "changed_paths": paths,
        "surfaces": {surface: sorted(items) for surface, items in sorted(surfaces.items())},
        "unmapped_paths": unknown,
        "required_critical_check_ids": sorted(cid for cid in checks if cid in CRITICAL_CHECKS),
        "recommendations": result,
        "declared_test_candidates": declared_tests,
        "unmapped_check_ids": sorted(set(checks) - mapped_checks),
        "test_mapping_source": "OWNER_DECLARED_NOT_VERIFIED" if test_map is not None else "NONE",
        "gate": "INSUFFICIENT_EVIDENCE",
        "executed_tests": 0,
        "client_effectiveness": "NOT_TESTED",
        "limitations": [
            "Path matches are heuristics: contracts, consumers and test availability not inspected",
            "Recommended checks are NOT_RUN, never PASS; no CI, browser or production evidence",
            "Project policy, actual source diff, change intent and reviewers can require more checks",
            "No writes to target repository, installation, provider calls or paid APIs",
            "Test references are declared by owner: existence, applicability and execution NOT_VERIFIED",
        ],
    }


def add_content_evidence(report: dict, inspection: dict,
                         test_map: dict | None = None) -> dict:
    """Enrich, never remove, test checks using source-line token hints only."""
    enriched = dict(report)
    enriched["diff_content"] = inspection
    by_id = {item["id"]: dict(item) for item in report["recommendations"]}
    for path, data in inspection["files"].items():
        if is_documentation_path(path):
            # Documentation prose may mention auth/API tokens without modifying runtime.
            continue
        if data["binary_or_unparsed"]:
            cid = "unmapped-impact"
            if cid not in by_id:
                purpose, risk = CHECKS[cid]
                by_id[cid] = {
                    "id": cid, "purpose": purpose, "risk": risk,
                    "status": "NOT_RUN", "evidence": "CONTENT_UNINSPECTED",
                    "changed_paths": [], "test_command": None,
                    "execution_receipt": None,
                    "guidance": guidance_for_check(cid),
                }
            by_id[cid]["changed_paths"] = sorted(set(by_id[cid]["changed_paths"]) | {path})
        for surface in data["signals"]:
            if surface not in RULE_CHECKS:
                raise ImpactInputError("Unsupported patch signal class")
            for cid in RULE_CHECKS[surface]:
                if cid not in by_id:
                    purpose, risk = CHECKS[cid]
                    by_id[cid] = {
                        "id": cid, "purpose": purpose, "risk": risk,
                        "status": "NOT_RUN", "evidence": "CONTENT_TOKEN_HINT_ONLY",
                        "changed_paths": [], "test_command": None,
                        "execution_receipt": None,
                    "guidance": guidance_for_check(cid),
                    }
                by_id[cid]["changed_paths"] = sorted(set(by_id[cid]["changed_paths"]) | {path})
    enriched["recommendations"] = [by_id[cid] for cid in sorted(by_id)]
    active_checks = set(by_id)
    enriched["required_critical_check_ids"] = sorted(active_checks & CRITICAL_CHECKS)
    if test_map is not None:
        tests = select_declared_tests(enriched["changed_paths"], active_checks,
                                      validate_test_map(test_map))
        enriched["declared_test_candidates"] = tests
        enriched["unmapped_check_ids"] = sorted(
            active_checks - {item["check_id"] for item in tests}
        )
    else:
        enriched["unmapped_check_ids"] = sorted(active_checks)
    enriched["content_evidence_status"] = "TOKEN_HINTS_WITH_GAPS" if (
        inspection["requires_manual_review"]) else "TOKEN_HINTS_ONLY"
    enriched["gate"] = "INSUFFICIENT_EVIDENCE"
    enriched["executed_tests"] = 0
    return enriched


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--paths", nargs="+", help="Explicit changed relative file paths")
    group.add_argument("--git-base", help="Exact SHA of baseline revision")
    p.add_argument("--git-head", help="Exact SHA of changed revision, only with --git-base")
    p.add_argument("--inspect-diff", action="store_true", help="Bounded local content-token hints (git SHA pair only)")
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--repository", default="UNKNOWN")
    p.add_argument("--test-map", type=Path, help="Optional owner-supplied, read-only test ID mapping JSON")
    p.add_argument("--output", type=Path, help="Write a new report file (never overwrite)")
    args = p.parse_args(argv)
    try:
        if bool(args.git_base) != bool(args.git_head):
            raise ImpactInputError("--git-base and --git-head must be supplied together")
        if args.inspect_diff and not args.git_base:
            raise ImpactInputError("--inspect-diff requires an exact local Git SHA pair")
        paths = (changed_paths_by_git(args.root.resolve(), args.git_base, args.git_head)
                 if args.git_base else validate_paths(args.paths))
        declared = load_test_map(args.test_map) if args.test_map is not None else None
        report = plan(paths, repository=args.repository,
                      base=args.git_base or "UNKNOWN", head=args.git_head or "UNKNOWN",
                      source="LOCAL_GIT_DIFF" if args.git_base else "SUPPLIED_PATH_LIST",
                      test_map=declared)
        if args.inspect_diff:
            import qa_diff_signals
            inspection = qa_diff_signals.inspect_git(
                args.root.resolve(), args.git_base, args.git_head, paths
            )
            report = add_content_evidence(report, inspection, declared)
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
