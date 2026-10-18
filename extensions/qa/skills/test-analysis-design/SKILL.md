---
name: test-analysis-design
description: "Design meaningful tests using partitions, boundaries, state transitions and explicit oracles. Use before automating new behavior or evaluating missed cases."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Test Analysis Design

1. Inventory inputs, constraints, authorization roles, state transitions and externally observable effects.
2. Choose a design technique based on behavior: equivalence classes for domains, boundary analysis for thresholds, decision tables for combinations, state diagrams for lifecycles, pairwise where combinations explode.
3. State each **test oracle**: what observable fact distinguishes correct from incorrect behavior; do not accept a successful HTTP response alone when state must change.
4. Cover at least a valid flow, key invalid inputs, idempotency/retry where applicable, race and error/recovery paths proportional to risk.
5. Map each case to requirement and expected evidence; remove redundant tests that add no coverage of distinct risk.

Deliver a small structured case table: `ID | precondition | action | expected result | observable oracle | risk`. Read [test design template](references/TEST_DESIGN.md) for large changes.
