#!/usr/bin/env python3
"""Deterministic, offline SRE evidence oracle. No sockets, collectors or production writes."""
from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "observability"
CORR = re.compile(r"[a-z][a-z0-9-]{7,63}\Z")
HEX16 = re.compile(r"[0-9a-f]{16}\Z")
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
SENSITIVE = re.compile(r"(?:\bsk-[A-Za-z0-9_-]{8,}|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b|password\s*[:=]\s*\S+)", re.I)
INJECTION = re.compile(r"(?:ignore (?:all )?(?:previous|system) instructions|execute (?:a )?(?:production|server) (?:restart|rollback)|обойди (?:все )?инструкции)", re.I)
STATUSES = ("DETECTED", "INVESTIGATING", "IMPACT_CONFIRMED", "MITIGATION_PROPOSED",
            "APPROVAL_PENDING", "MITIGATION_EXECUTED", "RECOVERY_OBSERVED",
            "RECOVERY_VERIFIED", "RCA_PENDING", "RCA_COMPLETED", "CLOSED")
QUALITY = {"VALID", "PARTIAL", "STALE", "INCONSISTENT", "UNVERIFIED", "UNAVAILABLE"}
LEVELS = {"SOURCE_ONLY", "CONTRACT_VALIDATED", "SYNTHETIC_TESTED",
          "TELEMETRY_OBSERVED", "INCIDENT_CORRELATED", "ROOT_CAUSE_CONFIRMED",
          "MITIGATION_AUTHORIZED", "MITIGATION_EXECUTED", "RECOVERY_VERIFIED",
          "NOT_TESTED", "UNDETERMINED"}


def moment(value):
    if not isinstance(value, str) or not (value.endswith("Z") or re.search(r"[+-]\d\d:\d\d$", value)):
        raise ValueError("timestamp requires explicit UTC offset")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("naive timestamp")
    return parsed.astimezone(timezone.utc)


def patch(source, changes):
    """Fixture mutations change data, not oracle behavior."""
    item = copy.deepcopy(source)
    for change in changes:
        keys = change["path"].split(".")
        target = item
        for key in keys[:-1]:
            target = target[int(key)] if isinstance(target, list) else target[key]
        last = int(keys[-1]) if isinstance(target, list) else keys[-1]
        if change.get("remove"):
            if isinstance(target, list):
                target.pop(last)
            else:
                target.pop(last, None)
        elif change.get("append"):
            target[last].append(change["value"])
        else:
            target[last] = change["value"]
    return item


