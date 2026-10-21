# Incremental processing and safe reprocessing

Record source version, batch_id, sequence/cursor, stable record identity, high-water mark, checkpoint, late-arrival threshold, deletion policy where supported, duplicate delivery and retry policy.

Stage data and checkpoint as one atomic commit when supported; otherwise document replay and compensating recovery. A crash before commit must leave the checkpoint unchanged. Replay of identical batches must be idempotent; a conflicting replay must fail, not silently overwrite. Do not promise distributed exactly-once.

Lineage at dataset level is generally sufficient. Record source dataset/version, batch, transform/version, output dataset, temporal window, dependencies, source quality, failures and completeness. Field/record level is optional and evidence-dependent; missing links => LINEAGE = PARTIAL.

For backfill: record cause, bounded interval, source and transform revisions, dry-run plan, estimate/cost, resources, checkpoint/overlap, idempotency, expected invariants, recovery/rollback, permission, execution and independent post-run QA. Code rollback is not a data rollback. Backfill planned != backfill run != corrections verified. Do not run production backfill.
