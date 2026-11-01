#!/usr/bin/env python3
"""Opt-in public GitHub fact checks and review proposals for native learning #436.

Only typed, bounded facts are verified. The significance of a fact for improving
a skill is NEVER attested automatically. No session data, models, writes,
approval creation, or skill installation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib import error, request

from skill_observation_review import (
    ID, MAX_BYTES, MAX_ITEMS, SOURCE, preview_learning,
)

SHA40 = re.compile(r"[a-f0-9]{40}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
MAX_RESPONSE_BYTES = 131072
MAX_SKILL_BYTES = 262144
PREDICATES = {
    "issue_exists": "issues",
    "pr_head_at_sha": "pull",
    "pr_merged_at_sha": "pull",
    "run_success_at_sha": "actions/runs",
    "commit_exists_at_sha": "commit",
}
# Fixed categories: no text from observations or GitHub becomes an instruction.
PROPOSALS = {
    "incorrect-routing": ("REVIEW_ROUTING_CONDITION", "Add positive and negative routing tests"),
    "missing-evidence": ("ADD_EVIDENCE_GATE", "Test matching and mismatched SHA and CI outcomes"),
    "redundant-step": ("REVIEW_WORKFLOW_STEP", "Test that required approvals and checks remain"),
    "regression": ("ADD_REGRESSION_CHECK", "Reproduce failure and verify old behavior"),
    "policy-conflict": ("REVIEW_POLICY_CONFLICT", "Test authorization and fail-closed boundaries"),
    "documentation-gap": ("CLARIFY_SKILL_DOCUMENTATION", "Test documented examples and compatibility"),
}


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def public_github_get(path: str) -> dict:
    """GET one predetermined public GitHub API path, never arbitrary evidence URLs."""
    if not re.fullmatch(
        r"/repos/[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}/"
        r"(?:issues/[1-9][0-9]*|pulls/[1-9][0-9]*|actions/runs/[1-9][0-9]*|"
        r"git/commits/[a-f0-9]{40})"
        r"|/repos/[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}",
        path, flags=re.ASCII,
    ):
        raise ValueError("INVALID_GITHUB_PATH")
    url = "https://api.github.com" + path
    opener = request.build_opener(request.ProxyHandler({}), _NoRedirect)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ADT-Native-Learning-ReadOnly",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    with opener.open(request.Request(url, headers=headers, method="GET"), timeout=6) as response:
        if response.geturl() != url or response.status != 200:
            raise ValueError("UNEXPECTED_RESPONSE")
        if "json" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("NON_JSON_RESPONSE")
        data = response.read(MAX_RESPONSE_BYTES + 1)
    if len(data) > MAX_RESPONSE_BYTES:
        raise ValueError("RESPONSE_TOO_LARGE")
    parsed = json.loads(data.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("INVALID_GITHUB_RESPONSE")
    return parsed


def read_bounded_json(path: Path) -> object:
    """Read a small, explicit regular file without following symlinks or junctions."""
    if any(part.is_symlink() or getattr(part, "is_junction", lambda: False)()
           for part in (path, *path.parents)) or not path.is_file():
        raise ValueError("INVALID_FILE")
    with path.open("rb") as source:
        data = source.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("TOO_LARGE")
    return json.loads(data.decode("utf-8"))


def validate_claims(payload: object, packet: dict) -> dict[str, dict]:
    """Every sanitized observation has one exact, typed and non-executable claim."""
    if (not isinstance(payload, dict) or set(payload) != {"schema_version", "claims"}
            or type(payload["schema_version"]) is not int
            or payload["schema_version"] != 1):
        raise ValueError("INVALID_CLAIMS_SCHEMA")
    claims = payload["claims"]
    if not isinstance(claims, list) or len(claims) != len(packet["observations"]):
        raise ValueError("INVALID_CLAIMS_COUNT")
    by_url: dict[str, dict] = {}
    for item in claims:
        if not isinstance(item, dict) or set(item) != {
            "source_url", "predicate", "expected_sha",
        }:
            raise ValueError("INVALID_CLAIM_FIELDS")
        source, predicate, sha = (item[key] for key in (
            "source_url", "predicate", "expected_sha",
        ))
        if (not isinstance(source, str) or not SOURCE.fullmatch(source)
                or not isinstance(predicate, str) or predicate not in PREDICATES):
            raise ValueError("INVALID_CLAIM")
        if (predicate == "issue_exists" and sha is not None) or (
            predicate != "issue_exists" and
            (not isinstance(sha, str) or not SHA40.fullmatch(sha))
        ):
            raise ValueError("INVALID_CLAIM_SHA")
        if source in by_url:
            raise ValueError("DUPLICATE_CLAIM")
        kind, _ = _resource(source)
        if kind != PREDICATES[predicate]:
            raise ValueError("CLAIM_RESOURCE_MISMATCH")
        if kind == "commit" and source.rsplit("/", 1)[-1] != sha:
            raise ValueError("CLAIM_SHA_MISMATCH")
        by_url[source] = item
    if set(by_url) != {row["source_url"] for row in packet["observations"]}:
        raise ValueError("CLAIM_SOURCE_MISMATCH")
    return by_url


def _resource(source: str) -> tuple[str, str]:
    # URL syntax is validated by preview_learning and validate_claims.
    parts = source.removeprefix("https://github.com/").split("/")
    kind = "/".join(parts[2:-1])
    return kind, parts[-1]


def _object_path(repo: str, source: str) -> str:
    kind, number = _resource(source)
    api_kind = {
        "issues": "issues", "pull": "pulls",
        "actions/runs": "actions/runs", "commit": "git/commits",
    }[kind]
    return "/repos/" + repo + "/" + api_kind + "/" + number


def _same_repo(actual: object, expected: str) -> bool:
    return isinstance(actual, str) and actual.casefold() == expected.casefold()


def _fact_verdict(claim: dict, obj: dict, repo: str) -> tuple[str, str | None]:
    """Return verified typed fact only; never infer that a practice is correct."""
    if not isinstance(obj, dict):
        return "NOT_VERIFIED", None
    kind, ident = _resource(claim["source_url"])
    predicate, expected = claim["predicate"], claim["expected_sha"]
    if kind == "issues":
        if (obj.get("number") == int(ident) and "pull_request" not in obj
                and obj.get("state") in {"open", "closed"}):
            return "EXISTS_ONLY", "issue:" + ident
    elif kind == "pull":
        head = obj.get("head") or {}
        base = obj.get("base") or {}
        if (obj.get("number") != int(ident) or not isinstance(head, dict)
                or not isinstance(base, dict)
                or not _same_repo((base.get("repo") or {}).get("full_name"), repo)
                or not isinstance(head.get("sha"), str)
                or not SHA40.fullmatch(head["sha"])):
            return "NOT_VERIFIED", None
        if predicate == "pr_head_at_sha" and head["sha"] == expected:
            return "VERIFIED_FACT", "sha:" + head["sha"]
        if (predicate == "pr_merged_at_sha" and obj.get("merged") is True
                and isinstance(obj.get("merged_at"), str) and obj["merged_at"]
                and obj.get("merge_commit_sha") == expected):
            return "VERIFIED_FACT", "sha:" + head["sha"]
    elif kind == "actions/runs":
        if (obj.get("id") == int(ident)
                and _same_repo((obj.get("repository") or {}).get("full_name"), repo)
                and obj.get("head_sha") == expected
                and obj.get("status") == "completed"
                and obj.get("conclusion") == "success"):
            return "VERIFIED_FACT", "sha:" + expected
    elif kind == "commit":
        if obj.get("sha") == ident == expected:
            return "EXISTS_ONLY", "sha:" + expected
    return "NOT_VERIFIED", None


def check_skill_lock(root: Path, skill_id: str, path: str, expected: str) -> dict:
    """Check one explicitly selected local skill version, without any mutation."""
    if not ID.fullmatch(skill_id) or not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise ValueError("INVALID_SKILL_LOCK")
    if not isinstance(path, str) or "\\" in path:
        raise ValueError("INVALID_SKILL_PATH")
    pure = PurePosixPath(path)
    parts = pure.parts
    if (pure.is_absolute() or ".." in parts or "." in parts
            or not ((len(parts) == 4 and parts[:2] == (".agents", "skills")
                     and parts[2] == skill_id and parts[-1] == "SKILL.md")
                    or (len(parts) == 5 and parts[0] == "extensions"
                        and parts[2] == "skills" and parts[3] == skill_id
                        and parts[-1] == "SKILL.md"))):
        raise ValueError("INVALID_SKILL_PATH")
    if root.is_symlink() or getattr(root, "is_junction", lambda: False)() or not root.is_dir():
        raise ValueError("INVALID_SKILL_ROOT")
    target = root.joinpath(*parts)
    if (not target.resolve().is_relative_to(root.resolve())
            or any(node.is_symlink() or getattr(node, "is_junction", lambda: False)()
                   for node in (target, *target.parents) if node != root.parent)
            or not target.is_file()):
        raise ValueError("INVALID_SKILL_FILE")
    with target.open("rb") as handle:
        raw = handle.read(MAX_SKILL_BYTES + 1)
    if len(raw) > MAX_SKILL_BYTES:
        raise ValueError("SKILL_TOO_LARGE")
    actual = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    return {
        "skill_id": skill_id,
        "path": path,
        "expected_sha256": expected,
        "actual_sha256": actual,
        "status": "LOCAL_SHA_MATCH" if expected == actual else "STALE_SKILL_SOURCE",
    }


def verify_learning(packet: object, claims: object, *, project_repo: str,
                    as_of: str, fetch=public_github_get, skill_lock: dict | None = None) -> dict:
    """Prepare fact receipts and deterministic proposals; never approve or apply."""
    preview = preview_learning(packet, project_repo=project_repo, as_of=as_of)
    expected = validate_claims(claims, packet)
    repo = preview["project_scope"]
    try:
        metadata = fetch("/repos/" + repo)
        accessible = (isinstance(metadata, dict) and metadata.get("private") is False
                      and _same_repo(metadata.get("full_name"), repo))
    except (OSError, ValueError, TypeError, KeyError, error.URLError):
        accessible = False
    cache: dict[str, tuple[str, str | None]] = {}
    receipts = []
    for obs in packet["observations"]:
        source = obs["source_url"]
        if source not in cache:
            verdict = ("NOT_VERIFIED", None)
            if accessible:
                try:
                    obj = fetch(_object_path(repo, source))
                    verdict = _fact_verdict(expected[source], obj, repo)
                except (OSError, ValueError, TypeError, KeyError, error.URLError):
                    pass
            cache[source] = verdict
        status, group = cache[source]
        receipts.append({
            "observation_id": obs["observation_id"],
            "source_url": source,
            "predicate": expected[source]["predicate"],
            "signal": obs["signal"],
            "fact_status": status,
            "fact_group": group,
            "practice_correctness_verified": False,
        })
    receipt_by_id = {r["observation_id"]: r for r in receipts}
    for candidate in preview["candidates"]:
        matched = [
            receipt_by_id[row["observation_id"]]
            for row in packet["observations"]
            if (row["skill_id"] == candidate["skill_id"]
                and row["category"] == candidate["category"])
        ]
        supports = {r["fact_group"] for r in matched
                    if r["signal"] == "support" and r["fact_status"] == "VERIFIED_FACT"}
        contradictions = {r["fact_group"] for r in matched
                          if r["signal"] == "contradict" and r["fact_status"] == "VERIFIED_FACT"}
        unknown = sum(r["fact_status"] != "VERIFIED_FACT" for r in matched)
        conflicted = bool(supports & contradictions or contradictions)
        ready = len(supports) >= 2 and not conflicted and unknown == 0
        lock = (skill_lock if skill_lock and
                skill_lock["skill_id"] == candidate["skill_id"] else None)
        source_status = lock["status"] if lock else "SOURCE_PIN_REQUIRED"
        proposal_kind, test_plan = PROPOSALS[candidate["category"]]
        fingerprint = hashlib.sha256(json.dumps({
            "repo": repo, "skill_id": candidate["skill_id"],
            "category": candidate["category"],
            "source_sha256": lock["expected_sha256"] if lock else None,
            "facts": sorted((r["source_url"], r["predicate"], r["fact_status"],
                             r["signal"]) for r in matched),
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        candidate.update({
            "verified_independent_support_facts": len(supports),
            "verified_independent_contradiction_facts": len(contradictions),
            "unverified_or_existence_only_claims": unknown,
            "content_relevance_verified": False,
            "source_revision_gate": source_status,
            "review_gate": ("OWNER_REVIEW_REQUIRED" if ready and
                            source_status == "LOCAL_SHA_MATCH" else "NOT_READY"),
            "proposal": {
                "proposal_id": fingerprint,
                "kind": proposal_kind,
                "skill_id": candidate["skill_id"],
                "project_repo": repo,
                "source_lock": lock,
                "change": "STRUCTURED_PROPOSAL_ONLY_NO_DIFF_NO_EXECUTION",
                "tests_required": [test_plan, "Confirm no regression across project scope"],
                "risks": ["Unverified behavior benefit", "Potential stale skill or CI evidence"],
                "rollback": "Revert a separately owner-approved GitHub PR",
                "approval": "NOT_GRANTED",
                "applied": False,
                "approval_route": "EXPLICIT_OWNER_DECISION_THEN_NORMAL_PR_CI_MERGE",
            },
        })
    return {
        **preview,
        "fact_checks": receipts,
        "repo_access_verified": accessible,
        "network_mode": "EXPLICIT_PUBLIC_GITHUB_GET_ONLY",
        "human_practice_approval": "NOT_GRANTED",
        "practice_auto_promotion": False,
        "approved_practices_written": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--claims", type=Path, required=True)
    parser.add_argument("--project-repo", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--skill-root", type=Path)
    parser.add_argument("--skill-id")
    parser.add_argument("--skill-file")
    parser.add_argument("--skill-expected-sha256")
    args = parser.parse_args(argv)
    try:
        locks = (args.skill_root, args.skill_id, args.skill_file,
                 args.skill_expected_sha256)
        if any(value is not None for value in locks) and any(
                value is None for value in locks):
            raise ValueError("INCOMPLETE_SKILL_LOCK")
        lock = (check_skill_lock(*locks) if all(v is not None for v in locks)
                else None)
        packet = read_bounded_json(args.input)
        claims = read_bounded_json(args.claims)
        result = verify_learning(
            packet, claims, project_repo=args.project_repo,
            as_of=args.as_of, skill_lock=lock,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        print(json.dumps({"decision": "REJECT", "reason": "INVALID_OR_UNSAFE_INPUT"}))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
