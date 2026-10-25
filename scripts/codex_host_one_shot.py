#!/usr/bin/env python3
"""Opt-in durable one-shot reservation for host-owned Codex delegation (#357).

Not an MCP tool. An authorized Codex Desktop host may invoke this local Python
module to prevent two concurrent native spawn attempts for the same task.
No Codex CLI, provider API, native tool, or model execution is performed here.
The *host*, not this ledger, must authenticate subscription/billing provenance,
obtain per-call consent, enforce the native one-spawn/one-wait rule, and supply
a fresh capability snapshot. On uncertain cost, prepare() refuses the request.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any

CONTRACT_PATH = Path(__file__).with_name("codex_host_orchestration.py")
MAX_INPUT_BYTES = 96000


class LeaseDenied(ValueError):
    """Reservation refused without any native tool invocation."""


def _contract():
    spec = importlib.util.spec_from_file_location("_adt_357_host_contract", CONTRACT_PATH)
    if spec is None or spec.loader is None:
        raise LeaseDenied("HOST_CONTRACT_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _key(task_id: str) -> str:
    if not isinstance(task_id, str) or not 1 <= len(task_id) <= 200:
        raise LeaseDenied("INVALID_TASK_ID")
    return hashlib.sha256(task_id.encode("utf-8")).hexdigest()


def _safe_directory(root: str) -> Path:
    if not isinstance(root, str) or not root or len(root) > 4096:
        raise LeaseDenied("INVALID_LEDGER_ROOT")
    original = Path(root).expanduser()
    if not original.is_absolute():
        raise LeaseDenied("LEDGER_REQUIRES_ABSOLUTE_PATH")
    # Reject symlinks and Windows junctions, including ancestor paths.
    for path in (original, *original.parents):
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise LeaseDenied("LINKED_LEDGER_ROOT_REFUSED")
    try:
        info = original.stat()
    except (FileNotFoundError, OSError) as exc:
        raise LeaseDenied("LEDGER_ROOT_NOT_PREPARED") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise LeaseDenied("LEDGER_NOT_A_DIRECTORY")
    if os.name != "nt" and info.st_mode & 0o077:
        raise LeaseDenied("LEDGER_DIRECTORY_NOT_PRIVATE")
    return original


def _read_record(path: Path) -> dict[str, Any]:
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        raise LeaseDenied("LINKED_LEDGER_RECORD_REFUSED")
    try:
        data = path.read_bytes()
        if len(data) > 4096:
            raise LeaseDenied("LEDGER_RECORD_TOO_LARGE")
        value = json.loads(data)
    except (OSError, ValueError) as exc:
        raise LeaseDenied("LEDGER_RECORD_NOT_READABLE") from exc
    if not isinstance(value, dict):
        raise LeaseDenied("INVALID_LEDGER_RECORD")
    return value


def _write_once(path: Path, data: dict) -> None:
    payload = (json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise LeaseDenied("TASK_ALREADY_RESERVED_OR_RECORDED") from exc
    # Never delete a partially written reservation: a crash fails closed,
    # so an interrupted process cannot quietly create a second paid call.
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    except OSError as exc:
        raise LeaseDenied("LEDGER_WRITE_UNCERTAIN_STOP_NO_RETRY") from exc


def claim(
    root: str, plan: dict, request: dict, consent: dict, state: dict,
    client_snapshot: dict, context: str, *,
    confirmed_for_this_call: bool = False,
) -> dict[str, Any]:
    """Atomically consume one task ID in host storage, before native spawn.

    The local checks validate *supplied* state, not an authenticated host.
    The operator must not treat the outcome as proof of consent or free billing.
    """
    ledger = _safe_directory(root)
    contract = _contract()
    if not isinstance(plan, dict):
        raise LeaseDenied("INVALID_PREFLIGHT_PLAN")
    # Re-run current policy rather than trusting the caller-supplied fingerprint
    # (SHA256 is not signed and permits arbitrary caller fabrication).
    validated = contract.prepare(
        request, consent, plan.get("requested_model"), state,
        client_snapshot, context,
        confirmed_for_this_call=confirmed_for_this_call,
    )
    if validated != plan:
        raise LeaseDenied("PLAN_DOES_NOT_MATCH_CURRENT_PREFLIGHT")
    if plan["expected_extra_calls_after_claim"] != 1:
        # This single-shot host shim intentionally allows only one extra call
        # per task. More complex quotas require a separate authorized host.
        raise LeaseDenied("ONLY_ONE_CALL_PER_TASK_SUPPORTED")
    key = _key(plan["task_id"])
    file = ledger / (key + ".claim.json")
    # Nothing identifying the raw task, user prompt, model name or context is
    # persisted; the task id is represented by its SHA256 fingerprint.
    record = {
        "schema": 1,
        "task_key_sha256": key,
        "plan_fingerprint": plan["plan_fingerprint"],
        "inventory_revision_sha256": hashlib.sha256(
            plan["inventory_revision"].encode("utf-8")).hexdigest(),
        "attempts_reserved": 1,
        "lifecycle": "RESERVED_SPEND_UNKNOWN",
        "host_cost_attestation": "NOT_OBSERVED_BY_LEDGER",
        "host_model_attestation": "NOT_OBSERVED_BY_LEDGER",
    }
    _write_once(file, record)
    return {
        "status": "HOST_ONE_SHOT_RESERVED",
        "task_key_sha256": key,
        "plan_fingerprint": plan["plan_fingerprint"],
        "attempts_reserved": 1,
        "native_calls_executed": 0,
        "host_billing_provenance": "NOT_ATTESTED",
        "backend_model": "UNKNOWN",
    }


def inspect(root: str, task_id: str) -> dict[str, Any]:
    """Read-only report; never releases, retries or resets a reservation."""
    ledger = _safe_directory(root)
    key = _key(task_id)
    record = _read_record(ledger / (key + ".claim.json"))
    if record.get("schema") != 1 or record.get("task_key_sha256") != key:
        raise LeaseDenied("INVALID_LEDGER_RECORD")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Codex host one-shot claim (no native invocation)")
    parser.add_argument("action", choices=("claim", "inspect"))
    parser.add_argument("--root", required=True, help="Prepared absolute private ledger folder")
    parser.add_argument("--task-id", help="Required for inspect only")
    args = parser.parse_args(argv)
    try:
        if args.action == "inspect":
            if not args.task_id:
                raise LeaseDenied("TASK_ID_REQUIRED")
            response = inspect(args.root, args.task_id)
        else:
            if args.task_id:
                raise LeaseDenied("TASK_ID_NOT_ACCEPTED_WITH_CLAIM")
            # Bounded stdin JSON avoids shell-escaping sensitive context.
            payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
            if len(payload) > MAX_INPUT_BYTES:
                raise LeaseDenied("REQUEST_TOO_LARGE")
            params = json.loads(payload)
            if not isinstance(params, dict) or set(params) != {
                "plan", "request", "consent", "state", "client_snapshot",
                "context", "confirmed_for_this_call",
            }:
                raise LeaseDenied("INVALID_CLAIM_REQUEST")
            response = claim(args.root, params["plan"], params["request"],
                             params["consent"], params["state"],
                             params["client_snapshot"], params["context"],
                             confirmed_for_this_call=params["confirmed_for_this_call"])
    except (LeaseDenied, ValueError, TypeError, OSError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)[:120]}))
        return 2
    print(json.dumps(response, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
