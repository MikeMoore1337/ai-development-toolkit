#!/usr/bin/env python3
"""Opt-in, offline external Skill candidate review for Toolkit #199/#200.

This command combines the existing LOCAL lexical coverage diagnostic with the
existing file/manifest Security Gate. It NEVER searches external sites, installs
skills, fetches remote content, executes code or grants runtime permissions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from external_skill_gate import _manifest, review
from toolkit_mcp import _assess_skill_coverage

MAX_ALLOWED_SOURCES = 12

BASE = {
    "schema_version": 1,
    "external_search": "NOT_RUN",
    "remote_provenance_attested": False,
    "license_independently_verified": False,
    "installation": "NOT_AUTHORIZED",
    "execution": "NOT_RUN",
    "client_activation": "NOT_OBSERVED",
    "requires_manual_approval": True,
}


def _source(url: object) -> str | None:
    """Canonical HTTPS GitHub repo URL only (no credentials, query or fragments)."""
    if not isinstance(url, str) or len(url) > 240:
        return None
    try:
        parts = urlsplit(url)
        if (parts.scheme != "https" or parts.netloc != "github.com"
                or parts.query or parts.fragment):
            return None
        path = parts.path.rstrip("/")
        items = path.split("/")
        if (len(items) != 3 or items[0] != ""
                or not all(v and v.replace("-", "").replace("_", "").replace(".", "").isalnum()
                           for v in items[1:])):
            return None
        return "https://github.com/" + items[1] + "/" + items[2]
    except ValueError:
        return None


def evaluate(
    query: str,
    *,
    opt_in: bool = False,
    candidate_dir: Path | None = None,
    manifest: Path | None = None,
    allow_sources: tuple[str, ...] = (),
) -> dict:
    """Never mutate files and never treat a reviewed package as safe-to-install."""
    local = _assess_skill_coverage(query)
    result = {**BASE, "local_skill_coverage": local}
    has_candidate = candidate_dir is not None or manifest is not None
    if not has_candidate and not opt_in and not allow_sources:
        return {**result, "decision": "LOCAL_ONLY", "reason": "NO_EXTERNAL_CANDIDATE"}
    if (not opt_in or candidate_dir is None or manifest is None
            or not allow_sources or len(allow_sources) > MAX_ALLOWED_SOURCES):
        return {**result, "decision": "REJECT", "reason": "EXPLICIT_OPT_IN_AND_SOURCE_REQUIRED"}

    # Operator-supplied allowlist is a request boundary, NOT proof of upstream trust.
    canonical = tuple(_source(src) for src in allow_sources)
    if None in canonical or len(set(canonical)) != len(canonical):
        return {**result, "decision": "REJECT", "reason": "INVALID_ALLOWED_SOURCE"}
    if not isinstance(candidate_dir, Path) or not isinstance(manifest, Path):
        return {**result, "decision": "REJECT", "reason": "INVALID_LOCAL_PATH"}
    if candidate_dir.resolve() == manifest.resolve() or manifest.resolve().is_relative_to(candidate_dir.resolve()):
        return {**result, "decision": "REJECT", "reason": "MANIFEST_MUST_BE_OUTSIDE_CANDIDATE"}

    manifest_errors: list[dict] = []
    meta = _manifest(manifest, manifest_errors)
    if meta is None:
        return {**result, "decision": "REJECT", "reason": "INVALID_CANDIDATE_MANIFEST",
                "security_findings": manifest_errors}
    declared = _source(meta["source_url"])
    if declared is None or declared not in canonical:
        return {**result, "decision": "REJECT", "reason": "SOURCE_NOT_ALLOWLISTED"}
    verdict = review(candidate_dir, manifest)
    return {
        **result,
        "decision": "REJECT" if verdict["decision"] == "REJECT" else "MANUAL_REVIEW_REQUIRED",
        "reason": "STATIC_SECURITY_GATE",
        "candidate": {
            "id": meta["candidate_id"],
            "source_url": declared,
            "revision_claim": meta["source_revision"],
            "license_claim": meta["license"],
            "evidence": "OPERATOR_PROVIDED_UNVERIFIED_METADATA",
        },
        "security_gate_verdict": verdict["decision"],
        "security_findings": verdict["issues"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Local task or exact skill slug (1..500 chars)")
    parser.add_argument("--review-external", action="store_true",
                        help="Explicit consent to review one already-local external candidate")
    parser.add_argument("--candidate-dir", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--allow-source", action="append", default=[],
                        help="Exact allowed HTTPS GitHub repo URL; repeat only for approved sources")
    args = parser.parse_args(argv)
    try:
        outcome = evaluate(args.query, opt_in=args.review_external,
                           candidate_dir=args.candidate_dir, manifest=args.manifest,
                           allow_sources=tuple(args.allow_source))
    except (ValueError, TypeError):
        outcome = {**BASE, "decision": "REJECT", "reason": "INVALID_TASK"}
    print(json.dumps(outcome, ensure_ascii=False, indent=2, sort_keys=True))
    return {"LOCAL_ONLY": 0, "MANUAL_REVIEW_REQUIRED": 1, "REJECT": 2}[outcome["decision"]]


if __name__ == "__main__":
    raise SystemExit(main())
