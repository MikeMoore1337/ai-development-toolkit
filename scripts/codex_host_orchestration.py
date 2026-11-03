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
    native_runtime: str = "V1",
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
    if native_runtime not in ("V1", "V2"):
        raise HostOrchestrationError("UNSUPPORTED_NATIVE_RUNTIME")
    if native_runtime == "V2" and (
            client_snapshot.get("native_runtime") != "V2"
            or client_snapshot.get("native_model_override") != "VERIFIED"):
        raise HostOrchestrationError("V2_MODEL_OVERRIDE_NOT_VERIFIED")
    if native_runtime == "V1":
        spawn = {"model": target_model, "message": context, "fork_context": False}
    else:
        # Opaque, deterministic, privacy-preserving one-shot name. Never echo
        # the raw task ID into native task names or durable records.
        task_name = "adt_review_" + hashlib.sha256(
            request["task_id"].encode("utf-8")).hexdigest()[:16]
        spawn = {"task_name": task_name, "model": target_model,
                 "message": context, "fork_turns": "none"}
    # The fingerprint binds the returned preview to content but is not secret,
    # cannot authenticate the host, and cannot prevent replay.
    plan = {
        "schema_version": 1 if native_runtime == "V1" else 2, "task_id": request["task_id"],
        "inventory_revision": request["inventory_revision"],
        "requested_model": target_model, "primary_model": request["current_model"],
        "mode": approval["authorized_mode"],
        "status": "PREFLIGHT_ONLY_NOT_EXECUTED",
        "native_spawn_tool": ("multi_agent_v1__spawn_agent" if native_runtime == "V1" else "spawn_agent"),
        "native_spawn_arguments": spawn,
        "native_wait_tool": ("multi_agent_v1__wait_agent" if native_runtime == "V1" else "list_agents"),
        "native_wait_timeout_ms": 10000 if native_runtime == "V1" else 300000,
        "expected_extra_calls_after_claim": used + 1,
        "host_atomic_lease_required": True,
        "host_lease_observed": False,
        "host_executed": False,
        "observed_model": "UNKNOWN",
        "billing_attestation": "CALLER_DECLARED_NOT_INDEPENDENTLY_ATTESTED",
    }
    if native_runtime == "V2":
        plan["native_runtime"] = "V2"
    plan["plan_fingerprint"] = _digest(plan)
    return plan


