# Fictional incident walkthrough: SYN-63-001

**SYNTHETIC_TESTED only.** This is not a report about real users, servers or monitoring.

An invented order API (web, background worker, storage and a simulated external dependency) changes configuration from worker concurrency 4 to 1 while switching from fictional demo-v1 to demo-v2. The synthetic baseline is complete, with 100 eligible orders per minute and 100 successfully committed. In the simulated incident five intervals contain 500 eligible orders, 488 good, 12 errors. A sampled API trace has worker and storage spans; at least one other request is untraced by design (sampling PARTIAL). One external dependency timeout is recorded but **not** asserted causal. A deduplicated alert notes missing successful completions.

Competing explanations:
- H-CONFIG: concurrency restriction created backlog. **CONFIRMED IN THE MODEL** by independent synthetic configuration diff and deterministic replay, not solely by deployment proximity.
- H-EXTERNAL: external timeout caused all failed requests. **POSSIBLE**, insufficient evidence to assert as cause.

Timeline records configuration change, observed slow worker, synthetic impact, **simulated-only** configuration restoration after synthetic-only scoped approval, and two full normal intervals. SLI 97.6% fails synthetic 99% target, budget spent 12 against allowed 5. Model recovery oracle accepts the two completed 100/100 windows. It **does not** certify real recovery.

Alternate scenario: without the independent replay, H-CONFIG remains POSSIBLE, H-EXTERNAL remains POSSIBLE, and `ROOT_CAUSE=UNDETERMINED`. A plausible deployment hypothesis is not evidence. Corrective actions: reject unsafe synthetic concurrency settings and report missing trace coverage explicitly.

Run `python scripts/validate_observability.py` for an offline reference, unknown-cause variant and adversarial mutations. The same validator checks reference and broken inputs, covering correlations, span graph, clock skew, secret/PII injection, missing metrics, SLO arithmetic, approval, recovery and postmortem. The oracle deliberately does **not** open sockets, execute mitigation or operate a telemetry backend.
