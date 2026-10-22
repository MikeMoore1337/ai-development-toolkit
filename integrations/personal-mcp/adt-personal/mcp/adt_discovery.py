"""Bounded, read-only, opt-in GitHub Skill path discovery for personal MCP.

Only public, pinned Git commit/tree *metadata* is requested. Never fetch
SKILL.md bodies, install, execute, or assert license/identity verification.
The operator/client MUST supply each precise pinned repository explicitly.
"""
from __future__ import annotations

import http.client
import json
import re
import ssl

ROOT = re.compile(r"https://github\.com/([A-Za-z0-9][A-Za-z0-9_.-]{0,99})/([A-Za-z0-9][A-Za-z0-9_.-]{0,99})@([0-9a-f]{40})\Z")
SEGMENT = re.compile(r"\.?[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_BYTES = 256 * 1024
MAX_ENTRIES = 5000
MAX_REPOS = 3
MAX_MATCHES = 20


class DiscoveryDenied(ValueError):
    """Fixed diagnostic codes, never remote text."""


def _pin(raw: object) -> tuple[str, str, str, str]:
    if not isinstance(raw, str) or len(raw) > 240:
        raise DiscoveryDenied("INVALID_PINNED_SOURCE")
    match = ROOT.fullmatch(raw)
    if match is None or any(part in (".", "..") for part in match.group(1, 2)):
        raise DiscoveryDenied("INVALID_PINNED_SOURCE")
    owner, repo, revision = match.groups()
    return "https://github.com/" + owner + "/" + repo, owner, repo, revision


def _skill_path(path: object) -> str | None:
    if not isinstance(path, str) or len(path) > 240 or "\\" in path:
        return None
    segments = path.split("/")
    if len(segments) < 2 or segments[-1] != "SKILL.md":
        return None
    if not all(SEGMENT.fullmatch(x) and x not in (".", "..") for x in segments[:-1]):
        return None
    return path


def _get(owner: str, repo: str, resource: str, revision: str) -> dict:
    """Fixed API host; no redirects, auth, env proxy, cookies or arbitrary URLs."""
    if not (re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", owner)
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", repo)
            and resource in ("git/commits", "git/trees") and SHA.fullmatch(revision)):
        raise DiscoveryDenied("INVALID_HTTP_TARGET")
    path = f"/repos/{owner}/{repo}/{resource}/{revision}"
    if resource == "git/trees":
        path += "?recursive=1"
    conn = http.client.HTTPSConnection("api.github.com", timeout=8,
                                      context=ssl.create_default_context())
    try:
        conn.request("GET", path, headers={
            "User-Agent": "adt-personal-mcp-pinned-skill/1.0",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        response = conn.getresponse()
        if response.status != 200:
            raise DiscoveryDenied("GITHUB_METADATA_UNAVAILABLE")
        size = response.getheader("Content-Length")
        if response.getheader("Content-Encoding") not in (None, "identity"):
            raise DiscoveryDenied("UNEXPECTED_HTTP_ENCODING")
        if size is not None and (not size.isascii() or not size.isdecimal() or int(size) > MAX_BYTES):
            raise DiscoveryDenied("OVERSIZED_GITHUB_METADATA")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise DiscoveryDenied("OVERSIZED_GITHUB_METADATA")
        result = json.loads(raw.decode("utf-8"))
        if not isinstance(result, dict):
            raise DiscoveryDenied("INVALID_GITHUB_METADATA")
        return result
    except (OSError, UnicodeError, ValueError) as exc:
        if isinstance(exc, DiscoveryDenied):
            raise
        raise DiscoveryDenied("GITHUB_METADATA_UNAVAILABLE") from None
    finally:
        conn.close()


def discover(query: str, consent: object, allowed_repos: object, fetcher=None) -> dict:
    """No network without exact boolean opt-in and independent pinned allowlist."""
    base = {
        "schema_version": 1, "installation": "NOT_AUTHORIZED",
        "external_skill_execution": "NOT_RUN", "content_downloaded": False,
        "license_independently_verified": False,
        "security_gate": "NOT_RUN", "client_activation": "NOT_OBSERVED",
        "manual_review_required": True, "candidates": [],
    }
    if not isinstance(query, str) or not query.strip() or len(query) > 500:
        raise DiscoveryDenied("INVALID_QUERY")
    if consent is False and allowed_repos in (None, []):
        return {**base, "status": "NO_NETWORK", "reason": "EXPLICIT_OPT_IN_REQUIRED"}
    if (consent is not True or not isinstance(allowed_repos, list)
            or not 1 <= len(allowed_repos) <= MAX_REPOS):
        return {**base, "status": "REJECT", "reason": "EXPLICIT_OPT_IN_AND_PINS_REQUIRED"}
    try:
        repos = [_pin(v) for v in allowed_repos]
    except DiscoveryDenied as exc:
        return {**base, "status": "REJECT", "reason": str(exc)}
    if len({url.casefold() for url, _, _, _ in repos}) != len(repos):
        return {**base, "status": "REJECT", "reason": "DUPLICATE_REPOSITORY"}
    get = _get if fetcher is None else fetcher
    tokens = {word for word in re.findall(r"\w+", query.casefold().replace("-", " ").replace("_", " ")) if len(word) >= 2}
    candidates: list[dict] = []
    try:
        for url, owner, repo, revision in repos:
            commit = get(owner, repo, "git/commits", revision)
            if not isinstance(commit, dict) or commit.get("sha") != revision:
                raise DiscoveryDenied("COMMIT_SHA_NOT_VERIFIED")
            metadata = commit.get("tree")
            tree_sha = metadata.get("sha") if isinstance(metadata, dict) else None
            if not isinstance(tree_sha, str) or not SHA.fullmatch(tree_sha):
                raise DiscoveryDenied("TREE_SHA_NOT_VERIFIED")
            tree = get(owner, repo, "git/trees", tree_sha)
            if (not isinstance(tree, dict) or tree.get("sha") != tree_sha
                    or tree.get("truncated") is not False
                    or not isinstance(tree.get("tree"), list)
                    or len(tree["tree"]) > MAX_ENTRIES):
                raise DiscoveryDenied("TRUNCATED_OR_UNTRUSTED_TREE")
            for entry in tree["tree"]:
                if not isinstance(entry, dict) or entry.get("type") != "blob" or entry.get("mode") != "100644":
                    continue
                path = _skill_path(entry.get("path"))
                if path is None:
                    continue
                words = set(re.findall(r"\w+", path.casefold().replace("-", " ").replace("_", " ")))
                score = len(words & tokens)
                if score:
                    candidates.append({
                        "source_url": url, "revision": revision, "path": path,
                        "lexical_score": score, "license": "NOT_VERIFIED",
                        "content": "NOT_DOWNLOADED",
                        "trust": "UNVERIFIED_GITHUB_PATH_METADATA",
                    })
    except (DiscoveryDenied, OSError, ValueError, TypeError) as exc:
        reason = str(exc) if isinstance(exc, DiscoveryDenied) else "GITHUB_METADATA_UNAVAILABLE"
        return {**base, "status": "REJECT", "reason": reason}
    candidates.sort(key=lambda x: (-x["lexical_score"], x["source_url"], x["path"]))
    return {
        **base, "status": "REVIEW_ONLY",
        "external_search": "EXPLICIT_PINNED_GITHUB_METADATA",
        "matching": "LEXICAL_ONLY_NOT_SEMANTIC",
        "candidates": candidates[:MAX_MATCHES],
        "truncated_results": len(candidates) > MAX_MATCHES,
    }