def review(plan: dict, spawn_response: dict, wait_response: dict,
           *, host_claimed_one_shot_lease: bool = False) -> dict:
    """Validate one host-supplied V1/V2 spawn and completion snapshot.

    V2's wait_agent returns mailbox metadata, NOT completion content.
    The host must use native list_agents to provide the task's completed
    agent_status. No caller-supplied response authenticates actual execution.
    """
    base_fields = {
        "schema_version", "task_id", "inventory_revision", "requested_model",
        "primary_model", "mode", "status", "native_spawn_tool",
        "native_spawn_arguments", "native_wait_tool", "native_wait_timeout_ms",
        "expected_extra_calls_after_claim", "host_atomic_lease_required",
        "host_lease_observed", "host_executed", "observed_model",
        "billing_attestation", "plan_fingerprint",
    }
    if not isinstance(plan, dict) or plan.get("schema_version") not in (1, 2):
        raise HostOrchestrationError("INVALID_PREFLIGHT_PLAN")
    v2 = plan["schema_version"] == 2
    if set(plan) != (base_fields | ({"native_runtime"} if v2 else set())):
        raise HostOrchestrationError("INVALID_PREFLIGHT_PLAN")
    original = {k: v for k, v in plan.items() if k != "plan_fingerprint"}
    if not isinstance(plan["plan_fingerprint"], str) or _digest(original) != plan["plan_fingerprint"]:
        raise HostOrchestrationError("PLAN_FINGERPRINT_MISMATCH")

    args = plan["native_spawn_arguments"]
    common_valid = (
        plan["status"] == "PREFLIGHT_ONLY_NOT_EXECUTED"
        and type(plan["native_wait_timeout_ms"]) is int
        and 10000 <= plan["native_wait_timeout_ms"] <= 3600000
        and type(plan["expected_extra_calls_after_claim"]) is int
        and 1 <= plan["expected_extra_calls_after_claim"] <= 10
        and plan["host_atomic_lease_required"] is True
        and plan["host_lease_observed"] is False
        and plan["host_executed"] is False
        and plan["observed_model"] == "UNKNOWN"
        and isinstance(args, dict)
        and args.get("model") == plan["requested_model"]
        and isinstance(args.get("message"), str)
        and bool(args["message"].strip()) and len(args["message"]) <= 16000
    )
    if not common_valid:
        raise HostOrchestrationError("INVALID_NATIVE_PLAN")
    if v2:
        expected = "adt_review_" + hashlib.sha256(
            plan["task_id"].encode("utf-8")).hexdigest()[:16]
        valid = (
            plan["native_runtime"] == "V2"
            and plan["native_spawn_tool"] == "spawn_agent"
            and plan["native_wait_tool"] == "list_agents"
            and plan["native_wait_timeout_ms"] == 300000
            and set(args) == {"model", "message", "task_name", "fork_turns"}
            and args["task_name"] == expected
            and args["fork_turns"] == "none"
        )
    else:
        valid = (
            plan["native_spawn_tool"] == "multi_agent_v1__spawn_agent"
            and plan["native_wait_tool"] == "multi_agent_v1__wait_agent"
            and set(args) == {"model", "message", "fork_context"}
            and args["fork_context"] is False
        )
    if not valid:
        raise HostOrchestrationError("INVALID_NATIVE_PLAN")
    if type(host_claimed_one_shot_lease) is not bool:
        raise HostOrchestrationError("INVALID_LEASE_CLAIM")

    if v2:
        if (not isinstance(spawn_response, dict) or
                set(spawn_response) - {"task_name", "nickname"} or
                "task_name" not in spawn_response):
            raise HostOrchestrationError("INVALID_SPAWN_RESPONSE")
        task_ref = spawn_response["task_name"]
        # Spawn returns a CANONICAL path under the current parent, which
        # may be /root/parent/child rather than /root/child.
        canonical = (isinstance(task_ref, str) and len(task_ref) <= 512
                     and task_ref.startswith("/root/")
                     and task_ref.endswith("/" + expected)
                     and all(segment.isascii() and
                             segment.replace("_", "").isalnum() and
                             segment == segment.lower() and segment
                             for segment in task_ref[6:].split("/")))
        if not (task_ref == expected or canonical):
            raise HostOrchestrationError("MISMATCHED_SPAWN_TASK")
        accepted_refs = ({task_ref} if canonical else {expected, "/root/" + expected})
        if ("nickname" in spawn_response and spawn_response["nickname"] is not None
                and not isinstance(spawn_response["nickname"], str)):
            raise HostOrchestrationError("INVALID_NICKNAME")
        if not isinstance(wait_response, dict) or set(wait_response) != {"agents"}:
            raise HostOrchestrationError("INVALID_AGENT_LIST")
        agents = wait_response["agents"]
        if not isinstance(agents, list) or len(agents) > 64:
            raise HostOrchestrationError("INVALID_AGENT_LIST")
        matching = []
        for entry in agents:
            if (not isinstance(entry, dict) or set(entry) != {"agent_name", "agent_status"}
                    or not isinstance(entry["agent_name"], str)):
                raise HostOrchestrationError("INVALID_AGENT_LIST")
            if entry["agent_name"] in accepted_refs:
                matching.append(entry["agent_status"])
        if len(matching) > 1:
            raise HostOrchestrationError("AMBIGUOUS_AGENT_LIST")
        status = matching[0] if matching else None
        success = (isinstance(status, dict) and set(status) == {"completed"}
                   and isinstance(status["completed"], str)
                   and bool(status["completed"].strip()))
        agent_ref = task_ref
    else:
        if (not isinstance(spawn_response, dict) or
                set(spawn_response) - {"agent_id", "nickname"} or
                "agent_id" not in spawn_response):
            raise HostOrchestrationError("INVALID_SPAWN_RESPONSE")
        agent_ref = _uuid(spawn_response["agent_id"])
        if ("nickname" in spawn_response and spawn_response["nickname"] is not None
                and not isinstance(spawn_response["nickname"], str)):
            raise HostOrchestrationError("INVALID_NICKNAME")
        if not isinstance(wait_response, dict) or set(wait_response) != {"status", "timed_out"}:
            raise HostOrchestrationError("INVALID_WAIT_RESPONSE")
        if type(wait_response["timed_out"]) is not bool:
            raise HostOrchestrationError("INVALID_TIMEOUT_FLAG")
        statuses = wait_response["status"]
        if not isinstance(statuses, dict) or set(statuses) != {agent_ref}:
            raise HostOrchestrationError("MISMATCHED_WAIT_TARGET")
        status = statuses[agent_ref]
        success = (wait_response["timed_out"] is False
                   and isinstance(status, dict) and set(status) == {"completed"}
                   and isinstance(status["completed"], str)
                   and bool(status["completed"].strip()))

    return {
        "status": "HOST_COMPLETED_MODEL_UNVERIFIED" if success else "HOST_RESULT_NOT_CONFIRMED",
        "agent_id": agent_ref, "native_reference_kind": "TASK_NAME" if v2 else "AGENT_UUID",
        "task_id": plan["task_id"], "requested_model": plan["requested_model"],
        "observed_model": "UNKNOWN", "backend_model_attestation": "NOT_VERIFIED",
        "host_execution_evidence": "CALLER_SUPPLIED_NATIVE_RESPONSE_NOT_INDEPENDENTLY_ATTESTED",
        "host_lease_evidence": ("CLAIMED_NOT_ATTESTED" if host_claimed_one_shot_lease
                                else "NOT_OBSERVED"),
        "model_calls_requested": 1, "extra_calls_used": "HOST_MUST_RECONCILE",
        "quality_benefit": "NOT_MEASURED", "quota_cost": "NOT_MEASURED",
        "fallback": "NONE", "retry": "NONE",
    }
