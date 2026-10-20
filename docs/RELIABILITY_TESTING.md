# Reliability Testing (Issue #58)

[Русская версия](ru/RELIABILITY_TESTING.md) | [Optional skill](../extensions/reliability/skills/reliability-testing/SKILL.md)

Reliability is observable correctness despite expected failures, not the presence
of a retry loop. Start with a business invariant, identify a fault checkpoint,
inject it locally, verify persistent state and recovery, and preserve the
regression test. Use the optional `reliability-testing` profile; this is not an
automatic QA Pack install or a new controller.

## Understand the guarantees

- **Timeout:** an operation may commit before its reply is lost. Its outcome
  remains unknown to the caller until read-back or reconciliation.
- **Retry vs idempotency:** retry repeats the request; idempotency prevents a
  second unauthorized business effect. Bound attempts, total deadline and
  backoff, and never blindly retry authorization errors or unkeyed writes.
- **Concurrency:** a lost update occurs when concurrent actors write from stale
  reads. A deterministic interleaving helps reproduce it, not rule out all races.
- **At-least-once:** a message can be delivered again. Deduplication and
  ack-after-commit can preserve a local invariant, but neither proves distributed
  end-to-end exactly-once (especially for external side effects).
- **Transactions:** a fault between logical updates can leave partial state
  unless the real storage transaction atomically commits or rolls back.
- **Recovery:** inspect durable committed state, dedup keys, checkpoints and
  pending work after restart. Distinguish RECOVERED, RECOVERY_PENDING,
  RECOVERY_BLOCKED and STATE_UNKNOWN.

## Safe offline checks

From an authorized Toolkit development checkout:

~~~sh
python scripts/validate_reliability.py
python scripts/validate_reliability.py --json
python -m unittest tests.test_reliability -v
~~~

The nine independent offline oracles test duplicate delivery, ambiguous
timeouts, lost updates, rollback, bounded retry, out-of-order events, ack order,
SQLite reopen and optimistic version conflicts. The same oracles reject nine
known-bad variants. No waits, paid tools, network calls, production tests or
long-running workloads are required. They **do not** verify real worker crash
recovery, physical durability, race freedom, Kafka/RabbitMQ semantics, external
exactly-once effects or availability/SLA. Those need separately authorized
integration tests against actual infrastructure.

**Beginner prompt:** "Check whether my app preserves data if a request is
repeated, the server stops or two users edit simultaneously. Start with safe
offline tests and clearly separate tested from untested properties."

**Expert prompt:** "Model bounded at-least-once message delivery with a
durable inbox, lost ack, commit ordering, version conflict and replay after
restart. Provide deterministic fault points, independent state oracles, bounded
execution and explicitly NOT_MEASURED real-broker properties."

Reuse `background-processing`, `integration-testing`, `database-validation`,
`contract-testing` and `failure-triage`. Full
[case/evidence contract](../extensions/reliability/skills/reliability-testing/references/CONTRACT.md)
and [failure patterns](../extensions/reliability/skills/reliability-testing/references/FAILURES.md)
are optional reference materials.

When applying Toolkit to another project, every Toolkit copy is read-only.
Return results in chat by default and write files only to a separately approved
destination. No production chaos, real broker mutation, user data capture,
security scanning or load tests are authorized by this skill.
