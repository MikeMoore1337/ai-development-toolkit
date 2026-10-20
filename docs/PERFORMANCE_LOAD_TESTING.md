# Performance & Load Testing (Issue #59)

[Русская версия](ru/PERFORMANCE_LOAD_TESTING.md) | [Optional skill](../extensions/performance/skills/performance-load-testing/SKILL.md) | [Portable contract](../extensions/performance/skills/performance-load-testing/references/CONTRACT.md)

Performance testing measures how a specific operation behaves under specified
conditions. **Load testing** checks bounded, intended traffic; **stress testing**
pushes beyond known limits and is not automatically authorized. Neither is the
same as verifying recovery from crashes and duplicate events.

## Reuse-first audit

| Concern | Reused | Unique gap / decision |
| --- | --- | --- |
| Browser rendering and interactions | `frontend-performance` | REUSE; not duplicated |
| Baseline measurement discipline | `frontend-performance` | REFINE: reproducible cross-version load comparisons |
| Load modeling and requested vs achieved rate | `test-strategy` | NEW: bounded constant/step/mixed workload contracts |
| Latency, tail percentiles, throughput and errors | QA analysis methods | NEW: explicit calculation and independent arithmetic tests |
| Performance budgets and variation | `frontend-performance` | REFINE: approval, statistics and failure classifications |
| Resource observability | `failure-triage` | REUSE; missing data remain NOT_MEASURED |
| Bottleneck evidence | `failure-triage`, backend skills | REUSE; observed vs hypothesized causes |
| Reliability under retries and state faults | `reliability-testing` | REUSE; separate functional assurance |
| External load safety | `security-boundaries` | NEW: executable in-process-only safety caps |

The optional `performance-load-testing` profile combines a specialist skill
with existing `test-strategy` and `failure-triage`. It does not add a
controller or automatically install the entire QA Pack.

## Concepts in plain language

- **Latency**: duration from operation start to finish. Use monotonic clocks.
- **Throughput**: attempts, completions and successful operations per *actual*
  elapsed second, not the requested RPS.
- **p95 / p99**: the 95th / 99th percentile of a declared timing population.
  Small samples cannot reliably characterize the tail.
- **Baseline**: version and measurement conditions recorded before changes.
- **Candidate**: proposed change tested with the same workload, input data,
  cache, environment, warmup and calculation method.
- **Performance budget**: metric, units, maximum/minimum acceptable result and
  tolerance agreed **before** looking at candidate results; default PROPOSED.
- **Variation**: noise from machines, background work and cache. Use repeated
  runs and raw distributions, never a single fastest result as proof.
- **Correctness**: matching outputs, successful operations and expected states
  are necessary. Faster but wrong must never PASS.

## Try the safe offline example

From an authorized Toolkit development checkout:

```sh
python scripts/validate_performance.py --mode virtual --profile constant
python scripts/validate_performance.py --mode virtual --profile step
python scripts/validate_performance.py --mode virtual --profile mixed
python scripts/validate_performance.py --mode local --operations 5 --duration 2
python -m unittest tests.test_performance -v
```

The **virtual** mode uses artificial timestamps and fixture latencies. It
checks arithmetic and decisions, not system performance. **Local** mode measures
only a tiny in-process fictional checksum: it is a bounded smoke test, not
application evidence. It uses no HTTP listener or remote endpoint, needs only
Python standard library, and reports JSON to stdout (no report written by
default). Both versions return the same functional checksum; the deliberately
broken fast variant is rejected by the correctness oracle.

Hard caps, validated before running: **5 RPS, 50 total operations including
warmup, 2 concurrent operations, 10 seconds**. The CLI accepts no URL, request
payload, host or script. A failed safety check aborts rather than proceeding.
No production, public, third-party, cloud, VPS, shared staging or real data
traffic is run by this example.

## Interpret the report

Use the [performance contract](../extensions/performance/skills/performance-load-testing/references/CONTRACT.md)
for source requirement, test and scenario IDs, revisions, workload, raw samples,
units, methods, actual interval, errors, observed/suspected bottlenecks,
functional oracle and limits. In the offline example, no CPU/RAM is captured;
resource data are `NOT_MEASURED`. A passing fixture comparison is not an
approved SLO or evidence about an unrelated real application.

Possible results: `PASS` (no demonstrated regression under these conditions),
`REGRESSION`, `INCONCLUSIVE` (insufficient evidence),
`COMPARISON_INVALID` (unfair/malformed inputs), `NOT_MEASURED` or
`BLOCKED` (broken functional contract). p95 requires at least 20 samples
and p99 at least 100 in this reference; p99 therefore remains unmeasured in
the capped demo. The algorithm is type-7 linear interpolation.

## Applying to another project

The Toolkit copy is **read-only**: send the results in chat by default.
Save source data or generated reports only to a separately authorized location.
Confirm exact target ownership, environment, RPS, concurrency, duration, cost,
data segregation, stop triggers and timing **before** running any real load,
including staging. Never infer authorization from a URL or endpoint name.
A shared CI runner is for deterministic contract tests, not absolute latency
SLO gates.

Optional specialist tools such as k6, Locust or JMeter may be evaluated for
an explicitly authorized real-system project, but are neither installed nor
required here; verify current licensing and features from official vendor
sources before recommending a particular deployment. Distributed generators,
paid clouds and dedicated infrastructure are not part of this issue.

### Optional tools checked against official projects (2026-10-20)

- [k6](https://github.com/grafana/k6): JavaScript-based load testing, AGPL-3.0. Consider for approved programmable protocol tests.
- [Locust](https://github.com/locustio/locust): Python user-behavior scenarios, MIT. Consider if Python-defined flows are useful.
- [Apache JMeter](https://github.com/apache/jmeter): Java load/functional testing and reports, Apache-2.0. Consider for existing JMeter workflows.

No tool above is installed, mandatory, invoked or connected to an online service. A license does not grant target-testing permission.

**Beginner prompt:** "Check whether my local application has slowed down.
First identify one safe scenario and compare old/new versions fairly; do not
test any public site or save results inside the Toolkit repository."

**Expert prompt:** "Design a bounded constant/step workload with pinned data,
warmup/cache controls, explicit p95/throughput/error budgets and baseline vs
candidate comparisons. Reject changed environments, functional failures and
unapproved targets. Preserve raw observations and quantify noise."
