---
name: data-access
description: "Use when changing backend persistence queries, transaction invariants and concurrent writes."
---

# Data access

**Use for:** stored-data integrity, concurrent mutations, transaction scope or query bottlenecks. **Do not use for:** schema rollout plans (database-migrations) or service decomposition decisions.

**Inputs:** storage engine, isolation/transaction semantics, data model, invariant, access rights and realistic isolated data set. Follow repository approval gates; never assume a transaction spans external services.

1. Name a falsifiable invariant before implementation (e.g., at most one active reservation per resource and time slot).
2. Identify the source of truth and enforce uniqueness at the storage boundary when supported; do not rely on a pre-insert read alone.
3. Map atomic operations, isolation requirements, expected conflicts and rollback. Protect against lost updates with constraints, locks or version comparisons as appropriate.
4. Define retry behavior for transient serialization failures; never blindly repeat a non-idempotent external side effect. Parameterize queries and prevent data exposure.
5. Test two concurrent requests for the same slot, a failed partial update, duplicate invocation and a slow path on representative volume. Record affected rows and invariant checks, not only successful HTTP codes.

**Output:** storage invariant, transaction/conflict policy, query and concurrency evidence, negative checks and untested limits.

**Negative example:** read "slot free" twice then insert twice without a uniqueness constraint. Both reads can succeed. An atomic unique index or equivalent constraint must reject one competing insert. No production writes without approval.
