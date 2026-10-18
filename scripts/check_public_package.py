#!/usr/bin/env python3
"""Conservative public-package hygiene checks.

Not a substitute for dedicated secret scanning, code review or license audit.
Findings print rule names and file paths, NEVER the credential-like value.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAD_EXACT = {"LICENSE.personal.txt", "make-feature-0.3.0.tar.gz", "make-feature-0.3.0.tar(1).gz"}
BAD_SUFFIXES = {".exe", ".dll", ".pem", ".p12", ".pfx", ".zip", ".tgz"}
PROJECT_RULES = {
    "nonportable-project": r"(?i)your[- ]fitness[- ]coach|second[- ]brain|\\byfc\\b",
    "private-repository": r"(?i)github\\.com/MikeMoore1337/(?!ai-development-toolkit)",
    "personal-email": r"(?i)mikhail\\.murzaev@",
}
SECRETS = {
    "private-key-header": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "github-classic-token": r"gh[opusr]_[A-Za-z0-9]{36}",
    "github-fine-grained-token": r"github_pat_[A-Za-z0-9_]{82,}",
    "aws-access-key": r"AKIA[0-9A-Z]{16}",
    "openai-project-key": r"sk-proj-[A-Za-z0-9_-]{30,}",
}
RULES = {**PROJECT_RULES, **SECRETS}


def scan(root: Path = ROOT) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        if path.is_symlink():
            findings.append(f"Linked file or directory: {relative}")
            continue
        if not path.is_file():
            continue
        if path.name in BAD_EXACT or path.suffix.lower() in BAD_SUFFIXES:
            findings.append(f"Forbidden file type: {relative}")
        if path.name.startswith(".env") and path.name != ".env.example":
            findings.append(f"Environment file: {relative}")
        try:
            if path.stat().st_size > 2_000_000:
                continue
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in RULES.items():
            if re.search(pattern, content):
                findings.append(f"Sensitive content suspected: {relative} / {label}")
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
