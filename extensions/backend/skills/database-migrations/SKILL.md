---
name: database-migrations
description: "Use when planning or implementing compatible schema or data migrations with measurable validation and recovery."
---

# Database migrations

**Use for:** persistent data shape changes, backfill, expand/contract and rollback planning. **Do not use for:** ordinary query optimization (data-access) or direct production execution without owner approval.

**Inputs:** current/target schemas, deployed reader and writer versions, storage engine, row volumes, backup/restore ability, lock budget and nonproduction test environment.

1. Establish data invariants, compatibility matrix and measured or estimated lock/duration constraints; inspect migration tooling and permissions.
2. Prefer expand -> migrate -> contract when old and new applications overlap: add compatible columns first, update writers/readers in safe order, backfill existing rows in resumable batches, verify, then contract only after old readers are gone.
3. Make batches restartable and idempotent; define checkpoint, uniqueness, validation queries, stop threshold and failure handling. Evaluate lock behavior with the actual database engine.
4. Separate code rollback from data rollback. A destructive contract phase may require restore from tested backup rather than inverse SQL.
5. Test success, partial interruption, re-run, old-client compatibility and restoration procedure on isolated representative data. Never run production migrations or destructive writes without explicit approval.

**Output:** phase-by-phase runbook, compatibility window, exact validation queries/invariants, recovery boundary, executed evidence and NOT_MEASURED checks.

See [expand/migrate/contract worked example](references/expand-migrate-contract.md).
