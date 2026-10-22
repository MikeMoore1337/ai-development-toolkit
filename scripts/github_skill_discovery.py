#!/usr/bin/env python3
"""Explicit opt-in discovery of SKILL.md paths in PINNED public GitHub repositories.

Only GitHub's public REST metadata is read. No code/content download, execution,
installation, tokens, credential lookup, or implicit network access.
"""
from __future__ import annotations

import argparse
import http.client
import json
import re
import ssl
from urllib.parse import urlsplit

from skill_candidate_review import _source
from toolkit_mcp import _assess_skill_coverage

MAX_REPOS = 3
MAX_BYTES = 256 * 1024
MAX_TREE_ENTRIES = 5000
MAX_MATCHES = 20
HEX = re.compile(r"[0-9a-f]{40}\Z")
SAFE_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z")


class DiscoveryError(ValueError):
    """Denial reason is a fixed non-secret code."""


def _pin(raw: object) -> tuple[str, str, str, str]:
    if not isinstance(raw, str) or len(raw) > 250 or raw.count("@") != 1:
        raise DiscoveryError("INVALID_PINNED_SOURCE")
    source, revision = raw.rsplit("@", 1)
    canonical = _source(source)
    if canonical is None or not HEX.fullmatch(revision):
        raise DiscoveryError("INVALID_PINNED_SOURCE")
    _, _, owner, repo = canonical.split("/")
    if not SAFE_SEGMENT.fullmatch(owner) or not SAFE_SEGMENT.fullmatch(repo):
        raise DiscoveryError("INVALID_PINNED_SOURCE")
    return canonical, owner, repo, revision


