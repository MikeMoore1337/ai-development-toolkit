---
name: performance-load-testing
description: "Measure latency, throughput and error rates under bounded workloads; define performance budgets and compare baseline with candidate safely. Use for load modeling or performance regressions, not browser-only rendering, failure recovery, security scans or production stress."
metadata:
  pack: "performance"
  version: "1.0.0"
---

# Performance & Load Testing

**Use for:** "Measure API response time", "Prepare safe local load testing", "Compare baseline and candidate", "Define a p95 budget", "Проверь скорость под нагрузкой", "Обнаружь регрессию производительности".

**Do not use for:** normal unit tests, authorization bugs, UI redesign, repeated-event recovery, security audits, deployments or API provider pricing. Narrow browser rendering: use `frontend-performance`; state correctness under faults: `reliability-testing`; diagnosis: `failure-triage`. This skill is **not** a workflow controller.

1. **Define scenario:** record requirement, operation, dataset, environment, revision, functional oracle and whether measured data represent real users or `SYNTHETIC_ASSUMPTION`. Never invent SLA, traffic or RPS.
2. **Model workload:** choose constant, step, burst, mixed, concurrency or background only when relevant. Specify read/write mix, data size, cache state, warmup, duration, max requests, concurrency, rate and abort criteria. A synthetic profile is not production-representative.
3. **Specify budget before running:** metric, units, threshold, tolerance, measurement method, test conditions, source and approval. Use `PROPOSED` for unapproved targets and `NOT_MEASURED` for unavailable observations.
4. **Choose safe execution:** use a local owned disposable target and explicit upper bounds; refuse external URLs, production/staging without scoped authorization, open-ended stress, paid providers or shared data. Validate bounds **before** any work. Prefer the standard-library [bounded offline example](../../../../scripts/validate_performance.py) for Toolkit demonstrations. It never opens sockets.
5. **Measure and retain evidence:** monotonic timestamps, raw successes/failures/timeouts, attempted/completed/successful operations per actual elapsed second, latency mean/median/p95/p99 when sample sizes suffice; use consistent percentile definition. Record environment, cache, hardware variability and resource source; absent resource instrumentation = `NOT_MEASURED`. Do not filter slow samples without a documented reason.
6. **Compare fairly:** one scenario and dataset, same warmup, build mode, measurement method, cache, workload, concurrency, environment and budget. Run several repetitions where feasible and report spread. If not comparable, `COMPARISON_INVALID`, not a speedup.
7. **Decide and investigate:** gate functionality first; faster-but-wrong = `BLOCKED`. Separate error regression from latency regression, proposed budgets from approved budgets, observed bottleneck from testable hypothesis. Mark weak evidence `INCONCLUSIVE`. Confirm any suspected cause with profiling before asking an engineering skill to change code, then rerun functional and performance tests.
8. **Report concisely:** what was tested, workload/limits, raw evidence, aggregates, baseline/candidate revisions, comparison status, risks, unknowns and next action. Return user-project results in chat by default; Toolkit is a **read-only** source when consumed by other projects.

[Contract, workload and comparison rules](references/CONTRACT.md). [Reference guide EN](../../../../docs/PERFORMANCE_LOAD_TESTING.md) and [RU](../../../../docs/ru/PERFORMANCE_LOAD_TESTING.md).

**Synthetic demo:** `python scripts/validate_performance.py --mode virtual` demonstrates contract mathematics (NOT benchmark evidence). `python scripts/validate_performance.py --mode local` runs only safe in-process operations (bounded smoke, NOT real application performance). `python -m unittest tests.test_performance -v` validates both. No mandatory k6, Locust, JMeter, HTTP, cloud, paid tooling or production tests.
