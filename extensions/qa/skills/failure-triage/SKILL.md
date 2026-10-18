---
name: failure-triage
description: "Investigate failed CI jobs or tests and classify failure origin using evidence. Use when tests fail, infra is unstable or release status is ambiguous."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Failure Triage

1. Record exact run, commit, environment, step, test name and first failing observation; never infer status from a partial log.
2. Reconstruct the first causal failure rather than focusing on later cascading errors.
3. Classify as `PRODUCT`, `TEST`, `INFRA`, `ENVIRONMENT`, `EXTERNAL_DEPENDENCY` or `UNKNOWN`; include confidence and supporting evidence.
4. Compare known-good runs and reproducibility. Check config drift, timeouts, state leakage and external service behavior.
5. Propose the smallest falsifiable next check before broad remediation. Retry alone is not a diagnosis.

Report `observed failure | classification | evidence | confidence | next diagnostic | release impact`. Use [triage template](references/TRIAGE.md) for multi-job failures.
