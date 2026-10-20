# Reliability scenario and evidence contract

Every case identifies: case_id, system, source_requirement, business_invariant,
initial_state, operation, failure_point, failure_type, injection_method,
expected_observable_result, expected_persistent_state, recovery_behavior,
execution_bound (seconds), test_level, actual_evidence, result_status, limitations.

Start with an invariant about durable state, not an HTTP status. Distinguish
request deduplication, idempotent business effect and an independently proven
end-to-end exactly-once guarantee. A local processed-ID table cannot make an
uncoordinated external effect exactly-once.

Per run record: fixture_version, canonical UTF-8 input SHA256, tested_invariant,
failure_point, execution_method, test_environment, expected_state,
observed_state, oracle_outcome, retry_count, recovery_outcome,
bounded_duration_seconds (only when measured), reproduction instructions and
remaining_limitations. Allowed result statuses: PASS, FAIL, NOT_RUN, BLOCKED,
NOT_MEASURED, NOT_APPLICABLE. Recovery statuses: RECOVERED, RECOVERY_PENDING,
RECOVERY_BLOCKED, STATE_UNKNOWN.

Never turn a test definition, synthetic fixture, restartable process or
successful retry into a real production SLA, RTO, RPO, MTTR or availability
claim. Run history is not stored in the Toolkit source. Outputs default to chat.
