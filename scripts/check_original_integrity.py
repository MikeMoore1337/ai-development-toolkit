#!/usr/bin/env python3
"""Read-only integrity check for installed original skills with UPSTREAM.json.

Checks local bytes against installer metadata, NOT independently authenticated
upstream code. Independently verify the immutable GitHub commit before claiming
an unmodified original. Exit 0=locally consistent, 1=drift, 2=unattested.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
MAX_MANIFEST_SIZE = 128 * 1024
MAX_FILES = 2_000


def _safe_file(root: Path, name: object) -> Path | None:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        return None
    parts = name.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return None
    path = root.joinpath(*parts)
    try:
        if not path.resolve().is_relative_to(root.resolve()):
            return None
        current = root
        for part in path.relative_to(root).parts:
            current = current / part
            if current.is_symlink():
                return None
    except (ValueError, OSError):
        return None
    return path


def verify(root: Path, *, expected_repo: str | None = None,
           expected_commit: str | None = None) -> dict:
    root = root.resolve()
    result: dict = {"status": "SOURCE_DRIFT", "files_checked": 0,
                    "files_matched": 0, "mismatches": [], "issues": [],
                    "upstream_identity_verified": False}
    manifest = root / "UPSTREAM.json"
    if not manifest.exists() and not manifest.is_symlink():
        result["status"] = "NO_LOCAL_MANIFEST"
        result["issues"].append("UPSTREAM.json missing; original source is not attested")
        return result
    try:
        if (manifest.is_symlink() or not manifest.is_file()
                or manifest.stat().st_size > MAX_MANIFEST_SIZE):
            raise ValueError("unsafe or oversized UPSTREAM.json")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("manifest is not an object")
        repo, commit, files = data.get("repo"), data.get("commit"), data.get("files")
        if (not isinstance(repo, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo)
                or not isinstance(commit, str) or not COMMIT.fullmatch(commit)
                or not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES):
            raise ValueError("invalid source metadata or file list")
        result.update(declared_repo=repo, declared_commit=commit)
        if expected_repo is not None and expected_repo != repo:
            result["issues"].append("declared repository differs from expected repository")
        if expected_commit is not None and expected_commit != commit:
            result["issues"].append("declared commit differs from expected commit")
        names: set[str] = set()
        for entry in files:
            if not isinstance(entry, dict):
                result["issues"].append("invalid file entry")
                continue
            name, digest, size = entry.get("path"), entry.get("sha256"), entry.get("bytes")
            file = _safe_file(root, name)
            if (file is None or name in names or not isinstance(digest, str)
                    or not SHA256.fullmatch(digest)
                    or not isinstance(size, int) or isinstance(size, bool) or size < 0):
                result["issues"].append("unsafe or malformed file entry")
                continue
            names.add(name)
            result["files_checked"] += 1
            if not file.is_file():
                result["mismatches"].append(name)
                continue
            actual = hashlib.sha256(file.read_bytes()).hexdigest()
            if file.stat().st_size != size or actual != digest:
                result["mismatches"].append(name)
            else:
                result["files_matched"] += 1
        if "SKILL.md" not in names:
            result["issues"].append("SKILL.md is not in the manifest")
        if not result["issues"] and not result["mismatches"] and result["files_checked"] == len(files):
            result["status"] = "CONSISTENT_WITH_LOCAL_MANIFEST"
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        result["issues"].append(f"invalid UPSTREAM.json: {type(error).__name__}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", type=Path, help="Installed original skill directory (read-only)")
    parser.add_argument("--expected-repo", help="Repository from independently reviewed canonical source")
    parser.add_argument("--expected-commit", help="Immutable source SHA, independently verified")
    args = parser.parse_args()
    result = verify(args.skill_dir, expected_repo=args.expected_repo, expected_commit=args.expected_commit)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return {"CONSISTENT_WITH_LOCAL_MANIFEST": 0, "NO_LOCAL_MANIFEST": 2}.get(result["status"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
