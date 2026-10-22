#!/usr/bin/env python3
"""Offline, read-only review gate for candidate third-party Agent Skills.

This scanner is advisory and does not download, execute, install or authorize skills.
The manifest is operator-supplied metadata, not trusted evidence of upstream origin.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlsplit

MAX_MANIFEST_BYTES = 32_768
MAX_FILES = 80
MAX_FILE_BYTES = 512 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024
PIN = re.compile(r"[a-f0-9]{40}\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "CC0-1.0", "ISC", "MPL-2.0"}
SCRIPT_SUFFIXES = {".sh", ".bash", ".ps1", ".bat", ".cmd", ".py", ".js", ".mjs", ".exe", ".dll", ".so"}
SUSPICIOUS = (
    re.compile(r"ignore (?:all |previous |prior )?instructions", re.I),
    re.compile(r"(?:curl|wget)\s+.*(?:\||-o|--output)", re.I),
    re.compile(r"\b(?:rm\s+-rf|subprocess\.|os\.system\(|eval\(|exec\()", re.I),
    re.compile(r"(?:\.ssh/|\.aws/|\.config/|\.env\b|api[_-]?key|access[_-]?token)", re.I),
    re.compile(r"(?:send|upload|exfiltrat).{0,60}(?:secret|token|cookie|credential|repository)", re.I),
)


def _issue(code: str, severity: str, path: str | None = None) -> dict:
    result = {"code": code, "severity": severity}
    if path is not None:
        result["path"] = path
    return result


def _safe_name(name: object) -> bool:
    if not isinstance(name, str) or not name or len(name) > 240 or "\\" in name:
        return False
    if any(ord(char) < 32 for char in name):
        return False
    pure = PurePosixPath(name)
    return not pure.is_absolute() and all(segment not in {"", ".", ".."} for segment in name.split("/"))


def _manifest(source: Path, issues: list[dict]) -> dict | None:
    try:
        if source.is_symlink() or not source.is_file() or source.stat().st_size > MAX_MANIFEST_BYTES:
            raise ValueError("Missing, linked or oversized manifest")
        data = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data) != {
            "schema_version", "candidate_id", "source_url", "source_revision", "license", "files"
        } or data["schema_version"] != 1:
            raise ValueError("Invalid manifest structure")
        if not isinstance(data["candidate_id"], str) or not SLUG.fullmatch(data["candidate_id"]):
            raise ValueError("Invalid candidate ID")
        if not isinstance(data["source_revision"], str) or not PIN.fullmatch(data["source_revision"]):
            raise ValueError("Revision must be a full pinned commit SHA")
        if not isinstance(data["source_url"], str):
            raise ValueError("Invalid source URL")
        url = urlsplit(data["source_url"])
        if (url.scheme != "https" or url.hostname != "github.com" or url.username or url.password
                or url.port is not None or url.query or url.fragment
                or not re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", url.path)):
            raise ValueError("Source must be an explicit HTTPS GitHub repository URL")
        files = data["files"]
        if (not isinstance(files, dict) or not 1 <= len(files) <= MAX_FILES
                or "SKILL.md" not in files or any(not _safe_name(path)
                or not isinstance(digest, str) or not DIGEST.fullmatch(digest)
                for path, digest in files.items())):
            raise ValueError("Invalid or unpinned expected file inventory")
        return data
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        issues.append(_issue("INVALID_MANIFEST", "BLOCK"))
        return None


def review(candidate_dir: Path, manifest_file: Path) -> dict:
    """Inspect a local candidate only. No network, subprocess or writes."""
    issues: list[dict] = []
    data = _manifest(manifest_file, issues)
    if candidate_dir.is_symlink() or not candidate_dir.is_dir():
        issues.append(_issue("INVALID_CANDIDATE_DIRECTORY", "BLOCK"))
    actual: dict[str, Path] = {}
    total = 0
    if candidate_dir.is_dir() and not candidate_dir.is_symlink():
        for directory, subdirs, filenames in os.walk(candidate_dir, topdown=True, followlinks=False):
            parent = Path(directory)
            for subdir in list(subdirs):
                folder = parent / subdir
                rel = folder.relative_to(candidate_dir).as_posix()
                if folder.is_symlink() or subdir == ".git":
                    issues.append(_issue("UNSAFE_DIRECTORY", "BLOCK", rel))
                    subdirs.remove(subdir)
            for filename in filenames:
                path = parent / filename
                rel = path.relative_to(candidate_dir).as_posix()
                if not _safe_name(rel) or path.is_symlink() or not path.is_file():
                    issues.append(_issue("UNSAFE_FILE", "BLOCK", rel))
                    continue
                actual[rel] = path
                if len(actual) > MAX_FILES:
                    issues.append(_issue("TOO_MANY_FILES", "BLOCK"))
                    break
            if len(actual) > MAX_FILES:
                break
    if data is not None:
        license_name = data["license"]
        if not isinstance(license_name, str) or license_name not in LICENSES:
            issues.append(_issue("LICENSE_UNVERIFIED", "REVIEW"))
        expected = set(data["files"])
        for path in sorted(expected - set(actual)):
            issues.append(_issue("EXPECTED_FILE_MISSING", "BLOCK", path))
        for path in sorted(set(actual) - expected):
            issues.append(_issue("UNDECLARED_FILE", "BLOCK", path))
    for rel, path in sorted(actual.items()):
        try:
            size = path.stat().st_size
            total += size
            if size > MAX_FILE_BYTES:
                issues.append(_issue("OVERSIZED_FILE", "BLOCK", rel))
                continue
            if total > MAX_TOTAL_BYTES:
                issues.append(_issue("PACKAGE_TOO_LARGE", "BLOCK"))
                break
            body = path.read_bytes()
            if data is not None and rel in data["files"]:
                if hashlib.sha256(body).hexdigest() != data["files"][rel]:
                    issues.append(_issue("CHECKSUM_MISMATCH", "BLOCK", rel))
            if b"\x00" in body:
                issues.append(_issue("BINARY_CONTENT", "REVIEW", rel))
                continue
            try:
                text = body.decode("utf-8")
            except UnicodeDecodeError:
                issues.append(_issue("NON_UTF8_CONTENT", "REVIEW", rel))
                continue
            if path.suffix.lower() in SCRIPT_SUFFIXES or "scripts/" in rel or "hooks/" in rel:
                issues.append(_issue("EXECUTABLE_OR_HOOK", "REVIEW", rel))
            if any(pattern.search(text) for pattern in SUSPICIOUS):
                issues.append(_issue("SUSPICIOUS_INSTRUCTIONS", "REVIEW", rel))
            if rel == "SKILL.md":
                if not text.startswith("---\n"):
                    issues.append(_issue("SKILL_FRONTMATTER_MISSING", "REVIEW", rel))
                elif data is not None:
                    frontmatter = text.split("---\n", 2)
                    name = re.search(r"^name:\s*([a-z0-9-]+)\s*$",
                                     frontmatter[1] if len(frontmatter) > 1 else "",
                                     flags=re.M)
                    if name is None:
                        issues.append(_issue("SKILL_NAME_MISSING", "REVIEW", rel))
                    elif name.group(1) != data["candidate_id"]:
                        issues.append(_issue("SKILL_NAME_MISMATCH", "BLOCK", rel))
        except OSError:
            issues.append(_issue("UNREADABLE_FILE", "BLOCK", rel))
    severity = {item["severity"] for item in issues}
    decision = ("REJECT" if "BLOCK" in severity else
                "NEEDS_MANUAL_REVIEW" if "REVIEW" in severity else "ALLOW_FOR_REVIEW")
    return {
        "schema_version": 1,
        "decision": decision,
        "issues": issues,
        "file_count": len(actual),
        "external_fetch": "NOT_RUN",
        "execution": "NOT_RUN",
        "installation": "NOT_AUTHORIZED",
        "provenance_verified": False,
        "status": "OFFLINE_STATIC_ADVISORY_ONLY",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)
    result = review(args.candidate_dir, args.manifest)
    print(json.dumps(result, indent=2, sort_keys=True))
    return {"ALLOW_FOR_REVIEW": 0, "NEEDS_MANUAL_REVIEW": 1, "REJECT": 2}[result["decision"]]


if __name__ == "__main__":
    sys.exit(main())
