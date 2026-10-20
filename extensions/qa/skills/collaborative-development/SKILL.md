---
name: collaborative-development
description: "Coordinate parallel human and AI changes to tests and automation without conflicting ownership. Use when tasks share fixtures, branches or test infrastructure."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Collaborative Development

Identify independent work items and declare ownership by file/component; exclude overlapping changes or serialize them. Use separate worktrees where available, and never let one contributor silently update another's branch. Specify test contracts and handoffs ahead of implementation. Reconcile fixtures, schemas and CI edits explicitly before integration. Preserve human review and repository merge policy. Handoff includes changed files, tests run, known conflicts and unverified assumptions.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
