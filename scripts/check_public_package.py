#!/usr/bin/env python3
"""Offline publication hygiene gate; diagnostic output never contains matched values.

Scans files inside the supplied tree, including untracked files, but never
follows symbolic links or junctions. This is not comprehensive secret scanning.
"""
from __future__ import annotations

import os
import re
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Repository-specific distribution exclusions (not personal account markers).
FORBIDDEN_NAMES = frozenset({
    "LICENSE.personal.txt", "make-feature-0.3.0.tar.gz",
    "make-feature-0.3.0.tar(1).gz",
})
FORBIDDEN_SUFFIXES = frozenset({
    ".exe", ".dll", ".pem", ".p12", ".pfx", ".key", ".zip", ".tgz",
    ".gz", ".tar", ".7z", ".rar", ".pyc", ".sqlite", ".db",
})
CREDENTIAL_FILES = frozenset({
    ".npmrc", ".pypirc", "credentials.json", "id_rsa", "id_ed25519",
})
# Ignore only generated local folders, not arbitrary hidden folders.
SKIP_DIRS = frozenset({
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".venv", "venv", ".hermes-compat", ".artifacts", "dist", "build",
})
# Only these two already reviewed branding assets are expected binary files.
ALLOWED_IMAGES = frozenset({
    "assets/branding/hero.png", "assets/branding/social-preview.png",
})
MAX_TEXT_BYTES = 2_000_000
SECRETS = {
    "private-key-header": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "github-classic-token": r"gh[opusr]_[A-Za-z0-9]{36}",
    "github-fine-grained-token": r"github_pat_[A-Za-z0-9_]{82,}",
    "aws-access-key": r"(?:AKIA|ASIA)[0-9A-Z]{16}",
    "openai-project-key": r"sk-proj-[A-Za-z0-9_-]{30,}",
}
RULES = {name: re.compile(pattern) for name, pattern in SECRETS.items()}


def _linked(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def scan(root: Path = ROOT) -> list[str]:
    """Report only path, rule and line. Do not follow links or read outside root."""
    findings: list[str] = []
    if _linked(root) or not root.is_dir():
        return ["Invalid or linked scan root"]

    def walk_error(error: OSError) -> None:
        # Do not echo exception details: OS errors can contain private paths.
        findings.append("Cannot enumerate directory")

    for folder, dirs, files in os.walk(root, topdown=True, followlinks=False,
                                       onerror=walk_error):
        parent = Path(folder)
        for dirname in sorted(dirs):
            if dirname in SKIP_DIRS:
                dirs.remove(dirname)
                continue
            entry = parent / dirname
            if _linked(entry):
                findings.append(f"Linked directory: {entry.relative_to(root).as_posix()}")
                dirs.remove(dirname)
        dirs.sort()
        for filename in sorted(files):
            path = parent / filename
            relative = path.relative_to(root).as_posix()
            if _linked(path):
                findings.append(f"Linked file: {relative}")
                continue
            try:
                mode = path.lstat().st_mode
            except OSError:
                findings.append(f"Unreadable file: {relative}")
                continue
            if not stat.S_ISREG(mode):
                findings.append(f"Unexpected special file: {relative}")
                continue
            if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
                findings.append(f"Forbidden file type: {relative}")
            if path.name.startswith(".env") and path.name != ".env.example":
                findings.append(f"Environment file: {relative}")
            if path.name in CREDENTIAL_FILES:
                findings.append(f"Credential configuration file: {relative}")
            try:
                data = path.read_bytes()
            except (OSError, ValueError):
                findings.append(f"Unreadable file: {relative}")
                continue
            if relative in ALLOWED_IMAGES and data.startswith(b"\x89PNG\r\n\x1a\n"):
                continue
            if len(data) > MAX_TEXT_BYTES:
                findings.append(f"Oversized unreviewed file: {relative}")
                continue
            try:
                content = data.decode("utf-8")
            except UnicodeError:
                findings.append(f"Unexpected binary file: {relative}")
                continue
            if "\x00" in content:
                findings.append(f"Unexpected binary file: {relative}")
                continue
            for label, pattern in RULES.items():
                match = pattern.search(content)
                if match:
                    line = content.count("\n", 0, match.start()) + 1
                    findings.append(f"Sensitive content: {relative}:{line} / {label}")
    return findings


def main() -> int:
    findings = scan()
    for finding in findings:
        print(f"FAIL: {finding}")
    if findings:
        print(f"FAIL: {len(findings)} publication hygiene issue(s)")
        return 1
    print("PASS: publication hygiene checks (limited high-confidence patterns)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
