#!/usr/bin/env python3
"""Opt-in host adapter for model handoffs; never discovers or calls a provider itself.

A host supplies verified model inventory and three callbacks. This module
enforces consent on each call, a cap and a safe main-model return contract.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable

POLICY = Path(__file__).with_name("adaptive_execution_advisor.py")

class AdapterError(ValueError):
    """Refused handoff. No model invocation is performed."""

def _advisor():
    spec = importlib.util.spec_from_file_location("_adt_model_consent", POLICY)
    if spec is None or spec.loader is None:
        raise AdapterError("CONSENT_POLICY_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def _state(state: Any, request: dict) -> int:
    if not isinstance(state, dict) or set(state) != {
        "task_id", "inventory_revision", "calls_used", "revoked"
    }:
        raise AdapterError("INVALID_STATE")
    if state["task_id"] != request["task_id"] or state["inventory_revision"] != request["inventory_revision"]:
        raise AdapterError("STALE_STATE")
    if type(state["revoked"]) is not bool or type(state["calls_used"]) is not int or not 0 <= state["calls_used"] <= 10:
        raise AdapterError("INVALID_STATE_VALUES")
    if state["revoked"]:
        raise AdapterError("CONSENT_REVOKED")
    return state["calls_used"]

def _same_capabilities(before: dict, after: Any) -> bool:
    """Compare all safety-critical properties, not just the model name."""
    keys = ("task_id", "current_model", "inventory_revision", "available_models",
            "inventory_status", "switching", "delegation",
            "zero_incremental_cost_verified")
    return isinstance(after, dict) and all(before.get(k) == after.get(k) for k in keys)

def dispatch(
    request: dict, consent: dict, target_model: str, state: dict,
    *, snapshot: Callable[[], dict],
    invoke: Callable[[str, str, str], dict],
    restore: Callable[[str], bool] | None = None,
    context: str = "",
    confirmed_for_this_call: bool = False,
) -> dict:
    """Attempt one handoff, returning an explicit receipt and updated counter.

    The host is responsible for authoritative capability inventory, true user
    consent, allowed context and model execution. This is a policy boundary,
    not authentication or proof of model identity.
    """
    try:
        policy = _advisor()
        approval = policy.authorize(request, consent)
    except (ValueError, OSError) as exc:
        raise AdapterError("CONSENT_DENIED") from exc
    used = _state(state, request)
    if not isinstance(target_model, str) or target_model not in approval["approved_models"]:
        raise AdapterError("TARGET_NOT_APPROVED")
    if used >= approval["max_extra_calls"]:
        raise AdapterError("CALL_LIMIT_EXHAUSTED")
    if not request["zero_incremental_cost_verified"]:
        raise AdapterError("ZERO_INCREMENTAL_COST_NOT_VERIFIED")
    if (approval["authorized_mode"] == "RECOMMEND_WITH_CONFIRMATION"
            and confirmed_for_this_call is not True):
        raise AdapterError("PER_CALL_CONFIRMATION_REQUIRED")
    if type(confirmed_for_this_call) is not bool or not isinstance(context, str) or len(context) > 16000:
        raise AdapterError("INVALID_INVOCATION_ARGUMENTS")
    if not callable(snapshot) or not callable(invoke):
        raise AdapterError("HOST_RUNTIME_NOT_AVAILABLE")
    current = snapshot()
    if not _same_capabilities(request, current) or current.get("inventory_status") != "VERIFIED":
        raise AdapterError("STALE_OR_UNVERIFIED_CLIENT_SNAPSHOT")
    method = ("delegate" if current["delegation"] == "VERIFIED"
              else "switch" if current["switching"] == "VERIFIED" else None)
    if method is None:
        raise AdapterError("HOST_SWITCHING_UNAVAILABLE")
    if method == "switch" and not callable(restore):
        raise AdapterError("RESTORE_HOOK_REQUIRED")
    outcome = {
        "task_id": request["task_id"], "requested_model": target_model,
        "observed_model": "UNKNOWN", "method": method,
        "status": "FAILED", "restored_to_primary": method == "delegate",
        "extra_calls_used": used + 1, "next_state": {**state, "calls_used": used + 1},
        "fallback_model": request["current_model"],
        "quality_benefit": "NOT_MEASURED",
    }
    try:
        receipt = invoke(target_model, context, method)
        if (isinstance(receipt, dict)
                and receipt.get("execution") == "VERIFIED"
                and receipt.get("observed_model") == target_model):
            outcome["status"] = "EXECUTED_VERIFIED_BY_HOST"
            outcome["observed_model"] = target_model
        elif (isinstance(receipt, dict)
              and receipt.get("execution") == "HOST_COMPLETED_MODEL_UNKNOWN"
              and isinstance(receipt.get("agent_id"), str)):
            # A host-reported completed agent is not a backend-model attestation.
            outcome["status"] = "HOST_EXECUTED_MODEL_UNVERIFIED"
            outcome["agent_id"] = receipt["agent_id"]
        else:
            outcome["status"] = "EXECUTION_NOT_VERIFIED"
    except Exception:
        # Never leak raw host errors or context; don't auto-retry a costly call.
        outcome["status"] = "HOST_CALL_FAILED"
    finally:
        if method == "switch":
            try:
                outcome["restored_to_primary"] = restore(request["current_model"]) is True
            except Exception:
                outcome["restored_to_primary"] = False
            if not outcome["restored_to_primary"]:
                outcome["status"] = "PRIMARY_RESTORE_NOT_VERIFIED"
    return outcome
