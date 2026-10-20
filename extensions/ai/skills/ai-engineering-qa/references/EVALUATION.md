# Portable evaluation and dataset contracts (v1)

Use this alongside existing Issue #11 scripts/skill_eval.py, agent_eval_review.py and agent_eval_fixtures.py. They own real paired skill trials and independent review. This document does not introduce a new runtime, model judge, agent launcher or score aggregation service.

## Dataset
dataset_id, version (SemVer), sha256 of canonical UTF-8 JSON cases (sorted object keys, no whitespace), categories, limitations and cases. Every case has stable id, category, source, input, expected_properties, negative_conditions and independent oracle {type, assertion}. Keep sources synthetic or permitted and document change reason. Changes to cases require new version and digest; do not alter an oracle to turn a failure green. Changed datasets are not automatically comparable.

## Evaluation record
evaluation_id; dataset_id/version/sha256; scenario_id/category; model_id/provider/model_revision (or UNKNOWN); prompt_version; tool_configuration; retrieval_configuration; baseline/candidate; expected_properties; negative_conditions; independent_oracle; execution_environment; actual_observations; evidence_refs; limitations; execution_type; metrics and result_status. Use lifecycle keys dataset_prepared, contract_validated, oracle_validated, execution_completed, acceptance_verified, effectiveness_measured.

A static fixture may PASS only the first three lifecycle stages. Mark later stages NOT_RUN or NOT_MEASURED. Independent oracle must detect a deliberately broken fixture; self-grading model text alone is not an oracle.

## Comparability
For baseline and candidate pin dataset/version/SHA, task prompt, provider/model/revision, tool/retrieval config, sampling, repeat count, environment and oracle. State every difference. A single run has no statistically significant difference; cross-provider aggregates require an explicit justification. Do not infer token usage from character count. Latency and usage require source evidence; if price is not independently grounded COST = UNKNOWN.

Status meanings: PASS observed contract satisfied; FAIL observed contract violated; NOT_RUN not executed; NOT_MEASURED cannot be measured by selected evidence; BLOCKED prerequisite missing; NOT_APPLICABLE irrelevant. JSON validation is not answer correctness and schema PASS is not end-to-end security.
