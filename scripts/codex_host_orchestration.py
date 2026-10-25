#!/usr/bin/env python3
"""Read-only Codex Desktop native-tool orchestration contract (#357).

The Toolkit MCP stdio process cannot access session-local native tools.
This module validates a *preview* and normalizes separately supplied native
results. Nothing here executes a model, reserves a call or proves model identity.
An authorized host must hold an exclusive, durable, one-shot lease before spawn.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any
from uuid import UUID

BASE = Path(__file__).with_name("model_switching_adapters.py")


class HostOrchestrationError(ValueError):
    """Refusal of invalid or unverifiable delegation evidence."""


def _adapter():
    spec = importlib.util.spec_from_file_location("_adt_codex_host_contract", BASE)
    if spec is None or spec.loader is None:
        raise HostOrchestrationError("POLICY_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _uuid(raw: Any) -> str:
    if not isinstance(raw, str) or len(raw) != 36:
        raise HostOrchestrationError("INVALID_AGENT_ID")
    try:
        canonical = str(UUID(raw))
    except (TypeError, ValueError, AttributeError) as exc:
        raise HostOrchestrationError("INVALID_AGENT_ID") from exc
    if raw != canonical:
        raise HostOrchestrationError("INVALID_AGENT_ID")
    return raw


def _digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                     separators=(",", ":"), ensure_ascii=False,
                                     allow_nan=False).encode("utf-8")).hexdigest()


def prepare(
    request: dict, consent: dict, target_model: str, state: dict,
    client_snapshot: dict, context: str, *, confirmed_for_this_call: bool,
) -> dict:
    """Fail-closed *advice*, not an executable permission or atomic lease.

    A trusted host must verify actual entitlement, included-cost route, and
    exclusive reservation. Merely supplying VERIFIED fields proves none of them.
    """
    adapter = _adapter()
    policy = adapter._advisor()
    try:
        approval = policy.authorize(request, consent)
        used = adapter._state(state, request)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        raise HostOrchestrationError("CONSENT_OR_STATE_DENIED") from exc
    if not isinstance(target_model, str) or target_model not in approval["approved_models"]:
        raise HostOrchestrationError("TARGET_NOT_APPROVED")
    if used >= approval["max_extra_calls"]:
        raise HostOrchestrationError("CALL_LIMIT_EXHAUSTED")
    if not request["zero_incremental_cost_verified"]:
        raise HostOrchestrationError("ZERO_INCREMENTAL_COST_NOT_VERIFIED")
    if (approval["authorized_mode"] == "RECOMMEND_WITH_CONFIRMATION"
            and confirmed_for_this_call is not True):
        raise HostOrchestrationError("PER_CALL_CONFIRMATION_REQUIRED")
    if type(confirmed_for_this_call) is not bool or not isinstance(context, str) or not context.strip() or len(context) > 16000:
        raise HostOrchestrationError("INVALID_CONTEXT_OR_CONFIRMATION")
    if request["delegation"] != "VERIFIED":
        raise HostOrchestrationError("NATIVE_DELEGATION_NOT_VERIFIED")
    if (not adapter._same_capabilities(request, client_snapshot)
            or client_snapshot.get("inventory_status") != "VERIFIED"
            or client_snapshot.get("delegation") != "VERIFIED"):
        raise HostOrchestrationError("STALE_OR_UNVERIFIED_SNAPSHOT")
    spawn = {
        "model": target_model,
        "message": context,
        "fork_context": False,
    }
    # The fingerprint binds the returned preview to content but is not secret,
    # cannot authenticate the host, and cannot prevent replay.
    plan = {
        "schema_version": 1, "task_id": request["task_id"],
        "inventory_revision": request["inventory_revision"],
        "requested_model": target_model, "primary_model": request["current_model"],
        "mode": approval["authorized_mode"],
        "status": "PREFLIGHT_ONLY_NOT_EXECUTED",
        "native_spawn_tool": "multi_agent_v1__spawn_agent",
        "native_spawn_arguments": spawn,
        "native_wait_tool": "multi_agent_v1__wait_agent",
        "native_wait_timeout_ms": 10000,
        "expected_extra_calls_after_claim": used + 1,
        "host_atomic_lease_required": True,
        "host_lease_observed": False,
        "host_executed": False,
        "observed_model": "UNKNOWN",
        "billing_attestation": "CALLER_DECLARED_NOT_INDEPENDENTLY_ATTESTED",
    }
    plan["plan_fingerprint"] = _digest(plan)
    return plan


def review(plan: dict, spawn_response: dict, wait_response: dict,
           *, host_claimed_one_shot_lease: bool = False) -> dict:
    """Interpret one supplied host spawn and wait response, no native calls.

    A host claiming a one-shot lease is NOT proof of atomicity. Callers must
    never pass this result off as independent telemetry.
    """
    if not isinstance(plan, dict) or set(plan) != {
        "schema_version", "task_id", "inventory_revision", "requested_model",
        "primary_model", "mode", "status", "native_spawn_tool",
        "native_spawn_arguments", "native_wait_tool", "native_wait_timeout_ms",
        "expected_extra_calls_after_claim", "host_atomic_lease_required",
        "host_lease_observed", "host_executed", "observed_model",
        "billing_attestation", "plan_fingerprint",
    }:
        raise HostOrchestrationError("INVALID_PREFLIGHT_PLAN")
    original = {k: v for k, v in plan.items() if k != "plan_fingerprint"}
    if not isinstance(plan["plan_fingerprint"], str) or _digest(original) != plan["plan_fingerprint"]:
        raise HostOrchestrationError("PLAN_FINGERPRINT_MISMATCH")
    spawn_args = plan["native_spawn_arguments"]
    if (plan["schema_version"] != 1 or plan["status"] != "PREFLIGHT_ONLY_NOT_EXECUTED"
            or plan["native_spawn_tool"] != "multi_agent_v1__spawn_agent"
            or plan["native_wait_tool"] != "multi_agent_v1__wait_agent"
            or type(plan["native_wait_timeout_ms"]) is not int
            or not 10000 <= plan["native_wait_timeout_ms"] <= 3600000
            or type(plan["expected_extra_calls_after_claim"]) is not int
            or not 1 <= plan["expected_extra_calls_after_claim"] <= 10
            or plan["host_atomic_lease_required"] is not True
            or plan["host_lease_observed"] is not False
            or plan["host_executed"] is not False
            or plan["observed_model"] != "UNKNOWN"
            or not isinstance(spawn_args, dict)
            or set(spawn_args) != {"model", "message", "fork_context"}
            or spawn_args["model"] != plan["requested_model"]
            or spawn_args["fork_context"] is not False
            or not isinstance(spawn_args["message"], str)
            or not spawn_args["message"].strip()
            or len(spawn_args["message"]) > 16000):
        raise HostOrchestrationError("INVALID_NATIVE_PLAN")
    if type(host_claimed_one_shot_lease) is not bool:
        raise HostOrchestrationError("INVALID_LEASE_CLAIM")
    if not isinstance(spawn_response, dict) or set(spawn_response) - {"agent_id", "nickname"} or "agent_id" not in spawn_response:
        raise HostOrchestrationError("INVALID_SPAWN_RESPONSE")
    agent_id = _uuid(spawn_response["agent_id"])
    if ("nickname" in spawn_response and spawn_response["nickname"] is not None
            and not isinstance(spawn_response["nickname"], str)):
        raise HostOrchestrationError("INVALID_NICKNAME")
    if not isinstance(wait_response, dict) or set(wait_response) != {"status", "timed_out"}:
        raise HostOrchestrationError("INVALID_WAIT_RESPONSE")
    if type(wait_response["timed_out"]) is not bool:
        raise HostOrchestrationError("INVALID_TIMEOUT_FLAG")
    statuses = wait_response["status"]
    if not isinstance(statuses, dict) or set(statuses) != {agent_id}:
        raise HostOrchestrationError("MISMATCHED_WAIT_TARGET")
    entry = statuses[agent_id]
    success = (wait_response["timed_out"] is False and
               isinstance(entry, dict) and set(entry) == {"completed"} and
               isinstance(entry["completed"], str) and bool(entry["completed"].strip()))
    return {
        "status": "HOST_COMPLETED_MODEL_UNVERIFIED" if success else "HOST_RESULT_NOT_CONFIRMED",
        "agent_id": agent_id, "task_id": plan["task_id"],
        "requested_model": plan["requested_model"],
        "observed_model": "UNKNOWN",
        "backend_model_attestation": "NOT_VERIFIED",
        "host_execution_evidence": "CALLER_SUPPLIED_NATIVE_RESPONSE_NOT_INDEPENDENTLY_ATTESTED",
        "host_lease_evidence": ("CLAIMED_NOT_ATTESTED" if host_claimed_one_shot_lease
                                else "NOT_OBSERVED"),
        "model_calls_requested": 1,
        "extra_calls_used": "HOST_MUST_RECONCILE",
        "quality_benefit": "NOT_MEASURED",
        "quota_cost": "NOT_MEASURED",
        "fallback": "NONE",
        "retry": "NONE",
    }
