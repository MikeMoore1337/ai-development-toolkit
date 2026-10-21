---
name: observability-sre
description: "Investigate service incidents using structured logs, metrics, traces, evidence-linked timelines, SLI/SLO and recovery checks. Use for observability reviews, incident response and postmortems; not for isolated CI failures, load tests, infrastructure changes or deployment."
metadata:
  pack: "operations"
  version: "1.0.0"
---

# Observability & SRE

Use for "Investigate a service incident", "Correlate logs and traces", "Review telemetry quality", "Define SLI/SLO", "Calculate an error budget", "Prepare a postmortem", "Помоги разобраться с инцидентом", "Проверь наблюдаемость приложения". Start by identifying a critical user journey and the evidence actually available.

Do **not** activate for a single failed CI job (use `failure-triage`), load benchmark (`performance-load-testing`), repeated-event state invariant (`reliability-testing`), container/IaC setup (`devops-infrastructure`), security audit (`security-engineering`), production deployment (`release-safety`), an isolated unit test or interface design. This skill is **not** a controller or a live monitoring agent.

1. **Scope and authority.** Record system, user journey, service/component, environment, source revision, time window, clock uncertainty, existing telemetry and permitted access. Toolkit sources stay read-only in other projects. Without an authorized live source, report `NOT_TESTED` / `UNAVAILABLE`, never claim live observations.
2. **Assess evidence before diagnosis.** Read [telemetry contracts](references/TELEMETRY.md): logs are events, metrics are aggregates, traces are sampled relationships. Check completeness, sampling, freshness, privacy, schema, environment and source. Report `VALID`, `PARTIAL`, `STALE`, `INCONSISTENT`, `UNVERIFIED` or `UNAVAILABLE`, with scope-specific rationale.
3. **Correlate conservatively.** Match exact, validated correlation/trace context and parent-child spans, not timestamp proximity. Never infer absence of an operation from a missing sampled span. Flag clock skew, duplicate IDs, missing parents and parallel spans. See [correlation and tracing](references/TELEMETRY.md).
4. **Quantify impact.** Define eligible and good operations, exclusions and window **before** evaluating [SLI, SLO and budgets](references/SLI_SLO.md). Do not invent SLO targets, user counts, or completeness. Evaluate alert quality, deduplication, user impact and an evidence-linked incident timeline using [incident contract](references/INCIDENT.md).
5. **Investigate.** Separate observations from hypotheses and prove competing explanations with independent sources or reproducible authorized checks. Hand narrow diagnostic reproduction and origin classification to `failure-triage`. Use `codebase-knowledge-map` for verified dependency edges. Record trigger, contributing factors, root cause, detection gap and recovery limitation separately. Unsupported cause: `UNDETERMINED`.
6. **Propose mitigation, not execution.** Compare risk, reversibility, data loss, cost and expected effect; route deployment/rollback decisions through `release-safety`, security findings through `security-boundaries` or `security-engineering`, and state safety through `reliability-testing`. Production restart, configuration, service stop, DNS, firewall, rollback, migrations and any other infrastructure mutation require explicit environment- and action-scoped owner permission. A proposal, approval and actually verified action are distinct.
7. **Verify and hand off.** Use independent, complete post-action recovery windows and affected user journeys; green metrics alone are insufficient. Record actual versus unperformed actions, evidence stage, unknowns and [postmortem with regression tasks](references/POSTMORTEM.md). Stop before any unauthorized action.

**Output:** scoped observation contract; telemetry quality and limitations; SLI/SLO calculation when approved; alert and timeline; hypotheses plus falsifiers; action/approval/evidence status; verification; RCA confidence; postmortem and testable prevention. Never turn synthetic `SYNTHETIC_TESTED` into live `RECOVERY_VERIFIED`.

**Offline example:** `python scripts/validate_observability.py` and `python -m unittest tests.test_observability -v` in an authorized Toolkit checkout. These are deterministic standard-library fixtures, not production monitoring or live AI skill-activation trials. [Fictional incident walkthrough](references/SYNTHETIC_INCIDENT.md).