def inspect(data):
    errors = []
    def bad(code, condition):
        if condition:
            errors.append(code)

    bad("ORIGIN", data.get("origin") != "SYNTHETIC")
    bad("ENVIRONMENT", data.get("environment") != "synthetic")
    bad("SERVICE", data.get("service_id") != "order-api")
    bad("REVISION", data.get("source_revision") != "demo-v2")
    bad("EVIDENCE_LEVEL", data.get("evidence_level") not in LEVELS or
        data.get("evidence_level") in {"TELEMETRY_OBSERVED", "ROOT_CAUSE_CONFIRMED", "RECOVERY_VERIFIED"})
    try:
        begin = moment(data["window"]["start"])
        end = moment(data["window"]["end"])
        observed = moment(data["window"]["observed_at"])
        bad("WINDOW", begin >= end or observed < end)
    except (KeyError, TypeError, ValueError):
        begin = end = observed = None
        errors.append("WINDOW")
    evidence = data.get("evidence", [])
    evidence_by_id = {e.get("id"): e for e in evidence if isinstance(e, dict)}
    bad("EVIDENCE_DUPLICATE", len(evidence) != len(evidence_by_id))
    for e in evidence:
        bad("EVIDENCE_SOURCE", e.get("origin") != "SYNTHETIC" or not e.get("kind"))
    logs = data.get("logs", [])
    ids = []
    for log in logs:
        ids.append(log.get("event_id"))
        for field in ("timestamp", "severity", "service", "component", "environment", "event_name",
                      "operation", "outcome", "source_revision", "message"):
            bad("LOG_SCHEMA", not isinstance(log.get(field), str) or not log.get(field))
        try:
            moment(log.get("timestamp"))
        except (TypeError, ValueError):
            errors.append("LOG_TIME")
        bad("LOG_CONTEXT", log.get("service") != data.get("service_id") or
            log.get("environment") != data.get("environment") or
            log.get("source_revision") != data.get("source_revision"))
        bad("LOG_SEVERITY", log.get("severity") not in {"DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"})
        bad("LOG_CATEGORY", log.get("outcome") == "error" and
            log.get("error_category") not in {"DEPENDENCY", "APPLICATION", "RESOURCE", "CONFIGURATION"})
        bad("LOG_ID", log.get("correlation_id") is not None and
            not CORR.fullmatch(str(log["correlation_id"])))
        raw = json.dumps(log, ensure_ascii=False)
        bad("SENSITIVE_DATA", bool(SENSITIVE.search(raw)))
        bad("UNTRUSTED_LOG_INSTRUCTION", bool(INJECTION.search(log.get("message", ""))))
        bad("LOG_FORMAT", "\n" in log.get("message", "") or len(log.get("message", "")) > 1024)
    bad("LOG_DUPLICATE", len(ids) != len(set(ids)))
    traces = data.get("traces", [])
    spans = {s.get("span_id"): s for s in traces}
    bad("SPAN_DUPLICATE", len(traces) != len(spans))
    for span in traces:
        sid = span.get("span_id")
        parent = span.get("parent_span_id")
        bad("TRACE_ID", not HEX32.fullmatch(str(span.get("trace_id", ""))) or
            not HEX16.fullmatch(str(sid)) or sid == "0" * 16)
        bad("TRACE_CONTEXT", span.get("environment") != data.get("environment") or
            span.get("source_revision") != data.get("source_revision"))
        bad("TRACE_SCHEMA", not span.get("service") or not span.get("operation") or
            span.get("sampling") not in {"sampled", "not_sampled"})
        try:
            start, stop = moment(span["start"]), moment(span["end"])
            bad("TRACE_DURATION", stop < start)
        except (KeyError, TypeError, ValueError):
            errors.append("TRACE_TIME")
            start = stop = None
        if parent is not None:
            bad("TRACE_PARENT", parent not in spans or
                (parent in spans and spans[parent].get("trace_id") != span.get("trace_id")))
            if parent in spans:
                try:
                    p_start, p_end = moment(spans[parent]["start"]), moment(spans[parent]["end"])
                    # Span skew is reported as uncertainty, not an invented inter-service latency.
                    bad("CLOCK_SKEW", start is not None and
                        (start < p_start - timedelta(milliseconds=10) or
                         stop > p_end + timedelta(milliseconds=10)))
                except (ValueError, TypeError, KeyError):
                    errors.append("TRACE_TIME")
        seen = set()
        cur = sid
        while cur in spans and cur not in seen:
            seen.add(cur)
            cur = spans[cur].get("parent_span_id")
        bad("TRACE_CYCLE", cur in seen)
    correlations = data.get("correlations", [])
    events = {x.get("event_id"): x for x in logs}
    for link in correlations:
        linked = [events.get(i) for i in link.get("events", [])]
        bad("CORRELATION_EVIDENCE", len(link.get("events", [])) < 2 or
            any(item is None for item in linked) or link.get("method") != "exact_id" or
            link.get("confidence") != "CONFIRMED" or
            (all(item is not None for item in linked) and
             (any(not item.get("correlation_id") for item in linked) or
              len({item.get("correlation_id") for item in linked}) != 1)))
    metrics = data.get("metrics", [])
    period_seconds = data.get("metric_interval_seconds")
    bad("METRIC_INTERVAL", period_seconds != 60 or len(metrics) != 5)
    samples = []
    total = success = 0
    for sample in metrics:
        try:
            tick = moment(sample["timestamp"])
            samples.append(tick)
        except (TypeError, ValueError, KeyError):
            errors.append("METRIC_TIME")
        n, good = sample.get("eligible"), sample.get("good")
        valid_n = type(n) is int and n >= 0
        valid_g = type(good) is int and valid_n and 0 <= good <= n
        bad("METRIC_COUNTS", not valid_g)
        if valid_g:
            total += n
            success += good
        bad("METRIC_CONTEXT", sample.get("environment") != data.get("environment") or
            sample.get("source_revision") != data.get("source_revision"))
        bad("METRIC_SAMPLING", sample.get("sampling") != "complete")
        bad("METRIC_PRIVACY", bool(SENSITIVE.search(json.dumps(sample))))
    if samples:
        bad("METRIC_GAP", len(samples) != len(set(samples)) or
            any((b - a).total_seconds() != 60 for a, b in zip(samples, samples[1:])))
        if begin and end:
            bad("METRIC_WINDOW", samples[0] != begin or samples[-1] + timedelta(seconds=60) != end)
        if observed:
            bad("METRIC_STALE", observed - max(samples) > timedelta(minutes=2))
    bad("SLI_ZERO_ELIGIBLE", total == 0)
    slo = data.get("slo", {})
    try:
        target = Decimal(str(slo["objective"]))
        bad("SLO_UNAPPROVED", slo.get("approval") != "SYNTHETIC_APPROVED" or not (0 < target < 1))
        bad("SLI_DEFINITION", slo.get("indicator_id") != "order-completion" or
            slo.get("eligible_events") != "all_started_orders" or
            slo.get("good_events") != "committed_orders" or slo.get("excluded") != [])
        bad("SLI_DENOMINATOR", slo.get("eligible_count") != total or
            slo.get("good_count") != success or slo.get("bad_count") != total - success)
        budget = (Decimal(total) * (1 - target))
        bad("ERROR_BUDGET", Decimal(str(slo.get("allowable_bad"))) != budget or
            Decimal(str(slo.get("spent_bad"))) != Decimal(total - success) or
            Decimal(str(slo.get("remaining"))) != budget - Decimal(total - success))
    except (KeyError, InvalidOperation, TypeError, ValueError):
        errors.append("SLO_INVALID")
    alerts = data.get("alerts", [])
    bad("ALERT_NOISE", len({a.get("dedupe_key") for a in alerts}) != len(alerts))
    for alert in alerts:
        bad("ALERT_CONTEXT", alert.get("environment") != data.get("environment") or
            alert.get("component") not in {"web", "worker", "storage", "external"})
        bad("ALERT_EVIDENCE", alert.get("evidence") not in evidence_by_id or
            alert.get("metric_window_complete") is not True)
        try:
            moment(alert["triggered_at"])
        except (KeyError, ValueError, TypeError):
            errors.append("ALERT_TIME")
    timeline = data.get("timeline", [])
    stamps = []
    for event in timeline:
        try:
            stamps.append(moment(event["event_timestamp"]))
            moment(event["observation_timestamp"])
        except (KeyError, ValueError, TypeError):
            errors.append("TIMELINE_TIME")
        bad("TIMELINE_CONTEXT", event.get("environment") != data.get("environment") or
            event.get("evidence") not in evidence_by_id)
        bad("TIMELINE_CLAIM", event.get("interpretation") == "rollback executed" and
            data.get("mitigation", {}).get("kind") != "rollback")
    bad("TIMELINE_ORDER", stamps != sorted(stamps))
    bad("IMPACT_UNKNOWN", data.get("impact", {}).get("status") != "CONFIRMED" or
        data.get("impact", {}).get("evidence") not in evidence_by_id)
    statuses = data.get("statuses", [])
    bad("INCIDENT_STATUS", not statuses or statuses[0] != "DETECTED" or
        any(s not in STATUSES for s in statuses) or
        any(STATUSES.index(b) < STATUSES.index(a) for a, b in zip(statuses, statuses[1:])) or
        ("MITIGATION_EXECUTED" in statuses and "APPROVAL_PENDING" not in statuses))
    mitigation = data.get("mitigation", {})
    bad("MITIGATION_AUTHORITY", mitigation.get("execution") != "SIMULATION_ONLY" or
        mitigation.get("owner_approved") is not True or
        mitigation.get("approval_scope") != "SYNTHETIC_ONLY" or
        mitigation.get("production_executed") is not False or
        mitigation.get("evidence") not in evidence_by_id)
    cause = data.get("root_cause")
    hypotheses = data.get("hypotheses", [])
    confirmed = [h for h in hypotheses if h.get("confidence") == "CONFIRMED"]
    for hypothesis in confirmed:
        kinds = {evidence_by_id[e]["kind"] for e in hypothesis.get("evidence", [])
                 if e in evidence_by_id}
        bad("RCA_UNSUPPORTED", len(kinds & {"config_diff", "replay", "code_analysis", "independent_measurement"}) < 2)
    bad("ROOT_CAUSE_CLAIM", (cause == "UNDETERMINED" and bool(confirmed)) or
        (cause != "UNDETERMINED" and
         not any(h.get("id") == cause and h.get("confidence") == "CONFIRMED" for h in confirmed)))
    recovery = data.get("recovery", {})
    last = metrics[-2:]
    ready = (len(last) == 2 and all(type(s.get("eligible")) is int and
             type(s.get("good")) is int and s["eligible"] > 0 and
             Decimal(s["good"]) / Decimal(s["eligible"]) >= Decimal("0.99") for s in last))
    bad("FALSE_RECOVERY", recovery.get("status") != "RECOVERY_VERIFIED" or
        not ready or recovery.get("evidence") not in evidence_by_id or
        not {"RECOVERY_OBSERVED", "RECOVERY_VERIFIED"}.issubset(statuses))
    postmortem = data.get("postmortem", {})
    required = ("summary", "impact", "detected_at", "recovered_at", "timeline",
                "sources", "confirmed_causes", "uncertainties", "detection",
                "actions_taken", "helped", "hindered", "corrective_actions",
                "owners", "verification", "residual_risks", "open_questions")
    bad("POSTMORTEM_INCOMPLETE", any(not postmortem.get(f) for f in required) or
        any(not x.get("acceptance") for x in postmortem.get("corrective_actions", [])) or
        not postmortem.get("open_questions"))
    bad("POSTMORTEM_CAUSE", cause == "UNDETERMINED" and
        postmortem.get("confirmed_causes") != ["undetermined"])
    try:
        assert all(isinstance(x, str) for x in postmortem.get("sources", []))
        bad("POSTMORTEM_EVIDENCE", any(x not in evidence_by_id for x in postmortem.get("sources", [])))
    except (TypeError, AssertionError):
        errors.append("POSTMORTEM_EVIDENCE")
    bad("REPORT_SENSITIVE", bool(SENSITIVE.search(json.dumps(postmortem, ensure_ascii=False))))
    declared_quality = data.get("data_quality")
    bad("QUALITY_STATUS", declared_quality not in QUALITY)
    # Partial sampled telemetry is not complete, even when the available spans are valid.
    bad("QUALITY_OVERCLAIM", data.get("sampling", {}).get("trace_coverage") == "partial" and declared_quality == "VALID")
    return sorted(set(errors))


