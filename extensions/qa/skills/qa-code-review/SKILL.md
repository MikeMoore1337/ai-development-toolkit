---
name: qa-code-review
description: "Review the quality of QA automation code, test fixtures and framework boundaries. Use for PRs changing test implementations or CI helpers."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Qa Code Review

Inspect test code as production code: type boundaries, fixture scope, concurrency, cleanup, secrets and performance. Distinguish errors in framework structure from errors in the test oracle (route those to `test-review`). Check imports and dependencies against the actual project's runtime. Prefer constrained changes to test harnesses over new abstractions. For every finding, provide location, failure mechanism and minimal reproducer or evidence. Do not assert that a green job proves the test logic is correct.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
