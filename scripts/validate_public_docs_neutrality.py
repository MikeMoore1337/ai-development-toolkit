#!/usr/bin/env python3
"""Check tracked public sources for project-specific references without storing private names.

CI uses only generic namespace rules. A local operator can additionally supply an
untracked denylist outside the repository to check exact private identifiers.
No network, content execution, mutation, or project-source collection.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = frozenset({
    ".git", ".venv", "venv", "node_modules", ".artifacts",
    "__pycache__", ".pytest_cache", ".hermes-compat",
})
BINARY_SUFFIXES = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
    ".zip", ".gz", ".tgz", ".woff", ".woff2", ".ttf", ".otf",
    ".exe", ".dll", ".so", ".dylib", ".pyc", ".db", ".sqlite",
})
MAX_SOURCE_BYTES = 4 * 1024 * 1024


def _paths(root: Path) -> list[Path]:
    if (root / ".git").is_file() or (root / ".git" / "HEAD").exists():
        run = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached"],
            capture_output=True, check=False, timeout=15,
        )
        if run.returncode:
            raise ValueError("Cannot verify tracked-file inventory")
        names = [os.fsdecode(v) for v in run.stdout.split(b"\0") if v]
        return [root / name for name in names]
    # Disposable synthetic fixtures in unit tests have no Git metadata.
    return sorted(path for path in root.rglob("*") if path.is_file() or path.is_symlink())


def _repo_namespace(repository: str | None) -> tuple[str, str] | None:
    name = repository or os.environ.get("GITHUB_REPOSITORY")
    if not name:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name):
        raise ValueError("Invalid repository identity")
    owner, project = name.split("/", 1)
    return owner.casefold(), project.casefold()


def audit(
    root: Path = ROOT, *, deny_patterns: tuple[str, ...] = (),
    repository: str | None = None,
) -> list[dict[str, object]]:
    """Read-only findings; no blocked private tokens included in reports."""
    if not root.is_dir() or root.is_symlink():
        return [{"file": ".", "line": 0, "token": "INVALID_ROOT"}]
    findings: list[dict[str, object]] = []
    try:
        paths = _paths(root)
        namespace = _repo_namespace(repository)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return [{"file": ".", "line": 0, "token": "INVENTORY_UNAVAILABLE"}]
    if any(not isinstance(v, str) or not v.strip() or len(v) > 256 for v in deny_patterns):
        return [{"file": ".", "line": 0, "token": "INVALID_DENYLIST"}]
    private = tuple(v.casefold() for v in deny_patterns)
    for path in paths:
        rel = path.relative_to(root)
        name = rel.as_posix()
        if SKIP_DIRS.intersection(rel.parts):
            continue
        if path.is_symlink() or not path.is_file():
            findings.append({"file": name, "line": 0, "token": "UNSAFE_LINK"})
            continue
        if any(p in name.casefold() for p in private):
            findings.append({"file": name, "line": 0, "token": "PRIVATE_NAME_IN_PATH"})
        if path.suffix.casefold() in BINARY_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_SOURCE_BYTES:
                findings.append({"file": name, "line": 0, "token": "OVERSIZED_SOURCE"})
                continue
            data = path.read_bytes()
            if b"\0" in data:
                continue  # non-text tracked binary
            lines = data.decode("utf-8-sig").splitlines()
        except (OSError, UnicodeError):
            findings.append({"file": name, "line": 0, "token": "UNREADABLE"})
            continue
        for number, line in enumerate(lines, 1):
            lower = line.casefold()
            if any(v in lower for v in private):
                findings.append({"file": name, "line": number, "token": "PRIVATE_IDENTIFIER"})
                continue
            if namespace:
                owner, project = namespace
                # Other repositories of the same maintainer are integration data,
                # not generic Toolkit fixtures or enforced project policy.
                pattern = re.compile(r"(?<![\w.-])" + re.escape(owner) + r"/([a-z0-9_.-]+)", re.I)
                for match in pattern.finditer(line):
                    if match.group(1).casefold().rstrip(".,;").removesuffix(".git") != project:
                        findings.append({"file": name, "line": number, "token": "FOREIGN_OWNER_REPOSITORY"})
                        break
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--repository", help="owner/repository; in CI defaults to GITHUB_REPOSITORY")
    parser.add_argument("--local-denylist", type=Path, help="untracked local UTF-8 file, one literal per line")
    args = parser.parse_args()
    patterns: tuple[str, ...] = ()
    if args.local_denylist:
        source = args.local_denylist
        if source.is_symlink() or not source.is_file() or source.stat().st_size > 8192:
            print('{"status":"FAIL","error":"INVALID_DENYLIST"}')
            return 2
        patterns = tuple(line.strip() for line in source.read_text(encoding="utf-8").splitlines()
                         if line.strip() and not line.strip().startswith("#"))
    found = audit(args.root.resolve(), deny_patterns=patterns, repository=args.repository)
    print(json.dumps({
        "status": "FAIL" if found else "PASS",
        "tracked_text_findings": len(found), "findings": found,
    }, ensure_ascii=False, indent=2))
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
