# Performance Test Contract (Issue #59)

Record explicit values or `UNKNOWN`; do not invent evidence. Small function checks may use a compact report; large engagements may attach separate raw data outside Toolkit.

| Field | Requirement |
| --- | --- |
| test_id / scenario_id / source_requirement | Stable IDs linking measured behavior to a requirement |
| target_component / source_revision | Exactly what was executed, including build/commit |
| workload_model | Constant, step, bounded burst, mixed operation ratios, concurrency, optional background tasks; actual rate vs requested rate |
| execution_environment | Host class, OS, interpreter/runtime, build mode, CPU constraints when known |
| dataset_version / input_size / read_write_mix | Fixed and comparable; if unknown mark `UNKNOWN` |
| warmup_policy / cache_state | Equal for baseline and candidate |
| measurement_method / percentile_method | Monotonic elapsed measurements; type-7 linear quantile in reference example |
| duration / operation_limit / concurrency_limit / rate_limit / stop_conditions | Finite, checked before running; deadline must be enforced |
| baseline_definition / budget | Version, metric, units, threshold, tolerance, evidence basis and APPROVED or PROPOSED |
| expected_properties / functional_oracle | Exact result checking independent of speed |
| observed_samples / errors | Raw attempts, status, elapsed timings including slow and failing requests |
| environment_limitations / evidence_references | Explicit omissions, source of metrics, run identity |
| result_status | PASS, REGRESSION, INCONCLUSIVE, COMPARISON_INVALID, NOT_MEASURED, BLOCKED |

## Workload recipes

- **Constant:** finite requests at fixed maximum requested RPS.
- **Step:** two or three increasing bounded levels; never raise above authorized cap.
- **Burst:** a short bounded peak with explicit total-operation limit.
- **Mixed:** deterministic mix with known operations, read/write ratio, input size and weights.
- **Concurrency:** declare in-flight limit independently of arrival rate.
- **Background:** only if actual target has worker processing and it is safe to isolate.

All synthetic choices must be marked `SYNTHETIC_ASSUMPTION`, not measured user traffic.

## Metrics and interpretation

Use `time.monotonic_ns()` for real elapsed operation intervals. Calculate mean, median, min, max and range over the declared sample population. For percentile p, type-7 linear interpolation sorts n samples and interpolates at zero-based index `(n - 1) * p`; different algorithms are not comparable without recalculation. In the reference example, p95 needs at least 20 completions and p99 at least 100; these minimums **are reporting guardrails**, not statistical-significance proofs.

Attempted throughput = attempts / actual measurement interval; completed throughput = completed / interval; successful throughput = successful / interval. Requested RPS is a generator input, not achieved throughput. Error rate = (all attempts not classified SUCCESS) / all attempts, state numerator and denominator. Preserve categories `SUCCESS`, `APPLICATION_ERROR`, `TIMEOUT`, `TRANSPORT_ERROR`, `TEST_HARNESS_ERROR`, `CANCELLED`; expected application rejections require explicit scenario-specific policy.

Resource metrics (CPU, memory/RSS, I/O, queue depth, threads, network) are optional and need a cited observer and units. Python `tracemalloc` is not full RSS, `process_time` not CPU utilization. Never manufacture numbers; use `NOT_MEASURED`.

## Comparison and negative cases

Reject environment, dataset, cache, warmup, workload, build mode, measurement method and budget mismatches as `COMPARISON_INVALID`; malformed or missing raw samples likewise. Missing baseline = `NOT_MEASURED`, too few valid measurements = `INCONCLUSIVE`, incorrect output = `BLOCKED`; detected errors or latency regression = `REGRESSION`. Any approved budget crossing is a regression; a proposed budget is advisory. With noisy observations use repeated paired runs and explain variability, not a post-hoc threshold that passes the candidate. A smaller median in this fixed virtual fixture means only that fixture is smaller, **not** that the application is faster.

A **confirmed bottleneck** requires profiling/controlled evidence. High response time alone cannot identify a database, network, CPU or lock as the cause. Keep hypotheses separate from verified bottlenecks.

## Safety

Issue #59's offline Python demonstration accepts **no target address at all**. Caps: 10 s, 5 RPS, 50 operations inclusive of warmup, 2 concurrent operations. No sockets, arbitrary script execution or paid dependencies. Out-of-range input is rejected before load. For real application testing require explicit target ownership, permitted environment/intensity, potential impact and expense, abort plan, test data isolation and separate approval. Do not load public sites, third-party APIs, staging or production by default.

Report results in chat for third-party user projects. Store only self-owned synthetic code/fixtures/tests in Toolkit; user-specific measurements and reports belong outside its read-only copies.
