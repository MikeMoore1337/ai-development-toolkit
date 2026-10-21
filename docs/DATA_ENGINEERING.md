# Data Engineering & Analytics (Issue #65)

[Русская версия](ru/DATA_ENGINEERING.md)

Optional data-engineering profile adds exactly one specialized skill and reuses existing Backend, QA and Reliability skills when relevant. It does not bundle an ETL framework, workflow orchestrator, data warehouse, broker, BI platform, paid API or runtime dependency.

## Data concepts

- ETL: extract, transform, load. ELT: extract, load, transform in target storage. Choose based on data location, privacy, compute availability, volume, delay and cost. Neither is universally better.
- Data Contract: agreed logical meaning, identity, fields/types, producer, consumer, version, privacy and temporal semantics. Not the same as a physical database schema or business requirement.
- Data Quality: completeness of fields AND batches, validity against contract, consistency of units/relations, uniqueness of record IDs, freshness against event and observation times, and accuracy against independent truth. Validity does not prove accuracy.
- Schema Evolution: evaluate producer and consumer compatibility, including semantic changes without a type change. Adding a nullable field does not guarantee strict consumers will accept it.
- Data Lineage: origin dataset/version, source batch, transform/version and output. Unknown links are PARTIAL, not inferred. Provenance edges do not prove source authenticity.
- Incremental Processing: checkpoints after successful persistence, stable batch identity, retries, duplicate and late arrivals. Local idempotency does not demonstrate exactly-once delivery across external services.
- Backfill: planning, authorized execution and independently confirmed data repair are separate stages. Re-running a batch can double count without idempotency.
- Analytics Metric: explicit formula, numerator/denominator, grain, window, timezone, NULL, zero division, filters and rounding; business owner determines meaning, engineer implements, QA independently verifies.

## Reuse-first gap matrix

| Capability | Reuse | Issue #65 addition |
| --- | --- | --- |
| Access, transactions, physical integrity | `data-access`, `database-validation` | No duplication |
| Contracts, consumers, schema changes | `contract-testing`, `database-migrations` | Pipeline-level version and semantic decisions |
| Quality and test data | `test-data-management`, `integration-testing` | Full-dataset completeness, freshness and independent aggregate oracle |
| Stateful recovery | `reliability-testing`, `observability-sre` | Batch checkpoints, bounded late arrival and synthetic backfill |
| Business and metric requirements | `business-system-analysis`, `product-discovery` | Implemented numerator/denominator and independent metric validation |
| ETL/ELT, lineage | Existing partial storage and QA guidance | One specialized source-to-result lifecycle skill |

No separate roles, workflow controller or new QA Pack is required. The example models local atomic commit only; real storage guarantees require separate tests.

## Beginner

Example request: "I have Excel and CSV exports. Help combine them using confirmed keys, find duplicate or missing rows, verify totals and preview changes without overwriting original files." No ETL vocabulary is needed. Real Excel processing can require an external project's chosen Excel library; the skill does not install one.

## Expert

Example request: "Design versioned incremental ETL/ELT contracts, schema evolution, change capture, deduplication, watermark and checkpoint semantics, late arrival, lineage, bounded backfill and independent metric/data-quality gates. Record UNKNOWN for unverified properties."

## Offline evidence

From Toolkit root:

    python scripts/validate_data_engineering.py
    python -m unittest discover -s tests -p test_data_engineering.py -v

The in-memory reference uses three synthetic batches, including an accepted late event, and 25 negative mutations. The same independent auditor must accept the good run and reject each broken variant. Separate fixture constants are metric oracles; a pipeline's own sum is not independent evidence. Interruption and replay are checked without a real database.

Only Python standard library is needed for Toolkit's internal tests, not for users applying this portable skill to other languages. No network, personal data, external services or costs. Real database durability, source authenticity, real-data accuracy, schema consumers, large-scale performance and live AI-client activation are NOT_TESTED/NOT_MEASURED. Synthetic PASS is not production PASS. No user reports or external project data may be written into Toolkit.

[Skill](../extensions/data/skills/data-engineering/SKILL.md) - [Contracts](../extensions/data/skills/data-engineering/references/CONTRACTS.md) - [Fixtures](../fixtures/data-engineering/README.md).