def _request(owner: str, repo: str, resource: str, revision: str) -> dict:
    """A fixed-host HTTPS GET without redirects, environment proxy or credentials."""
    if not (SAFE_SEGMENT.fullmatch(owner) and SAFE_SEGMENT.fullmatch(repo)
            and resource in {"commits", "git/trees"} and HEX.fullmatch(revision)):
        raise DiscoveryError("INVALID_HTTP_TARGET")
    target = f"/repos/{owner}/{repo}/{resource}/{revision}"
    if resource == "git/trees":
        target += "?recursive=1"
    client = http.client.HTTPSConnection("api.github.com", timeout=8,
                                       context=ssl.create_default_context())
    try:
        client.request("GET", target, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "adt-pinned-skill-discovery/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        response = client.getresponse()
        if response.status != 200:
            raise DiscoveryError("GITHUB_METADATA_UNAVAILABLE")
        if (response.getheader("Content-Encoding") not in (None, "identity")
                or (response.getheader("Content-Length") is not None
                    and int(response.getheader("Content-Length")) > MAX_BYTES)):
            raise DiscoveryError("OVERSIZED_OR_ENCODED_RESPONSE")
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise DiscoveryError("OVERSIZED_OR_ENCODED_RESPONSE")
        value = json.loads(data.decode("utf-8"))
        if not isinstance(value, dict):
            raise DiscoveryError("INVALID_GITHUB_METADATA")
        return value
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        if isinstance(error, DiscoveryError):
            raise
        raise DiscoveryError("GITHUB_METADATA_UNAVAILABLE") from None
    finally:
        client.close()


def _skill_path(path: object) -> str | None:
    if not isinstance(path, str) or len(path) > 240 or "\\" in path:
        return None
    pieces = path.split("/")
    if not pieces or pieces[-1] != "SKILL.md":
        return None
    if not all(SAFE_SEGMENT.fullmatch(x) and x not in {".", ".."} for x in pieces[:-1]):
        return None
    return "/".join(pieces)


def discover(
    query: str,
    *,
    opt_in: bool = False,
    allowed_sources: tuple[str, ...] = (),
    fetch_json=None,
) -> dict:
    local = _assess_skill_coverage(query)
    base = {
        "schema_version": 1, "local_skill_coverage": local,
        "installation": "NOT_AUTHORIZED", "execution": "NOT_RUN",
        "client_activation": "NOT_OBSERVED",
        "skills_content_downloaded": False,
        "license_independently_verified": False,
        "remote_security_gate": "NOT_RUN",
        "requires_manual_review": True,
    }
    if not opt_in and not allowed_sources:
        return {**base, "status": "NO_NETWORK", "candidates": []}
    if not opt_in or not isinstance(allowed_sources, tuple) or not 1 <= len(allowed_sources) <= MAX_REPOS:
        return {**base, "status": "REJECT", "reason": "OPT_IN_AND_PINNED_ALLOWLIST_REQUIRED",
                "candidates": []}
    try:
        pins = [_pin(source) for source in allowed_sources]
    except DiscoveryError as exc:
        return {**base, "status": "REJECT", "reason": str(exc), "candidates": []}
    if len({source.lower() for source, _, _, _ in pins}) != len(pins):
        return {**base, "status": "REJECT", "reason": "DUPLICATE_SOURCE", "candidates": []}
    fetcher = _request if fetch_json is None else fetch_json
    tokens = {t for t in re.findall(r"(?u)\b[\w-]{3,}\b", query.casefold())}
    candidates = []
    try:
        for url, owner, repo, commit_sha in pins:
            commit = fetcher(owner, repo, "commits", commit_sha)
            if not isinstance(commit, dict) or commit.get("sha") != commit_sha:
                raise DiscoveryError("REVISION_NOT_VERIFIED")
            commit_info = commit.get("commit")
            tree_info = commit_info.get("tree") if isinstance(commit_info, dict) else None
            tree_sha = tree_info.get("sha") if isinstance(tree_info, dict) else None
            if not isinstance(tree_sha, str) or not HEX.fullmatch(tree_sha):
                raise DiscoveryError("INVALID_GITHUB_METADATA")
            tree = fetcher(owner, repo, "git/trees", tree_sha)
            if (not isinstance(tree, dict) or tree.get("sha") != tree_sha
                    or tree.get("truncated") is not False or not isinstance(tree.get("tree"), list)
                    or len(tree["tree"]) > MAX_TREE_ENTRIES):
                raise DiscoveryError("UNTRUSTED_OR_TRUNCATED_TREE")
            for entry in tree["tree"]:
                if not isinstance(entry, dict) or entry.get("type") != "blob":
                    continue
                path = _skill_path(entry.get("path"))
                if path is None:
                    continue
                score = sum(1 for word in tokens
                            if word in re.findall(r"(?u)[\w-]+", path.casefold()))
                if score == 0:
                    continue
                candidates.append({
                    "source_url": url, "revision": commit_sha, "path": path,
                    "lexical_score": score, "license": "NOT_VERIFIED",
                    "content": "NOT_DOWNLOADED", "provenance": "PUBLIC_GITHUB_METADATA_ONLY",
                })
    except DiscoveryError as exc:
        return {**base, "status": "REJECT", "reason": str(exc), "candidates": []}
    except (OSError, ValueError, TypeError):
        return {**base, "status": "REJECT", "reason": "GITHUB_METADATA_UNAVAILABLE",
                "candidates": []}
    candidates.sort(key=lambda item: (-item["lexical_score"], item["source_url"], item["path"]))
    return {
        **base, "status": "REVIEW_ONLY",
        "external_search": "EXPLICIT_PINNED_GITHUB_METADATA",
        "query_match": "LEXICAL_ONLY_NOT_SEMANTIC",
        "candidates": candidates[:MAX_MATCHES],
        "truncated_results": len(candidates) > MAX_MATCHES,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--discover", action="store_true",
                        help="Explicit authorization for public GitHub metadata requests")
    parser.add_argument("--allow-repo", action="append", default=[],
                        help="Pinned URL: https://github.com/owner/repo@<40-character commit SHA>")
    args = parser.parse_args(argv)
    try:
        result = discover(args.query, opt_in=args.discover,
                          allowed_sources=tuple(args.allow_repo))
    except (TypeError, ValueError):
        result = {"status": "REJECT", "reason": "INVALID_QUERY",
                  "installation": "NOT_AUTHORIZED", "candidates": []}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 2 if result["status"] == "REJECT" else (1 if args.discover else 0)


if __name__ == "__main__":
    raise SystemExit(main())
