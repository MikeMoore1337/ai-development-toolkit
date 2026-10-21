# Portable data and pipeline contracts

A business requirement explains why information is needed. A logical data contract defines meaning; a physical schema defines concrete representation; a quality contract defines how observed data are checked; a metric contract defines how a business measurement is calculated. None implies another is verified.

Data contract: contract_id, dataset_id, dataset_version, producer, consumers, source, owner/UNKNOWN, record_identity, fields (name, type, nullability, required, allowed values, units), timezone/event-time semantics, uniqueness, references, business_rules, quality_expectations, update_policy, retention/UNKNOWN, privacy_classification, compatibility_policy, evidence.

Pipeline contract: pipeline_id, source datasets and versions, input/output contracts, transforms and versions, ETL/ELT choice, dependencies, operating mode, processing boundaries, error/retry policy, checkpoint, idempotency, replay/backfill policy, privacy and quality gates.

Data-quality contract: check_id, dataset_id, source_requirement, dimension, condition, invariant, scope, denominator_definition, threshold and its source, method, observation, evidence, status, remediation.

Metric contract: metric_id, objective, source requirement, definition, formula, numerator, denominator, units, grain, time_window, timezone, filters, exclusions, source datasets, transforms, quality prerequisites, owner/UNKNOWN, independent oracle, rounding, NULL/zero and late-arrival policy, evidence.

For schema evolution, evaluate nullable or required additions, rename, removal, type/range/default/allowed-value changes and changes of meaning; record old/new versions, producer and consumer compatibility, migration and deployment ordering, backfill need, validations, rollback limits. Nullable additions can still break strict consumers. Unverified compatibility = UNKNOWN.

Do not invent business rules, privacy policies, legal retention or ownership. Reuse contract-testing, database-migrations and existing QA skills rather than duplicating them.
