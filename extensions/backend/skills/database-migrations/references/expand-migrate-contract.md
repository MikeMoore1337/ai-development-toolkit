# Compatible name-field migration

**Context:** Table accounts(id, name NOT NULL). Existing readers expect name. New clients need display_name, but deployments are staggered. No production writes are authorized by this example.

1. **Expand:** add nullable display_name, leaving name unchanged. Old readers and writers continue to work. Measure DDL lock effects on a production-like copy before scheduling.
2. **Adapt writers:** dual-write name and display_name transactionally (or use a verified translation layer). Maintain compatibility with old writers during the transition.
3. **Backfill:** process stable id ranges in bounded batches, setting display_name = name only where display_name IS NULL. Persist progress, retry safely after interruption, and avoid clobbering newer edits.
4. **Validate:** select COUNT(*) WHERE display_name IS NULL; expect 0 only after old-writer gap is closed. Compare sampled name/display_name where appropriate, check row counts and violations and exercise both client versions.
5. **Adapt readers:** new readers prefer display_name with documented fallback, but old readers still use name. Monitor read/write consistency through coexistence.
6. **Contract:** only after old readers/writers are retired and correctness has been observed, consider tightening NOT NULL and dropping name in separate reviewed releases.

**Failure scenario:** worker stops after batch 20. Restart from checkpoint; already migrated rows are not overwritten. If a newer user edit occurs, predicate/locking or version semantics must protect it.

**Negative scenario:** dropping name in the first migration breaks old readers and may lose data. An unchecked table-wide UPDATE can lock too long or overwrite concurrent edits.

**Acceptance:** old and new clients function during the overlap; backfill can resume twice without data drift; counts and constraints match; recovery from a representative backup is rehearsed. A schema rollback alone cannot restore deleted values.

**Limits:** Syntax and lock guarantees depend on the actual database. This is an illustrative runbook, not SQL approved for a specific engine.