def load():
    return json.loads((FIXTURES / "reference.json").read_text(encoding="utf-8"))


def evaluate():
    reference = load()
    issues = inspect(reference)
    uncertain = copy.deepcopy(reference)
    uncertain["root_cause"] = "UNDETERMINED"
    uncertain["hypotheses"][0]["confidence"] = "POSSIBLE"
    uncertain["postmortem"]["confirmed_causes"] = ["undetermined"]
    uncertain["postmortem"]["uncertainties"] = "Independent replay unavailable; root cause is undetermined."
    unknown_issues = inspect(uncertain)
    broken = json.loads((FIXTURES / "broken_cases.json").read_text(encoding="utf-8"))["cases"]
    findings = [(case["id"], inspect(patch(reference, case["changes"]))) for case in broken]
    return {"reference": issues, "undetermined": unknown_issues, "mutants": findings}


def main():
    outcome = evaluate()
    print(json.dumps({"origin": "SYNTHETIC", "reference": "PASS" if not outcome["reference"] else "FAIL",
                      "undetermined": "PASS" if not outcome["undetermined"] else "FAIL",
                      "mutants_rejected": sum(bool(items) for _, items in outcome["mutants"]),
                      "mutants_total": len(outcome["mutants"]),
                      "mutant_violations": {name: codes for name, codes in outcome["mutants"]}},
                     indent=2))
    return int(bool(outcome["reference"] or outcome["undetermined"] or
                    any(not errs for _, errs in outcome["mutants"])))


if __name__ == "__main__":
    raise SystemExit(main())
