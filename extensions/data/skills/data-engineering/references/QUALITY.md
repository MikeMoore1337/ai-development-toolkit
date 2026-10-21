# Data quality gates and evidence

- Completeness: required values, expected records AND independently expected batch/interval coverage. Unknown input cardinality means dataset completeness UNKNOWN.
- Validity: schema, allowed values, fields, ranges and time semantics. Valid is not necessarily accurate.
- Accuracy: compare with an independently trusted source or fixed synthetic oracle. Otherwise NOT_VERIFIED.
- Freshness: distinguish event time, ingestion time, processing time and observation time; thresholds must be explicit before PASS.
- Uniqueness: stable record keys/composite keys and duplicate delivery both within and across batches. Other fields may repeat.
- Consistency: types, units, relationships, time zones, business invariants and independently checked aggregates.

Check statuses: PASS, FAIL, NOT_RUN, BLOCKED, UNKNOWN, NOT_APPLICABLE. Proposed thresholds stay PROPOSED until agreed.

Evidence must include pipeline and dataset/transform versions, source checksum, mode, batch IDs, input/accepted/rejected/output counts, time interval, checkpoint, checks/results, lineage, metric, independent oracle, errors and limitations.

Execution states include NOT_RUN, CONTRACT_VALIDATED, SYNTHETIC_TESTED, EXECUTION_PASS, EXECUTION_FAIL, DATA_QUALITY_PASS, DATA_QUALITY_FAIL, BLOCKED and NOT_MEASURED. No PASS without actual execution evidence. Synthetic oracle success proves only the supplied synthetic example. Lineage link is not source-authenticity verification.
