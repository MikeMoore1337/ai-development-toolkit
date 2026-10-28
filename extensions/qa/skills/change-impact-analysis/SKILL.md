---
name: change-impact-analysis
description: "Map a change to affected contracts, callers, state and regression tests. Use before modifying shared code, contracts, migrations or agent tools."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Change Impact Analysis

1. Identify changed behavior and affected API, event schema, database tables, UI routes, clients and operational workflows.
2. Search the repository for references and callers; inspect tests and documentation. External code graphs are optional, never mandatory.
3. Classify each impact as direct, downstream, compatibility, deployment or uncertain; provide an evidence link or path for each.
4. Choose targeted regression tests and smoke checks, including negative/rollback paths for high-risk changes.
5. Escalate risk for auth, PII, data migration, irreversible actions and cross-service contracts. Unknown callers are a limitation, not proof of safety.

Deliver: `change -> affected surface -> failure mode -> test -> remaining uncertainty`. Avoid blanket full-suite recommendations for trivial isolated changes.

## Pre-change vs actual-diff alignment (when scope warrants)

For cross-module, API/schema, authentication, migration, deployment or other high-risk changes, apply **one** existing impact analysis before implementation and revisit it after the actual diff:

1. **Before:** identify direct callers, downstream clients, persisted state, API/event contracts, migration and rollback constraints, targeted checks, affected documentation and boundaries not yet inspected. Cite real paths/contracts; avoid treating path heuristics as a call graph.
2. **After:** compare the reviewed plan against the exact actual diff. Mark each planned surface as `MATCHED`, `CHANGED` or `NOT_VERIFIED`; record newly affected consumers, scope drift, missing tests, documentation changes and remaining irreversible effects.
3. **Evidence:** link actual tests and check results only if executed on that revision. Missing call graph, hidden consumers, unexecuted rollback or unknown migration state remain `NOT_VERIFIED`. Escalate unapproved scope additions or unsafe recovery assumptions to the existing owner/release gate.
4. **Handoff:** use the existing Issue/PR/report location, or respond inline. Never create an alternate impact controller, force new document folders, run commands or edit unrelated user files just to satisfy a checklist.

The read-only `scripts/qa_change_impact.py` may propose path-scoped regressions; its output is **not** execution evidence. Follow the repository's existing authorization and delivery workflow. This alignment step refines Toolkit's `change-impact-analysis`, rather than installing ECC's overlapping `change-impact` as a second skill.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
