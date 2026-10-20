---
name: integration-testing
description: "Verify behavior across real component boundaries including queues, databases and external APIs. Use for multi-service or asynchronous changes."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Integration Testing

1. Enumerate participating components, their ownership and contract; define the minimum realistic integration boundary.
2. Verify handoffs, persisted outcomes, retries, idempotency, partial failures and compensation behavior where applicable.
3. Use controlled fakes only for true external dependencies, document their fidelity and test at least one realistic boundary when feasible.
4. Poll for observable state with a bounded timeout rather than fixed sleeps; include identifiers for correlation.
5. Ensure test data isolation and restore the environment after failures.

Record exactly which dependencies were real, simulated or inaccessible. Do not call a mock-only test end-to-end integration evidence.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
