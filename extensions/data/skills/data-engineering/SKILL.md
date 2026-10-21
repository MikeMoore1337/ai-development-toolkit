---
name: data-engineering
description: "Design and verify ETL/ELT data pipelines, logical data contracts, quality, lineage, incremental loads, backfills and analytics metrics. Not for ordinary SQL queries, migrations, API tests or product metric ideation."
metadata:
  pack: "data"
  version: "1.0.0"
---

# Data Engineering & Analytics

Use for: ETL/ELT pipelines, combining CSV sources, diagnosing wrong aggregates, dataset contracts, missing/duplicate batches, incremental processing, data quality and lineage. Russian: «проверь качество данных», «спроектируй ETL», «выполни анализ происхождения данных».

Do not activate for isolated SQL queries (data-access), physical constraints (database-validation), a table migration (database-migrations), API schema tests (contract-testing), product-metric goal setting (product-discovery), server monitoring (observability-sre), library upgrades or deployment. This is a focused skill, not an ETL engine or new workflow controller.

1. Establish source and destination boundaries, permissions, version, retention, private data and owner. Unknown policy stays UNKNOWN. Toolkit copies used by external projects remain read-only; output defaults to chat.
2. Separate business requirements, logical data contract, physical storage schema, quality contract and metric contract. Define source, producer/consumer, identities, fields/types/nullability, units/time zones, uniqueness, privacy, update policy, compatibility and evidence. See [contracts](references/CONTRACTS.md).
3. Choose ETL (transform before load) or ELT (transform after load) based on data location, scale, privacy, storage capability, available computation, latency and cost. Specify pipeline input/output contracts, transforms, boundaries, retries, errors and evidence. Neither is universally better.
4. Assess completeness of required fields AND expected records/batches, validity, consistency, uniqueness, event-time freshness and independent accuracy. Without a trusted oracle mark accuracy NOT_VERIFIED; without expected source size mark dataset completeness UNKNOWN. Thresholds not agreed are PROPOSED. See [quality](references/QUALITY.md).
5. Treat changes to field meaning as potential breaking changes even when types match. Verify producer and consumer compatibility, migration order, backfill need, rollback limitations. Link dataset/batch/transform/output lineage; mark gaps PARTIAL.
6. For incremental work declare stable record and batch IDs, checkpoint, watermark, lateness and duplicate policies. Do not advance checkpoint before durable output, or promise distributed exactly-once from local deduplication. Plan authorized bounded backfill and independent post-reprocessing validation. See [recovery](references/RECOVERY.md).
7. Analytics metrics need stated formula, numerator, denominator, zero handling, grain, time window/timezone, filters, NULL rules and rounding. Business System Analysis sets meaning; Engineering calculates; QA independently verifies.
8. Report actual observations, checksum, source/transform revisions, processed/accepted/rejected counts, evidence, checks, lineage, remaining UNKNOWNs and approval state. Synthetic PASS does not prove production quality.

Reuse existing data-access, contract-testing, database-validation, test-data-management, database-migrations, reliability-testing, observability-sre and business-system-analysis selectively; never install the whole QA pack for this task.

Beginner request: "Combine CSV/Excel files, check duplicates, missing records and totals; do not overwrite originals." Expert request: "Design incremental ETL/ELT with versioned contracts, watermark, schema evolution, backfill, lineage and independent gates."

Offline synthetic example: fixtures/data-engineering/README.md (from Toolkit root) is runnable with the Python standard library only inside Toolkit. External users can use any language, database or cloud and require no Python, paid service, API, DWH, broker or ETL framework.
