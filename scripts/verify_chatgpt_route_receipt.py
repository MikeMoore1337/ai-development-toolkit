#!/usr/bin/env python3
"""Issue #533: opt-in, offline, fail-closed UX/UI routing receipt validator.

A submitted JSON file is untrusted *assertion data*, not a signed ChatGPT trace.
No chat export API, network requests, telemetry, hooks or background process.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import uuid

SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SEMVER = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
ANON_ID = re.compile(r"task_[0-9a-f]{32}\Z")
EVENT_ID = re.compile(r"evt_[0-9a-f]{32}\Z")
SAFE_REF = re.compile(r"[a-zA-Z0-9_:/#.@?-]{3,300}\Z")
STAGES = ("PREFERENCE_READ", "ORCHESTRA", "ORIGINAL", "ORIGINAL", "ORIGINAL",
          "OWNER_APPROVAL", "REVIEWER", "BROWSER_VERIFICATION")
ORIGINAL_STAGES = {"impeccable": "concept-seed", "design-taste-frontend": "draw-app",
                   "ui-ux-pro-max": "design-system"}
STATUSES = {"OBSERVED", "NOT_VERIFIED", "BLOCKED", "FAILED", "DEGRADED"}
ROOT_FIELDS = {"schema_version", "task_id", "run_kind", "request_blind", "versions", "events"}
VERSION_FIELDS = {"toolkit", "plugin_backend", "active_mount"}
EVENT_FIELDS = {"event_id", "task_id", "sequence", "stage", "status", "observed_at",
                "recorded_at", "evidence_origin", "proof_ref", "data"}
DATA_FIELDS = {
    "PREFERENCE_READ": {"preference_file", "value", "read_source", "tool_result_ref"},
    "ORCHESTRA": {"skill", "mode", "loaded_sources", "tool_result_ref"},
    "ORIGINAL": {"name", "upstream_sha", "entrypoint", "command", "executor",
                 "exit_code", "stage", "artifact", "tool_result_ref", "source_toolkit_sha",
                 "runtime_toolkit_sha", "applicability", "applicability_source", "applicability_reason"},
    "OWNER_APPROVAL": {"decision", "approved_sha256", "message_ref"},
    "REVIEWER": {"mode", "disposition", "tool_result_ref"},
    "BROWSER_VERIFICATION": {"tests_passed", "tests_failed", "executor", "tool_result_ref", "artifact"},
}
# Refuse obvious secret/PII leaks even in synthetic fixtures. The schema also rejects free-form fields.
SENSITIVE = re.compile(r"(?i)(?:gh[pousr]_[a-z0-9_]{8,}|sk-[a-z0-9_-]{8,}|"
                       r"bearer\s+\S+|(?:api[-_ ]?key|authorization|password|token)\s*[:=]|"
                       r"[a-z0-9_.+%-]+@[a-z0-9.-]+\.[a-z]{2,}|"
                       r"[a-z]:[\\/]|\\\\[a-z0-9._-]+[\\/]|(?<!\S)~/|"
                       r"(?<![a-z0-9:/])/(?:[a-z0-9._-]+/)*[a-z0-9._-]+)")


class ReceiptRejected(ValueError):
    """Invalid schema or prohibited data; no rejected content is echoed."""


def _is_str(v: object, limit: int = 300) -> bool:
    return isinstance(v, str) and 0 < len(v) <= limit and v.strip() == v


def _safe_strings(value: object, depth: int = 0) -> None:
    if depth > 16:
        raise ReceiptRejected("NESTING_LIMIT_EXCEEDED")
    if isinstance(value, str):
        if len(value) > 600 or SENSITIVE.search(value):
            raise ReceiptRejected("SECRET_OR_PERSONAL_DATA_REJECTED")
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ReceiptRejected("INVALID_FIELD")
            _safe_strings(key, depth + 1)
            _safe_strings(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _safe_strings(item, depth + 1)


def _only_keys(row: object, fields: set[str]) -> dict:
    if not isinstance(row, dict) or set(row) - fields:
        raise ReceiptRejected("UNKNOWN_OR_INVALID_FIELDS")
    return row


def _unique_json_object(items: list[tuple[str, object]]) -> dict:
    """Reject duplicate keys before JSON decoding discards their first values."""
    row = {}
    for key, value in items:
        if key in row:
            raise ReceiptRejected("DUPLICATE_JSON_FIELD")
        row[key] = value
    return row


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", value):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _artifact(data: object, root: Path) -> str | None:
    """Check caller-supplied relative artifact integrity; never execute files."""
    if not isinstance(data, dict) or set(data) != {"path", "sha256"}:
        return "ARTIFACT_METADATA_INVALID"
    path, digest = data["path"], data["sha256"]
    if not _is_str(path, 200) or not isinstance(digest, str) or not SHA256.fullmatch(digest):
        return "ARTIFACT_METADATA_INVALID"
    rel = PurePosixPath(path)
    if (rel.is_absolute() or any(part in ("", ".", "..") for part in path.split("/"))
            or "\\" in path or ":" in path or not rel.parts
            or not re.fullmatch(r"[a-zA-Z0-9._-]+(?:/[a-zA-Z0-9._-]+)*", path)):
        return "ARTIFACT_PATH_INVALID"
    if root.is_symlink() or (hasattr(root, "is_junction") and root.is_junction()):
        return "ARTIFACT_ROOT_SYMLINK_REJECTED"
    target = root
    for part in rel.parts:
        target = target / part
        if target.is_symlink() or (hasattr(target, "is_junction") and target.is_junction()):
            return "ARTIFACT_SYMLINK_REJECTED"
    if not target.resolve().is_relative_to(root.resolve()):
        return "ARTIFACT_PATH_INVALID"
    if not target.is_file():
        return "ARTIFACT_MISSING"
    if target.stat().st_size > 2 * 1024 * 1024:
        return "ARTIFACT_OVERSIZED"
    if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        return "ARTIFACT_SHA256_MISMATCH"
    return None


def _event_problem(event: dict, root: Path, source_sha: str, run_kind: str) -> list[str]:
    problems = []
    stage, data, status = event["stage"], event["data"], event["status"]
    if not isinstance(stage, str) or stage not in DATA_FIELDS:
        return ["UNKNOWN_STAGE"]
    _only_keys(data, DATA_FIELDS[stage])
    if not isinstance(status, str) or status not in STATUSES or status not in ("OBSERVED", "DEGRADED"):
        problems.append("STAGE_NOT_OBSERVED")
    expected_origin = "OWNER_MESSAGE" if stage == "OWNER_APPROVAL" else "HOST_TOOL_RESULT"
    if run_kind == "LIVE" and event["evidence_origin"] != expected_origin:
        problems.append("LIVE_ORIGIN_UNVERIFIED")
    elif run_kind == "SYNTHETIC" and event["evidence_origin"] != "SYNTHETIC_FIXTURE":
        problems.append("SYNTHETIC_ORIGIN_MISMATCH")
    if not _is_str(event["proof_ref"]) or not SAFE_REF.fullmatch(event["proof_ref"]):
        problems.append("PRIMARY_REFERENCE_INVALID")

    if stage == "PREFERENCE_READ":
        if (data.get("preference_file") != "USER_PREFERENCES.json" or
                data.get("value") != "ALL_THREE" or data.get("read_source") != "tool_result" or
                not _is_str(data.get("tool_result_ref"))):
            problems.append("PREFERENCE_READ_NOT_PROVEN")
    elif stage == "ORCHESTRA":
        sources = data.get("loaded_sources")
        if (data.get("skill") != "ux-ui-design-orchestra" or data.get("mode") != "create-design" or
                not isinstance(sources, list) or not all(_is_str(s, 100) for s in sources) or
                not {"SKILL.md", "CREATE_DESIGN.md", "WORKFLOW.md"}.issubset(set(sources)) or
                not _is_str(data.get("tool_result_ref"))):
            problems.append("ORCHESTRA_NOT_LOADED")
    elif stage == "ORIGINAL":
        name = data.get("name")
        if not isinstance(name, str) or name not in ORIGINAL_STAGES:
            problems.append("UNKNOWN_ORIGINAL")
        if (not isinstance(data.get("upstream_sha"), str) or
                not SHA40.fullmatch(data["upstream_sha"]) or
                not _is_str(data.get("entrypoint"), 200) or
                not _is_str(data.get("executor"), 120) or
                not _is_str(data.get("tool_result_ref"))):
            problems.append("ORIGINAL_PROVENANCE_INCOMPLETE")
        if (data.get("source_toolkit_sha") != source_sha or
                data.get("runtime_toolkit_sha") != source_sha):
            problems.append("SOURCE_RUNTIME_MISMATCH")
        expected_stage = ORIGINAL_STAGES.get(name) if isinstance(name, str) else None
        command = data.get("command")
        if (not _is_str(command, 300) or type(data.get("exit_code")) is not int or
                data["exit_code"] != 0 or
                (isinstance(command, str) and re.search(r"(?i)(?:--help|\bhelp\b|\bcontext\b|\becho\b)", command))):
            problems.append("NATIVE_STAGE_NOT_RUN")
        applicability = data.get("applicability", "APPLICABLE")
        if applicability == "NOT_APPLICABLE_NATIVE_SCOPE":
            if not (_is_str(data.get("applicability_source")) and _is_str(data.get("applicability_reason"))):
                problems.append("SCOPE_EXCLUSION_UNDOCUMENTED")
            problems.append("ORIGINAL_SCOPE_EXCLUDED")
        elif applicability == "NATIVE_SUBSTAGE_NOT_APPLICABLE":
            if not (_is_str(data.get("applicability_source")) and _is_str(data.get("applicability_reason"))):
                problems.append("SUBSTAGE_EXCLUSION_UNDOCUMENTED")
            # Only a *specific native stage* may be skipped, never the original invocation.
            actual_stage = data.get("stage")
            if (not _is_str(actual_stage, 60) or not re.fullmatch(r"[a-z][a-z0-9_-]{2,59}", actual_stage)
                    or actual_stage == expected_stage or actual_stage in {"help", "context", "setup", "install"}):
                problems.append("ALTERNATIVE_NATIVE_STAGE_NOT_RUN")
        elif applicability != "APPLICABLE":
            problems.append("INVALID_APPLICABILITY")
        elif data.get("stage") != expected_stage:
            problems.append("NATIVE_STAGE_NOT_RUN")
        # Even with documented stage non-applicability, a genuine native output is required.
        artifact_problem = _artifact(data.get("artifact"), root)
        if artifact_problem:
            problems.append(artifact_problem)
    elif stage == "OWNER_APPROVAL":
        if (data.get("decision") != "approve" or not _is_str(data.get("message_ref")) or
                not isinstance(data.get("approved_sha256"), str) or
                not SHA256.fullmatch(data["approved_sha256"])):
            problems.append("OWNER_APPROVAL_NOT_PROVEN")
    elif stage == "REVIEWER":
        if (data.get("mode") not in ("NATIVE", "INLINE_DEGRADED") or
                data.get("disposition") != "ship" or not _is_str(data.get("tool_result_ref"))):
            problems.append("REVIEWER_NOT_POSITIVE")
        if data.get("mode") == "INLINE_DEGRADED" and status != "DEGRADED":
            problems.append("INLINE_MUST_BE_DEGRADED")
        if data.get("mode") == "NATIVE" and status != "OBSERVED":
            problems.append("NATIVE_REVIEW_STATUS_INVALID")
    elif stage == "BROWSER_VERIFICATION":
        if (type(data.get("tests_passed")) is not int or data["tests_passed"] < 1 or
                type(data.get("tests_failed")) is not int or data["tests_failed"] != 0 or
                not _is_str(data.get("executor"), 120) or
                not _is_str(data.get("tool_result_ref"))):
            problems.append("BROWSER_TEST_NOT_PROVEN")
        artifact_problem = _artifact(data.get("artifact"), root)
        if artifact_problem:
            problems.append(artifact_problem)
    return problems


def validate(receipt: object, artifact_root: Path) -> dict:
    """Validate assertions and local artifacts, never attest host event authenticity."""
    if not isinstance(receipt, dict):
        raise ReceiptRejected("INVALID_RECEIPT")
    if len(json.dumps(receipt, ensure_ascii=False)) > 100_000:
        raise ReceiptRejected("RECEIPT_TOO_LARGE")
    _safe_strings(receipt)
    _only_keys(receipt, ROOT_FIELDS)
    if set(receipt) != ROOT_FIELDS or receipt["schema_version"] != 1:
        raise ReceiptRejected("RECEIPT_SCHEMA_INVALID")
    task_id = receipt["task_id"]
    if not isinstance(task_id, str) or not ANON_ID.fullmatch(task_id):
        raise ReceiptRejected("INVALID_ANONYMOUS_TASK_ID")
    run_kind = receipt["run_kind"]
    if run_kind not in ("SYNTHETIC", "LIVE") or receipt["request_blind"] not in ("OBSERVED", "NOT_VERIFIED"):
        raise ReceiptRejected("INVALID_RUN_KIND")
    versions = _only_keys(receipt["versions"], VERSION_FIELDS)
    if set(versions) != VERSION_FIELDS:
        raise ReceiptRejected("VERSIONS_MISSING")
    for name in VERSION_FIELDS:
        entry = _only_keys(versions[name], {"version", "source"} if name != "toolkit" else {"sha", "source"})
        if name == "toolkit":
            sha = entry.get("sha")
            if (set(entry) != {"sha", "source"} or not isinstance(sha, str) or
                    (sha != "NOT_VERIFIED" and not SHA40.fullmatch(sha)) or
                    not _is_str(entry["source"])):
                raise ReceiptRejected("SOURCE_SHA_INVALID")
            if (sha == "NOT_VERIFIED") != (entry["source"] == "NOT_VERIFIED"):
                raise ReceiptRejected("SOURCE_ATTESTATION_MISMATCH")
        else:
            v = entry.get("version")
            if (set(entry) != {"version", "source"} or not isinstance(v, str)
                    or (v != "NOT_VERIFIED" and not SEMVER.fullmatch(v)) or
                    not _is_str(entry["source"])):
                raise ReceiptRejected("VERSION_SOURCE_INVALID")
            if (v == "NOT_VERIFIED") != (entry["source"] == "NOT_VERIFIED"):
                raise ReceiptRejected("VERSION_ATTESTATION_MISMATCH")
    events = receipt["events"]
    if not isinstance(events, list) or len(events) > 20:
        raise ReceiptRejected("INVALID_EVENT_COUNT")
    errors: list[str] = ["TOOLKIT_SOURCE_NOT_VERIFIED"] if versions["toolkit"]["sha"] == "NOT_VERIFIED" else []
    # The current offline validator has no authenticated live host mount metadata.
    # A version supplied in a JSON file cannot establish an actual mounted package.
    if run_kind == "LIVE" and versions["active_mount"]["version"] != "NOT_VERIFIED":
        errors.append("ACTIVE_MOUNT_CLAIM_UNATTESTED")
    seen_events: set[str] = set()
    seen_proofs: set[str] = set()
    observed_before = recorded_before = None
    originals: list[str] = []
    for index, event in enumerate(events):
        _only_keys(event, EVENT_FIELDS)
        if set(event) != EVENT_FIELDS:
            raise ReceiptRejected("EVENT_SCHEMA_INVALID")
        ident = event["event_id"]
        if not isinstance(ident, str) or not EVENT_ID.fullmatch(ident) or ident in seen_events:
            errors.append("DUPLICATE_OR_INVALID_EVENT_ID")
        else:
            seen_events.add(ident)
        proof = event["proof_ref"]
        if isinstance(proof, str):
            if proof in seen_proofs:
                errors.append("DUPLICATE_PRIMARY_REFERENCE")
            seen_proofs.add(proof)
        if event["stage"] != "REVIEWER" and event["status"] == "DEGRADED":
            errors.append("DEGRADED_NON_REVIEWER_EVENT")
        if event["task_id"] != task_id:
            errors.append("TASK_ID_MISMATCH")
        if type(event["sequence"]) is not int or event["sequence"] != index + 1:
            errors.append("EVENT_SEQUENCE_NONCONTIGUOUS")
        observed, recorded = _timestamp(event["observed_at"]), _timestamp(event["recorded_at"])
        if not observed or not recorded or observed > recorded:
            errors.append("INVALID_EVENT_TIMES")
        elif recorded - observed > timedelta(minutes=5):
            errors.append("DELAYED_OR_BACKDATED_CAPTURE")
        if observed_before and observed and observed <= observed_before:
            errors.append("BACKDATED_OR_REORDERED_EVENT")
        if recorded_before and recorded and recorded <= recorded_before:
            errors.append("BACKDATED_OR_REORDERED_CAPTURE")
        observed_before, recorded_before = observed, recorded
        if event["stage"] == "ORIGINAL":
            originals.append(event["data"].get("name") if isinstance(event["data"], dict) else None)
        errors.extend(_event_problem(event, artifact_root, versions["toolkit"]["sha"], run_kind))
    if [e["stage"] for e in events] != list(STAGES):
        errors.append("MISSING_OR_OUT_OF_ORDER_STAGES")
    if any(not isinstance(n, str) for n in originals) or set(n for n in originals if isinstance(n, str)) != set(ORIGINAL_STAGES) or len(originals) != 3:
        errors.append("MISSING_OR_DUPLICATE_ORIGINAL")
    reviewer_status = "DEGRADED" if any(e["stage"] == "REVIEWER" and e["status"] == "DEGRADED"
                                         for e in events) else "OBSERVED" if any(
        e["stage"] == "REVIEWER" and e["status"] == "OBSERVED" for e in events) else "NOT_VERIFIED"
    # Never infer a trusted ChatGPT host-call stream from the contents of an uploaded JSON file.
    client_attestation = "SYNTHETIC_ONLY" if run_kind == "SYNTHETIC" else "BLOCKED_HOST_TRACE_API"
    return {"evidence_sequence": "FAIL" if errors else "PASS",
            "client_attestation": client_attestation,
            "live_client_trace": "NOT_VERIFIED" if run_kind == "SYNTHETIC" else "BLOCKED_HOST_TRACE_API",
            "active_mount_version": ("NOT_VERIFIED" if run_kind == "LIVE"
                                     else versions["active_mount"]["version"]),
            "reviewer_status": reviewer_status,
            "errors": list(dict.fromkeys(errors)),
            "scope": "OFFLINE_ASSERTIONS_AND_LOCAL_ARTIFACT_HASHES_ONLY",
            "synthetic": run_kind == "SYNTHETIC"}


def empty_receipt() -> dict:
    """New anonymous task skeleton, not retroactive primary evidence."""
    return {"schema_version": 1, "task_id": "task_" + uuid.uuid4().hex,
            "run_kind": "LIVE", "request_blind": "NOT_VERIFIED",
            "versions": {"toolkit": {"sha": "NOT_VERIFIED", "source": "NOT_VERIFIED"},
                         "plugin_backend": {"version": "NOT_VERIFIED", "source": "NOT_VERIFIED"},
                         "active_mount": {"version": "NOT_VERIFIED", "source": "NOT_VERIFIED"}},
            "events": []}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--receipt", type=Path, help="Read one explicitly supplied receipt")
    group.add_argument("--new", action="store_true", help="Print anonymous empty template without writing")
    parser.add_argument("--artifact-root", type=Path, default=Path.cwd())
    parser.add_argument("--markdown", action="store_true", help="Print sanitized validation summary")
    args = parser.parse_args()
    if args.new:
        print(json.dumps(empty_receipt(), ensure_ascii=False, indent=2))
        return 0
    try:
        if args.receipt.is_symlink() or args.receipt.stat().st_size > 100_000:
            raise ReceiptRejected("UNSAFE_RECEIPT_FILE")
        payload = json.loads(args.receipt.read_text(encoding="utf-8"),
                             object_pairs_hook=_unique_json_object)
        result = validate(payload, args.artifact_root)
    except (ReceiptRejected, OSError, UnicodeError, json.JSONDecodeError, RecursionError):
        # Deliberately do not echo untrusted exception text (could contain a secret/path).
        print("RECEIPT_REJECTED", file=sys.stderr)
        return 2
    if args.markdown:
        print("# Route evidence receipt - sanitized summary\n\n"
              f"- Evidence sequence: {result['evidence_sequence']}\n"
              f"- Live client trace: {result['live_client_trace']}\n"
              f"- Client attestation: {result['client_attestation']}\n"
              f"- Active package: {result['active_mount_version']}\n"
              f"- Findings: {', '.join(result['errors']) or 'none'}")
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["evidence_sequence"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
