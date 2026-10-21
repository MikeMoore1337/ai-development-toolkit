# Observability & SRE (Issue #63)

[Русская версия](ru/OBSERVABILITY_SRE.md) | [Optional skill](../extensions/operations/skills/observability-sre/SKILL.md)

Observability explains *what was observed and with what quality*, not an AI-generated root-cause story. **Logs** describe single events, **metrics** count or aggregate populations, and **traces** link sampled operations across components. A **correlation ID** is an opaque identifier propagated across one logical operation; timestamps close together are not proof of a link. A partial trace does not prove an operation never happened.

**SLI** is a precisely defined indicator for a user journey. **SLO** is a target agreed with the owner. For a complete event-based window, `good/eligible` is the SLI, and `eligible*(1-objective)-bad` is the remaining **error budget**. An SLO of 99.9% is only an example until approved. Use exact decimal arithmetic, not rounded pass/fail percentages. Healthy charts cannot prove every user journey is restored when sampling, data gaps or independent failures remain.

**Incident timeline** records both event time and observation time with evidence and uncertainty. Correlation does not prove causation. **RCA** tests competing causal hypotheses and uses `UNDETERMINED` when evidence cannot distinguish them. A **postmortem** documents real actions, unresolved questions and measurable prevention tasks; writing it does not resolve those tasks. Verify recovery with complete, representative post-action windows and critical journeys, not just green CI or a successful request.

## Reuse-first decision table

| Capability | Existing coverage | Confirmed gap | Decision |
| --- | --- | --- | --- |
| Failure diagnosis / RCA | failure-triage | Cross-signal temporal incident evidence | REUSE + NEW incident workflow |
| System dependencies | codebase-knowledge-map | Proven span/correlation links | REUSE + NEW contract |
| Structured logs / IDs / tracing | Security privacy guidance | Portable schema and negative oracles | NEW |
| Metrics integrity | performance-load-testing | Quality and freshness classification | REFINE via NEW contract |
| SLI/SLO / error budgets | Performance calculations | User-journey ratio, owner objective, exact budget | NEW |
| Alert / timeline / postmortem | QA evidence and triage | State and evidence-linked history | NEW |
| Rollback / recovery | release-safety / reliability-testing | Operational handoff | REUSE + NEW handoff |
| Production authority | AGENTS.md / release-safety | No bypass permitted | REUSE |

One opt-in `operations` pack and `observability-sre` profile; no collector, server, background daemon, full QA Pack or paid dependency. No external traffic, real monitoring or production action is run.

## Reproducible fictional investigation

From an authorized Toolkit development checkout:

```sh
python scripts/validate_observability.py
python -m unittest tests.test_observability -v
```

The case and intentionally broken variants live under `fixtures/observability/`. Results are `SYNTHETIC_TESTED`, **not** live observability or real AI-client activation. The [telemetry](../extensions/operations/skills/observability-sre/references/TELEMETRY.md), [SLI/SLO](../extensions/operations/skills/observability-sre/references/SLI_SLO.md), [incident](../extensions/operations/skills/observability-sre/references/INCIDENT.md) and [postmortem](../extensions/operations/skills/observability-sre/references/POSTMORTEM.md) contracts guide actual authorized work.

**Beginner prompt:** "My application sometimes stops working. Help identify critical user actions, what failure evidence exists, what to check first, and what remains unknown. Do not touch production."

**Expert prompt:** "Define a portable observability, tracing, event-based SLI/SLO and incident response contract, independently verify error budgets and competing RCA hypotheses, and produce a mitigation-approval and recovery evidence handoff."

User evidence and reports return in chat by default. All Toolkit copies are read-only when referenced from another project. Production access, restarts, configuration, rollback, external telemetry exports and deployment require separately scoped approval. Incomplete evidence must not be promoted to confirmed cause or restored state.
