#!/usr/bin/env python3
"""Offline bounded ZIP source audit; does not extract, install or execute."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import stat
import sys
import zipfile
from validate_public_docs_neutrality import (
    _repo_namespace, BINARY_SUFFIXES, MAX_SOURCE_BYTES,
)

MAX_ZIP_BYTES = 128 * 1024 * 1024
MAX_MEMBERS = 5000
MAX_TOTAL_BYTES = 256 * 1024 * 1024
NESTED_ARCHIVES = {".zip", ".tar", ".gz", ".tgz", ".7z", ".rar"}


def audit_zip(path: Path, *, repository: str | None = None,
              deny_patterns: tuple[str, ...] = ()) -> dict:
    found = []
    skipped = checked = 0
    literals = tuple(s.casefold() for s in deny_patterns)
    def fail(name: str, number: int, code: str) -> None:
        safe = "[REDACTED_PATH]" if any(s in name.casefold() for s in literals) else name
        found.append({"file": safe, "line": number, "token": code})
    if any(not isinstance(s, str) or not s or len(s) > 256 for s in deny_patterns):
        fail(".", 0, "INVALID_DENYLIST")
    elif (not path.is_file() or path.is_symlink()
          or path.stat().st_size > MAX_ZIP_BYTES):
        fail(".", 0, "UNSAFE_OR_OVERSIZED_ARCHIVE")
    else:
        try:
            namespace = _repo_namespace(repository)
            with zipfile.ZipFile(path) as archive:
                infos = archive.infolist()
                if not infos or len(infos) > MAX_MEMBERS:
                    fail(".", 0, "INVALID_MEMBER_COUNT")
                seen: set[str] = set()
                regular: set[str] = set()
                total = 0
                for entry in infos:
                    name = entry.filename
                    parts = name.rstrip("/").split("/")
                    key = name.rstrip("/").casefold()
                    if (not name or name.startswith("/") or "\\" in name
                        or "\x00" in name or re.match(r"^[A-Za-z]:", name)
                        or any(p in {"", ".", ".."} for p in parts)):
                        fail(name, 0, "UNSAFE_ARCHIVE_PATH")
                        continue
                    if key in seen:
                        fail(name, 0, "DUPLICATE_ARCHIVE_PATH")
                        continue
                    seen.add(key)
                    if (stat.S_IFMT(entry.external_attr >> 16)
                        not in {0, stat.S_IFREG, stat.S_IFDIR}):
                        fail(name, 0, "UNSAFE_ARCHIVE_MEMBER_TYPE")
                        continue
                    if entry.flag_bits & 1:
                        fail(name, 0, "ENCRYPTED_ARCHIVE_MEMBER")
                        continue
                    if any("/".join(parts[:n]).casefold() in regular
                           for n in range(1, len(parts))):
                        fail(name, 0, "FILE_DIRECTORY_COLLISION")
                    if entry.is_dir():
                        continue
                    regular.add(key)
                    total += entry.file_size
                    if total > MAX_TOTAL_BYTES:
                        fail(name, 0, "UNCOMPRESSED_SIZE_LIMIT")
                        break
                    if ((not entry.compress_size and entry.file_size)
                        or (entry.compress_size and entry.file_size / entry.compress_size > 200)):
                        fail(name, 0, "COMPRESSION_RATIO_LIMIT")
                        continue
                    if any(s in name.casefold() for s in literals):
                        fail(name, 0, "PRIVATE_IDENTIFIER_IN_PATH")
                    if namespace:
                        owner, own = namespace
                        owner_re = r"(?<![\w.-])" + re.escape(owner) + r"/([a-z0-9_.-]+)"
                        if any(m.group(1).lower().rstrip(".,;").removesuffix(".git") != own
                               for m in re.finditer(owner_re, name, re.I)):
                            fail(name, 0, "FOREIGN_OWNER_PATH")
                    suffix = Path(name).suffix.lower()
                    if suffix in NESTED_ARCHIVES:
                        fail(name, 0, "NESTED_ARCHIVE_UNINSPECTED")
                        continue
                    if suffix in BINARY_SUFFIXES or entry.file_size > MAX_SOURCE_BYTES:
                        skipped += 1
                        continue
                    data = archive.read(entry)
                    if b"\x00" in data:
                        skipped += 1
                        continue
                    try:
                        lines = data.decode("utf-8-sig").splitlines()
                    except UnicodeError:
                        skipped += 1
                        continue
                    checked += 1
                    for line_no, line in enumerate(lines, 1):
                        lower = line.casefold()
                        if any(s in lower for s in literals):
                            fail(name, line_no, "PRIVATE_IDENTIFIER")
                        elif namespace:
                            if any(m.group(1).lower().rstrip(".,;").removesuffix(".git") != own
                                   for m in re.finditer(owner_re, line, re.I)):
                                fail(name, line_no, "FOREIGN_OWNER_REPOSITORY")
        except (OSError, ValueError, EOFError, RuntimeError, zipfile.BadZipFile):
            fail(".", 0, "INVALID_OR_CORRUPT_ARCHIVE")
    return {
        "status": "FAIL" if found else "PASS",
        "findings": found, "text_members_scanned": checked,
        "opaque_members_uninspected": skipped,
        "binary_contents_verified": skipped == 0,
        "archive_extracted": False, "model_calls": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--repository")
    parser.add_argument("--local-denylist", type=Path)
    args = parser.parse_args(argv)
    literals: tuple[str, ...] = ()
    if args.local_denylist:
        path = args.local_denylist
        if (path.is_symlink() or not path.is_file() or path.stat().st_size > 8192
            or path.resolve().is_relative_to(Path(__file__).resolve().parents[1])):
            print('{"status":"FAIL","token":"INVALID_DENYLIST"}')
            return 2
        literals = tuple(line.strip() for line in path.read_text(encoding="utf-8").splitlines()
                         if line.strip() and not line.lstrip().startswith("#"))
    report = audit_zip(args.zip, repository=args.repository, deny_patterns=literals)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
