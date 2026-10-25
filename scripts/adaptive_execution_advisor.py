#!/usr/bin/env python3
"""Portable, offline model advice and explicit per-task consent policy.

This module cannot inspect a live client, change models or launch agents.
Callers must supply capabilities; recommendations are not execution proof.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

MODES = ("SINGLE_MODEL", "RECOMMEND_WITH_CONFIRMATION", "AUTO_OPT_IN")
STATES = frozenset(("VERIFIED", "UNKNOWN", "UNAVAILABLE"))
SIGNALS = frozenset(("routine", "architecture", "security", "design", "ambiguous", "repeated_failure"))
WORDS = {
    "en": {
        "SINGLE_MODEL": ("No extra model or handoff; predictable limits.",
                         "Complex work may need more iterations or independent review."),
        "RECOMMEND_WITH_CONFIRMATION": ("Review a suitable model for each difficult step and keep control.",
                                        "Handoffs consume context, time and limits; quality is not guaranteed."),
        "AUTO_OPT_IN": ("Approved consultation can reduce manual coordination.",
                        "Extra calls consume quotas, increase latency and transmit task context; quality is not guaranteed."),
    },
    "ru": {
        "SINGLE_MODEL": ("Без дополнительных моделей и передач контекста, предсказуемые лимиты.",
                         "Сложная работа может потребовать больше итераций и отдельной проверки."),
        "RECOMMEND_WITH_CONFIRMATION": ("Выбор модели для сложного этапа с подтверждением каждого обращения.",
                                        "Передача контекста тратит время и лимиты; улучшение качества не гарантировано."),
        "AUTO_OPT_IN": ("Согласованные консультации выполняются без ручного переключения.",
                        "Дополнительные обращения расходуют лимиты, время и передают контекст; улучшение не гарантировано."),
    },
}

class AdvisorError(ValueError):
    """Invalid configuration or unverified authorization."""

def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 200:
        raise AdvisorError("INVALID_" + field.upper())
    return value

def _request(raw: Any) -> dict:
    if not isinstance(raw, dict) or set(raw) != {
        "task_id", "locale", "current_model", "available_models", "inventory_status",
        "inventory_revision", "switching", "delegation", "zero_incremental_cost_verified",
        "signals",
    }:
        raise AdvisorError("INVALID_REQUEST_FIELDS")
    task_id = _text(raw["task_id"], "task_id")
    locale = raw["locale"]
    if not isinstance(locale, str) or locale not in WORDS:
        raise AdvisorError("INVALID_LOCALE")
    current = _text(raw["current_model"], "current_model")
    inventory = raw["available_models"]
    if (not isinstance(inventory, list) or len(inventory) > 50
            or any(not isinstance(m, str) or not 1 <= len(m) <= 200 for m in inventory)
            or len(set(inventory)) != len(inventory)):
        raise AdvisorError("INVALID_MODEL_INVENTORY")
    for field in ("inventory_status", "switching", "delegation"):
        if not isinstance(raw[field], str) or raw[field] not in STATES:
            raise AdvisorError("INVALID_" + field.upper())
    revision = _text(raw["inventory_revision"], "inventory_revision")
    if type(raw["zero_incremental_cost_verified"]) is not bool:
        raise AdvisorError("INVALID_COST_EVIDENCE")
    signals = raw["signals"]
    if (not isinstance(signals, list) or
            any(not isinstance(s, str) or s not in SIGNALS for s in signals)
            or len(set(signals)) != len(signals)):
        raise AdvisorError("INVALID_SIGNALS")
    if raw["inventory_status"] == "VERIFIED" and current not in inventory:
        raise AdvisorError("CURRENT_MODEL_MISSING_FROM_VERIFIED_INVENTORY")
    return {**raw, "task_id": task_id, "inventory_revision": revision}

def advise(request: Any) -> dict:
    """Offer explained modes; never silently authorize an extra model call."""
    r = _request(request)
    supported = r["switching"] == "VERIFIED" or r["delegation"] == "VERIFIED"
    alternatives = r["inventory_status"] == "VERIFIED" and any(
        m != r["current_model"] for m in r["available_models"])
    auto_ready = supported and alternatives and r["zero_incremental_cost_verified"]
    demanding = bool(set(r["signals"]) & {"architecture", "security", "design",
                                         "ambiguous", "repeated_failure"})
    recommended = "RECOMMEND_WITH_CONFIRMATION" if demanding and alternatives else "SINGLE_MODEL"
    options = []
    for mode in MODES:
        benefit, risk = WORDS[r["locale"]][mode]
        enabled = (mode == "SINGLE_MODEL"
                   or mode == "RECOMMEND_WITH_CONFIRMATION" and alternatives
                   or mode == "AUTO_OPT_IN" and auto_ready)
        blockers = []
        if mode != "SINGLE_MODEL" and not alternatives:
            blockers.append("VERIFIED_ALTERNATIVE_NOT_AVAILABLE")
        if mode == "AUTO_OPT_IN":
            if not supported:
                blockers.append("CLIENT_EXECUTION_NOT_VERIFIED")
            if not r["zero_incremental_cost_verified"]:
                blockers.append("ZERO_INCREMENTAL_COST_NOT_VERIFIED")
        options.append({"mode": mode, "enabled": enabled, "benefit": benefit,
                        "risk": risk, "blockers": blockers})
    return {
        "schema_version": 1, "task_id": r["task_id"],
        "inventory_revision": r["inventory_revision"],
        "current_model": r["current_model"],
        "candidate_models": ([m for m in r["available_models"] if m != r["current_model"]]
                             if alternatives else []),
        "recommended_mode": recommended, "options": options,
        "user_selection_required": True, "selected_mode": None,
        "execution": "NOT_RUN", "extra_model_calls": 0,
        "quality_benefit": "NOT_MEASURED", "quota_remaining": "UNKNOWN",
        "evidence": "CALLER_DECLARED_CAPABILITY_NOT_INDEPENDENTLY_VERIFIED",
    }

def authorize(request: Any, consent: Any) -> dict:
    """Validate one task/revision/mode, without executing a model call."""
    r = _request(request)
    if not isinstance(consent, dict) or set(consent) != {
        "task_id", "inventory_revision", "mode", "approved_models", "max_extra_calls",
    }:
        raise AdvisorError("INVALID_CONSENT_FIELDS")
    if (consent["task_id"] != r["task_id"]
            or consent["inventory_revision"] != r["inventory_revision"]):
        raise AdvisorError("STALE_OR_CROSS_TASK_CONSENT")
    mode = consent["mode"]
    if not isinstance(mode, str) or mode not in MODES:
        raise AdvisorError("INVALID_MODE")
    models = consent["approved_models"]
    if (not isinstance(models, list) or len(models) > 50
            or any(not isinstance(m, str) for m in models)
            or len(models) != len(set(models))):
        raise AdvisorError("INVALID_APPROVED_MODELS")
    cap = consent["max_extra_calls"]
    if type(cap) is not int or not 0 <= cap <= 10:
        raise AdvisorError("INVALID_EXTRA_CALL_CAP")
    if mode == "SINGLE_MODEL":
        if models or cap:
            raise AdvisorError("SINGLE_MODEL_MUST_NOT_DELEGATE")
        return {"authorized_mode": mode, "approved_models": [], "max_extra_calls": 0,
                "extra_calls_authorized": False, "execution": "NOT_RUN",
                "task_id": r["task_id"]}
    if (not models or cap < 1 or r["inventory_status"] != "VERIFIED"
            or any(m == r["current_model"] or m not in r["available_models"] for m in models)):
        raise AdvisorError("UNVERIFIED_OR_EMPTY_MODEL_SELECTION")
    if mode == "AUTO_OPT_IN" and (
            r["switching"] != "VERIFIED" and r["delegation"] != "VERIFIED"
            or not r["zero_incremental_cost_verified"]):
        raise AdvisorError("AUTO_CAPABILITY_OR_COST_UNVERIFIED")
    return {"authorized_mode": mode, "approved_models": models,
            "max_extra_calls": cap, "extra_calls_authorized": mode == "AUTO_OPT_IN",
            "execution": "NOT_RUN", "task_id": r["task_id"]}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--consent", type=Path)
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
        result = (authorize(request, json.loads(args.consent.read_text(encoding="utf-8")))
                  if args.consent else advise(request))
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "INVALID_REQUEST", "reason": str(exc)}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
