---
name: reliability-testing
description: "Test failure resilience of stateful services with explicit invariants, bounded timeout/retry, duplicate delivery, concurrency, transaction rollback and recovery oracles. Use for fault injection and reliability regression, not ordinary unit tests, load testing, security scans or production chaos."
metadata:
  pack: "reliability"
  version: "1.0.0"
---

# Reliability Testing

**Use for:** "Test recovery after a worker restart", "Check idempotency after a lost response", "Find lost updates", "Verify ack after commit", "Test bounded retries", "Проверь отказоустойчивость и гонки".

**Do not use for:** ordinary API unit tests, React fixes, performance/load tests (#59), security scanning (#60), production deployment, or real chaos exercises. Use test-analysis-design for general tests, background-processing for worker implementation, database-validation for storage integrity, integration-testing for real boundaries, and failure-triage for diagnosing a failed CI job. This is **not a controller**.

1. **Inventory and scope:** identify persistent business effects, actual storage and broker guarantees, permissions, components and existing tests. Never assume a system has queues, transactions or exactly-once delivery.
2. **Invariant first:** record source requirement, initial state, operation, expected persistent state and what must remain true if a failure occurs. Use the [case and evidence contracts](references/CONTRACT.md).
3. **Failure model:** identify before/after-effect timeout, transient/permanent dependency errors, cancellation before/after commit, concurrent stale read/write, duplicate/out-of-order event, ack loss, poisoned message or restart. Choose the smallest meaningful subset; see [failure and oracle design](references/FAILURES.md).
4. **Controlled execution:** prefer deterministic failure points and barriers over sleeps, random stress or unbounded loops. For races, document exact forced interleavings and distinguish this from proof about real schedulers or isolation levels. Inject only into local synthetic environments unless a real environment is explicitly authorized.
5. **Verify and recover:** inspect durable business state **after** failure, reopen the storage when testing persistence, distinguish unknown outcome from rollback, and test a repeat with the same idempotency key. Bound overall deadline, backoff, attempts and test impact. A timeout does not mean no side effect.
6. **Report evidence:** test ID, fixture/version/SHA, injected failure point, independent oracle, observed state, retry count, recovery status and limitations. Link the discovered defect to an ordinary implementation workflow and add regression tests; do not silently modify applications. See [worked scenarios](references/EXAMPLES.md).

**Offline demonstration:** in an authorized development checkout run `python scripts/validate_reliability.py` and `python -m unittest tests.test_reliability -v`. Each reference case must PASS its independent expected-state oracle; each deliberately defective implementation must FAIL the **same** oracle.

**Safety and portability:** no mandatory queue, DB engine, provider, external network, extra dependency or cost. Synthetic SQLite and virtual ordering cannot prove production recovery, distributed exactly-once, broker delivery guarantees or freedom from all races. User-project Toolkit copies are read-only; return reports in chat or an explicitly approved destination. Never inject into production, external services or unknown environments.
