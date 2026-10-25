#!/usr/bin/env python3
"""Offline, read-only evidence gate for public competitor UX comparisons.

No web fetching, screenshots, LLM calls, installations, or writes to projects.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ALLOWED = {"VERIFIED", "UNVERIFIED", "CONTRADICTED"}
REQUIRED = {"feature", "competitor_source", "yfc_source", "competitor", "yfc"}
FORBIDDEN = {"password", "secret", "api_key", "access_token", "session_cookie", "authorization"}
SHA = re.compile(r"^[0-9a-f]{40}$")


def _public_link(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    host = parsed.hostname or ""
    return (
        parsed.scheme == "https"
        and host not in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
        and "." in host
        and not parsed.username
        and not parsed.password
        and not host.endswith((".local", ".internal", ".test", ".invalid"))
        and not (parsed.port and parsed.port != 443)
    )


def validate(packet: object) -> dict:
    errors: list[str] = []
    if not isinstance(packet, dict):
        return {"decision": "BLOCKED", "errors": ["packet must be an object"]}
    if any(k.lower() in FORBIDDEN for k in packet):
        errors.append("sensitive top-level field")
    if packet.get("schema") != 1:
        errors.append("schema must be 1")
    if packet.get("mode") != "PUBLIC_READ_ONLY":
        errors.append("public read-only mode is required")
    if not SHA.fullmatch(str(packet.get("upstream_sha", ""))):
        errors.append("pinned upstream SHA required")
    rows = packet.get("features")
    if not isinstance(rows, list) or not rows or len(rows) > 100:
        errors.append("features must contain 1-100 rows")
        rows = []
    for idx, row in enumerate(rows):
        prefix = f"features[{idx}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: object required")
            continue
        if any(k.lower() in FORBIDDEN for k in row):
            errors.append(f"{prefix}: sensitive field")
        if not REQUIRED.issubset(row):
            errors.append(f"{prefix}: required fields missing")
            continue
        if not isinstance(row["feature"], str) or not row["feature"].strip():
            errors.append(f"{prefix}: missing feature")
        for side in ("competitor", "yfc"):
            if row[side] not in ALLOWED:
                errors.append(f"{prefix}: invalid {side} status")
        for source in ("competitor_source", "yfc_source"):
            if not _public_link(row[source]):
                errors.append(f"{prefix}: invalid {source} public HTTPS URL")
        if row["competitor"] == "VERIFIED" and row["yfc"] == "CONTRADICTED":
            # A gap can be suggested, never asserted as an observed test outcome.
            if row.get("gap") not in ("CANDIDATE", None):
                errors.append(f"{prefix}: unsupported gap conclusion")
        if row.get("gap") == "VERIFIED":
            errors.append(f"{prefix}: use CANDIDATE until independent YFC review")
    return {"decision": "BLOCKED" if errors else "PASS", "errors": errors, "feature_count": len(rows)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path, help="Local JSON packet, never fetched")
    args = parser.parse_args()
    try:
        if args.packet.stat().st_size > 256_000:
            raise ValueError("packet too large")
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
        result = validate(packet)
    except (OSError, ValueError, UnicodeError) as exc:
        result = {"decision": "BLOCKED", "errors": [type(exc).__name__]}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
