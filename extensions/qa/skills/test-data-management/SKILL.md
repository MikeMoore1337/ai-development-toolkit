---
name: test-data-management
description: "Plan isolated reproducible test data and cleanup. Use when automated tests create state or run concurrently."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Test Data Management

1. Specify fixture ownership, lifecycle, uniqueness, namespaces and environment scope.
2. Ensure deterministic setup or a documented random seed; ensure the test asserts on only its own records.
3. Handle parallel workers, rollback/cleanup and partial failures. Never silently delete shared or production data.
4. Use synthetic/non-sensitive values; avoid live personal data, credentials and production identifiers in snapshots.
5. For retries, make setup idempotent or detect and isolate leftovers; ensure tests can rerun safely.

Output fixture plan with creation, ownership, isolation, cleanup and permissions. A global cleanup script requires separate approval.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
