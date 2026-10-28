#!/usr/bin/env python3
"""Strict, offline review handoff for a *manually sanitized* Task Observer packet.

This is not an observer, a curator, a GitHub evidence verifier, or an installer.
No network, code execution, inference, or filesystem writes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import date
import re
import sys

MAX_BYTES = 32768
MAX_ITEMS = 20
ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z", re.ASCII)
SOURCE = re.compile(
    r"https://github\.com/[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}/"
    r"(?:issues/[1-9][0-9]*|pull/[1-9][0-9]*|actions/runs/[1-9][0-9]*|commit/[a-f0-9]{40})\Z",
    re.ASCII,
)
CATEGORIES = frozenset({
    "incorrect-routing", "missing-evidence", "redundant-step",
    "regression", "policy-conflict", "documentation-gap",
})
OBS_KEYS = frozenset({"observation_id", "skill_id", "category", "source_url"})


def review_packet(packet: object) -> dict:
    """Validate a limited handoff; never promote claimed evidence to verified."""
    if not isinstance(packet, dict) or set(packet) != {"schema_version", "observations"}:
        raise ValueError("INVALID_SCHEMA")
    if type(packet["schema_version"]) is not int or packet["schema_version"] != 1:
        raise ValueError("INVALID_VERSION")
    raw = packet["observations"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_ITEMS:
        raise ValueError("INVALID_COUNT")
    seen = set()
    rows = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != OBS_KEYS:
            raise ValueError("INVALID_FIELDS")
        if any(not isinstance(item[key], str) for key in OBS_KEYS):
            raise ValueError("INVALID_TYPE")
        oid, skill = item["observation_id"], item["skill_id"]
        if not ID.fullmatch(oid) or not ID.fullmatch(skill):
            raise ValueError("INVALID_IDENTIFIER")
        if oid in seen:
            raise ValueError("DUPLICATE_ID")
        seen.add(oid)
        if item["category"] not in CATEGORIES:
            raise ValueError("INVALID_CATEGORY")
        if not SOURCE.fullmatch(item["source_url"]):
            raise ValueError("INVALID_SOURCE")
        rows.append({
            "observation_id": oid,
            "skill_id": skill,
            "category": item["category"],
            "source_url": item["source_url"],
            "evidence_verified": False,
            "disposition": "MANUAL_REVIEW_REQUIRED",
        })
    return {
        "schema_version": 1,
        "decision": "REVIEW_ONLY",
        "observer_executed": False,
        "curator_executed": False,
        "client_activation_verified": False,
        "items": rows,
    }


# Explicit, public, owner-supplied synthetic evidence only. This optional
# project-scoped preview does NOT read sessions, attest links, learn from the
# user, generate an executable skill, or authorize promotion.
LEARNING_KEYS = frozenset(OBS_KEYS | {"signal", "observed_on"})
PROJECT_RE = re.compile(r"[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}\Z", re.ASCII)
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z", re.ASCII)
SIGNALS = frozenset({"support", "contradict"})
MAX_AGE_DAYS = 730


def _calendar_day(value: str) -> date:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        raise ValueError("INVALID_DATE")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("INVALID_DATE") from exc


def preview_learning(packet: object, *, project_repo: str, as_of: str) -> dict:
    """Review-only, deterministic candidate ranking. Confidence is NOT a probability.

    Input evidence URLs are user claims, never fetched or independently verified.
    No state, files, networks, processes, models, hooks or agents are touched.
    """
    if not isinstance(project_repo, str) or not PROJECT_RE.fullmatch(project_repo):
        raise ValueError("INVALID_PROJECT_SCOPE")
    today = _calendar_day(as_of)
    if not isinstance(packet, dict) or set(packet) != {"schema_version", "observations"}:
        raise ValueError("INVALID_SCHEMA")
    if type(packet["schema_version"]) is not int or packet["schema_version"] != 2:
        raise ValueError("INVALID_VERSION")
    raw = packet["observations"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_ITEMS:
        raise ValueError("INVALID_COUNT")
    groups: dict[tuple[str, str], list[tuple[dict, int]]] = {}
    observed = set()
    for item in raw:
        if not isinstance(item, dict) or set(item) != LEARNING_KEYS:
            raise ValueError("INVALID_FIELDS")
        if any(not isinstance(v, str) for v in item.values()):
            raise ValueError("INVALID_TYPE")
        oid, skill = item["observation_id"], item["skill_id"]
        if not ID.fullmatch(oid) or not ID.fullmatch(skill):
            raise ValueError("INVALID_IDENTIFIER")
        if oid in observed:
            raise ValueError("DUPLICATE_ID")
        observed.add(oid)
        if item["category"] not in CATEGORIES:
            raise ValueError("INVALID_CATEGORY")
        if item["signal"] not in SIGNALS:
            raise ValueError("INVALID_SIGNAL")
        source = item["source_url"]
        if not SOURCE.fullmatch(source):
            raise ValueError("INVALID_SOURCE")
        # One authorized public repository per preview: no ambient project
        # lookup, global fallback or accidental cross-project evidence join.
        segments = source.removeprefix("https://github.com/").split("/")
        if len(segments) < 4 or "/".join(segments[:2]).casefold() != project_repo.casefold():
            raise ValueError("CROSS_PROJECT_SOURCE")
        delta = (today - _calendar_day(item["observed_on"])).days
        if delta < 0 or delta > MAX_AGE_DAYS:
            raise ValueError("STALE_OR_FUTURE_EVIDENCE")
        groups.setdefault((skill, item["category"]), []).append((item, delta))

    candidates = []
    for (skill, category), rows in sorted(groups.items()):
        sources = [r[0]["source_url"] for r in rows]
        if len(sources) != len(set(sources)):
            raise ValueError("DUPLICATE_SOURCE")
        support = [age for item, age in rows if item["signal"] == "support"]
        contra = [age for item, age in rows if item["signal"] == "contradict"]
        # Deliberately transparent, bounded recency heuristic; not validated
        # evidence, an empirical confidence estimate or authority to install.
        def weight(age: int) -> int:
            return 14 if age <= 30 else 10 if age <= 90 else 6 if age <= 180 else 2

        score = max(0, min(90, 30 + sum(weight(a) for a in support)
                            - 18 * len(contra))) if support else 0
        candidates.append({
            "candidate_id": f"{skill}-{category}",
            "project_repo": project_repo.casefold(),
            "skill_id": skill,
            "category": category,
            "support_count": len(support),
            "contradiction_count": len(contra),
            "confidence_hint": score / 100,
            "confidence_semantics": "UNVERIFIED_RECENCY_HEURISTIC_NOT_PROBABILITY",
            "public_evidence_claims": sorted(sources),
            "review_status": "MANUAL_REVIEW_REQUIRED" if len(support) >= 2
                             else "INSUFFICIENT_SUPPORT",
            "evidence_verified": False,
            "owner_approval": "NOT_GRANTED",
            "auto_promoted": False,
        })
    return {
        "schema_version": 2,
        "decision": "REVIEW_ONLY",
        "project_scope": project_repo.casefold(),
        "as_of": today.isoformat(),
        "candidates": candidates,
        "observer_executed": False,
        "model_calls": 0,
        "client_activation_verified": False,
        "skill_files_written": 0,
        "global_scope_enabled": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--learning-preview", action="store_true")
    parser.add_argument("--project-repo")
    parser.add_argument("--as-of")
    args = parser.parse_args(argv)
    try:
        if args.input.is_symlink() or not args.input.is_file():
            raise ValueError("INVALID_FILE")
        with args.input.open("rb") as handle:
            data = handle.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("TOO_LARGE")
        content = json.loads(data.decode("utf-8"))
        if args.learning_preview:
            report = preview_learning(content, project_repo=args.project_repo,
                                      as_of=args.as_of)
        elif args.project_repo is not None or args.as_of is not None:
            raise ValueError("INVALID_MODE")
        else:
            report = review_packet(content)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        # Reject without echoing untrusted data, paths, or raw prompt contents.
        code = str(exc) if isinstance(exc, ValueError) and str(exc) in {
            "INVALID_SCHEMA", "INVALID_VERSION", "INVALID_COUNT", "INVALID_FIELDS",
            "INVALID_TYPE", "INVALID_IDENTIFIER", "DUPLICATE_ID", "INVALID_CATEGORY",
            "INVALID_SOURCE", "INVALID_FILE", "TOO_LARGE",
            "INVALID_PROJECT_SCOPE", "INVALID_DATE", "INVALID_SIGNAL",
            "CROSS_PROJECT_SOURCE", "STALE_OR_FUTURE_EVIDENCE",
            "DUPLICATE_SOURCE", "INVALID_MODE",
        } else "INVALID_INPUT"
        print(json.dumps({"decision": "REJECT", "reason": code}, sort_keys=True))
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
