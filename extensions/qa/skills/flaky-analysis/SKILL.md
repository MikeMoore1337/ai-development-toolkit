---
name: flaky-analysis
description: "Determine why a test is nondeterministic and remove the mechanism. Use for intermittent failures, retries and timing-sensitive checks."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Flaky Analysis

1. Establish intermittency on the same code/configuration where possible; keep count of passing and failing repeats.
2. Compare timestamps, parallel workers, fixtures, ordering, external dependencies, browser traces and resource constraints.
3. Test competing hypotheses: unawaited work, leaked state, shared data, clock assumptions, races, unstable selectors or infrastructure.
4. Replace sleeps with observable readiness conditions and hard failure deadlines. Avoid enlarging timeouts without mechanism-based justification.
5. If quarantine is necessary, scope it, add expiry/owner and preserve visibility in CI.

Include confidence and repeatability evidence. Do not label something flaky merely because a rerun passed.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
