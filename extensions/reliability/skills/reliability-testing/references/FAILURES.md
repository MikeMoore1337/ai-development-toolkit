# Failure models, ordering and boundedness

| Failure | Injection | Independent invariant check |
| --- | --- | --- |
| Timeout before effect | Fail before durable write | State unchanged |
| Timeout after effect | Commit then lose response | Replay with same key has one effect |
| Dependency transient/permanent | Script N responses/errors | Retry only allowed errors and at most N attempts |
| Concurrent stale read | Force read A, read B, write A, write B | No lost acknowledged update under chosen consistency model |
| Dedup concurrency | Release two handlers at barrier | One durable effect per business identity |
| Before/after commit crash | Fault at transaction boundary | Rollback or durable committed state, no partial success |
| Duplicate/out-of-order | Redeliver event ID or version N-1 | No extra effect; obey chosen monotonicity policy |
| Ack lost after commit | Commit then abort before ack | Redelivery cannot duplicate business effect |
| Ack before commit | Ack then fault before persistence | Detect potential irrecoverable loss |
| Poison message | Deterministic always-failing item | Bound attempts and dead-letter policy |
| Restart | Close/reopen durable store | Preserve acknowledged effects and dedup keys |

Do not use arbitrary sleeps for concurrency or measure real retry delays in CI.
Inject exceptions at named checkpoints; use barriers or forced schedules to
reproduce racing interleavings. A forced schedule is a **model**, not proof
about a particular DB isolation level, scheduler or transaction implementation.
For physical durability or real queues, add approved integration tests with the
actual storage/transport and verify persisted state after a genuine process
restart. Keep side effects local, bounded, disposable and unprivileged.

Timeout budget covers the entire operation including retries and cancellation.
Backoff is capped; jitter is tested with controlled RNG or bounds. Do not retry
authorization failures or unkeyed non-idempotent effects automatically.
Classify ambiguous outcomes as STATE_UNKNOWN until reconciliation confirms
whether the effect committed.
