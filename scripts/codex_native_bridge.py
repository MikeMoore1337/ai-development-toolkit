#!/usr/bin/env python3
"""Codex native delegate bridge: host-injected callbacks, no Codex CLI or API.

The Toolkit Python process cannot call Codex Desktop session tools directly.
Only a trusted Codex host can provide the actual spawn_agent/wait_agent
callbacks. A native agent ID and completed result do NOT attest its model.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

SOURCE = Path(__file__).with_name("model_switching_adapters.py")


class CodexBridgeError(ValueError):
    """Invalid native host contract; no automatic fallback or retry."""


def _adapter():
    spec = importlib.util.spec_from_file_location("_adt_native_codex_delegate", SOURCE)
    if spec is None or spec.loader is None:
        raise CodexBridgeError("ADAPTER_NOT_FOUND")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _agent_id(value: Any) -> str:
    """Require a canonical agent ID; never accept arbitrary host-output text."""
    if not isinstance(value, str) or len(value) != 36:
        raise CodexBridgeError("INVALID_AGENT_ID")
    try:
        canonical = str(UUID(value))
    except (ValueError, AttributeError) as exc:
        raise CodexBridgeError("INVALID_AGENT_ID") from exc
    if value != canonical:
        raise CodexBridgeError("INVALID_AGENT_ID")
    return value


def codex_delegate(
    request: dict, consent: dict, target_model: str, state: dict,
    *, snapshot: Callable[[], dict],
    spawn_agent: Callable[..., dict], wait_agent: Callable[..., dict],
    context: str, confirmed_for_this_call: bool = False,
) -> dict:
    """Enforce Toolkit consent before attempting one native delegated call.

    The host wraps Codex session tools into the documented normalized shape:
    spawn_agent(model=..., message=..., fork_context=False) ->
        {"agent_id": "<UUID>"}
    wait_agent(agent_id="<UUID>") ->
        {"agent_id": "<same UUID>", "status": "completed", "result": "<text>"}

    No source of the observed backend model is available in this contract.
    Therefore successful completion is HOST_EXECUTED_MODEL_UNVERIFIED.
    Python never discovers, authenticates to or invokes Codex itself.
    """
    if not callable(spawn_agent) or not callable(wait_agent):
        raise CodexBridgeError("NATIVE_HOST_CALLBACKS_MISSING")
    if not isinstance(request, dict) or request.get("delegation") != "VERIFIED":
        raise CodexBridgeError("CODEX_DELEGATION_NOT_VERIFIED")

    observed: dict[str, str] = {}

    def invoke(model: str, minimal_context: str, method: str) -> dict:
        if method != "delegate":
            raise CodexBridgeError("CODEX_NATIVE_SWITCH_UNSUPPORTED")
        response = spawn_agent(model=model, message=minimal_context, fork_context=False)
        if not isinstance(response, dict):
            raise CodexBridgeError("INVALID_NATIVE_SPAWN_RESPONSE")
        agent_id = _agent_id(response.get("agent_id"))
        observed["agent_id"] = agent_id  # preserve an ID even if wait subsequently fails
        completion = wait_agent(agent_id=agent_id)
        if not isinstance(completion, dict):
            raise CodexBridgeError("INVALID_NATIVE_WAIT_RESPONSE")
        if completion.get("agent_id") != agent_id or completion.get("status") != "completed":
            raise CodexBridgeError("NATIVE_COMPLETION_NOT_CONFIRMED")
        if not isinstance(completion.get("result"), str) or not completion["result"].strip():
            raise CodexBridgeError("NATIVE_RESULT_MISSING")
        # Do not parse alleged model names from free-form agent text or labels.
        return {
            "execution": "HOST_COMPLETED_MODEL_UNKNOWN",
            "observed_model": "UNKNOWN",
            "agent_id": agent_id,
        }

    outcome = _adapter().dispatch(
        request, consent, target_model, state,
        snapshot=snapshot, invoke=invoke, context=context,
        confirmed_for_this_call=confirmed_for_this_call,
    )
    if "agent_id" in observed:
        outcome["agent_id"] = observed["agent_id"]
    outcome["backend_model_attestation"] = "NOT_VERIFIED"
    outcome["host_integration"] = "CALLBACK_SUPPLIED_BY_HOST"
    return outcome
