#!/usr/bin/env python3
"""Offline checks for explicitly promoted integration source release assets.

GitHub API queries are performed by the workflow, not this script. Its inputs
are data: untrusted workflow run/job JSON and a locally built ZIP set.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

EXPECTED_JOBS = {
    "tests (ubuntu-latest, 3.12)",
    "tests (ubuntu-latest, 3.13)",
    "tests (windows-latest, 3.14)",
    "macOS portability (macos-15, Python 3.12)",
    "macOS portability (macos-15-intel, Python 3.12)",
    "Integration source archives (main only)",
}


class ReleaseBlocked(ValueError):
    pass


def validate_sha(sha: str) -> str:
    if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{40}", sha) is None:
        raise ReleaseBlocked("INVALID_EXACT_SOURCE_SHA")
    return sha


def select_run(sha: str, payload: dict) -> int:
    validate_sha(sha)
    candidates = [
        item for item in payload.get("workflow_runs", [])
        if isinstance(item, dict) and item.get("head_sha") == sha
        and item.get("event") == "push" and item.get("head_branch") == "main"
        and item.get("status") == "completed" and item.get("conclusion") == "success"
        and type(item.get("id")) is int and item["id"] > 0
    ]
    if not candidates:
        raise ReleaseBlocked("NO_SUCCESSFUL_EXACT_MAIN_PUSH_VALIDATION")
    return max(item["id"] for item in candidates)


def verify_jobs(payload: dict) -> None:
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        raise ReleaseBlocked("INVALID_WORKFLOW_JOBS")
    matched = {}
    for job in jobs:
        if not isinstance(job, dict):
            raise ReleaseBlocked("INVALID_WORKFLOW_JOB")
        name = job.get("name")
        if name in EXPECTED_JOBS:
            if name in matched:
                raise ReleaseBlocked("DUPLICATE_REQUIRED_JOB")
            matched[name] = job
    if set(matched) != EXPECTED_JOBS:
        raise ReleaseBlocked("INCOMPLETE_CROSS_PLATFORM_CI")
    if any(job.get("status") != "completed" or job.get("conclusion") != "success"
           for job in matched.values()):
        raise ReleaseBlocked("CROSS_PLATFORM_CI_NOT_SUCCESS")


def verify_bundles(payload: dict, out: Path) -> tuple[list[tuple[str, str]], dict]:
    if payload.get("status") != "SOURCE_ARCHIVES_BUILT_NOT_INSTALLED":
        raise ReleaseBlocked("INVALID_SOURCE_BUILD_STATUS")
    results = payload.get("results")
    if not isinstance(results, list) or len(results) != 2:
        raise ReleaseBlocked("INVALID_SOURCE_ARCHIVE_COUNT")
    seen = set()
    hashes = []
    for entry in results:
        if not isinstance(entry, dict):
            raise ReleaseBlocked("INVALID_SOURCE_ARCHIVE_RESULT")
        path = Path(entry.get("path", "")).resolve()
        if (path.parent != out.resolve() or path.suffix != ".zip"
                or not path.name.startswith("AI-Development-Toolkit-")
                or path.name in seen or not path.is_file()
                or path.stat().st_size > 32 * 1024 * 1024):
            raise ReleaseBlocked("INVALID_SOURCE_ARCHIVE_PATH")
        seen.add(path.name)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry.get("sha256"):
            raise ReleaseBlocked("SOURCE_ARCHIVE_SHA256_MISMATCH")
        with ZipFile(path) as zf:
            names = zf.namelist()
            if zf.testzip() is not None or len(names) != entry.get("members"):
                raise ReleaseBlocked("SOURCE_ARCHIVE_CRC_OR_MEMBERS_FAILED")
            if "Personal-MCP-" in path.name and not {
                "adt-personal/mcp/adt_mcp.py", "adt-personal/mcp/adt_discovery.py"
            }.issubset(names):
                raise ReleaseBlocked("MCP_MODULE_PAIR_INCOMPLETE")
        hashes.append((path.name, digest))
    mcp = [x for x in seen if re.fullmatch(
        r"AI-Development-Toolkit-Personal-MCP-\d+\.\d+\.\d+\.zip", x)]
    plugin = [x for x in seen if re.fullmatch(
        r"AI-Development-Toolkit-ChatGPT-Plugin-\d+\.\d+\.\d+\.zip", x)]
    if len(mcp) != 1 or len(plugin) != 1:
        raise ReleaseBlocked("WRONG_INTEGRATION_BUNDLE_IDENTITIES")
    return sorted(hashes), {
        "mcp_source_version": payload.get("mcp_source_version"),
        "plugin_package_version": payload.get("plugin_package_version"),
        "chatgpt_installed_plugin": "NOT_VERIFIED",
        "installed_client_mcp": "NOT_VERIFIED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--runs-json", type=Path, required=True)
    parser.add_argument("--jobs-json", type=Path)
    parser.add_argument("--build-json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        runs = json.loads(args.runs_json.read_text(encoding="utf-8"))
        run_id = select_run(args.source_sha, runs)
        if not args.jobs_json and not args.build_json and not args.output:
            print(run_id)
            return 0
        if not all((args.jobs_json, args.build_json, args.output)):
            raise ReleaseBlocked("INCOMPLETE_RELEASE_GATE_INPUTS")
        verify_jobs(json.loads(args.jobs_json.read_text(encoding="utf-8")))
        out = args.output.resolve()
        hashes, details = verify_bundles(
            json.loads(args.build_json.read_text(encoding="utf-8")), out)
        (out / "INTEGRATION_SHA256SUMS.txt").write_text(
            "".join(f"{digest}  {name}\n" for name, digest in hashes), encoding="utf-8")
        evidence = {
            "status": "SOURCE_ARCHIVES_VALIDATED_NOT_INSTALLED",
            "source_sha": args.source_sha,
            "validation_run_id": run_id,
            "required_jobs": sorted(EXPECTED_JOBS),
            "source_archives": [{"name": name, "sha256": digest} for name, digest in hashes],
            **details,
        }
        (out / "INTEGRATION_EVIDENCE.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("PASS: exact-SHA Linux/Windows/macOS CI and integration source ZIPs")
        return 0
    except (ReleaseBlocked, OSError, ValueError, KeyError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
