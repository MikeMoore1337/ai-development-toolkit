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

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.

## Optional deterministic path-based preflight

For a bounded offline first pass over changed paths or an exact-SHA local Git diff, reuse the existing read-only helper [`scripts/qa_change_impact.py`](../../../../scripts/qa_change_impact.py) and the [RU/EN scope and evidence guide](../../../../docs/QA_CHANGE_IMPACT.md). This only proposes checks with `NOT_RUN` and `PATH_HEURISTIC_ONLY`: inspect the actual diff, consumers, issue AC and project governance before execution or any quality gate. Do not interpret heuristic path matches as a proven call graph, executed tests or release approval.
