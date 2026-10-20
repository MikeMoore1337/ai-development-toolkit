---
name: qa-safe-change
description: "Plan a safe, minimal QA automation change from request through verifiable handoff. Use when modifying shared test infrastructure or many test modules."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Qa Safe Change

Record change intent and actual acceptance criteria. Inspect project policy, dependencies, existing patterns and current failing/green baseline. Map blast radius, implement smallest reversible change, update affected tests and run them. Review the assertion semantics, not only test status, and examine CI evidence. Mark proposed vs executed steps separately. Do not merge, deploy or change production credentials unless an explicit project policy and owner approval allow it. Integrate with the core minimal-safe-change skill without duplicating its entire workflow.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
