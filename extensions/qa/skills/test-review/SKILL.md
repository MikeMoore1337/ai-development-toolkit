---
name: test-review
description: "Independently assess whether tests can detect regressions and avoid false passes. Use on new or modified tests, especially before merging a risky change."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Test Review

1. Identify the stated requirement separately from the test's implementation.
2. Inspect assertions for a **discriminating oracle**: if the feature were broken, would the test fail? Watch for status-only checks, absent state validation, and assertions of mock behavior rather than system behavior.
3. Verify setup/teardown, data independence, time boundaries, async handling, concurrency and the absence of unconditional skips or swallowed exceptions.
4. Look for brittle selectors, environmental dependencies, over-mocking, broad retry loops, and leaked credentials.
5. Run an intentional negative check or mutation where feasible. If not done, call this review static only.

Output findings with file/line, defect mechanism, realistic counterexample, severity and suggested verification. Distinguish critical semantic gaps from style preferences.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
