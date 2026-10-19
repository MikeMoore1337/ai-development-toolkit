---
name: database-migrations
description: "Use when evolving persisted schema or data with compatibility and recovery constraints."
---

# database migrations

Discover the application's actual language, framework and infrastructure first. Reuse existing conventions and respect project approvals.

1. Inspect current versions, migration tooling, data volume, backups and recovery capabilities.
2. Define target invariants, reader/writer compatibility, acceptable locking and downtime.
3. Prefer additive expand/migrate/contract where simultaneous versions require it; destructive changes may be irreversible.
4. Design idempotent, resumable backfill batches and validation queries with explicit stop conditions.
5. Never perform production migrations or destructive writes without approval. Test on representative nonproduction data.

**Output:** Migration sequence, compatibility window, rollback/restore limitations and validation.
