---
name: background-processing
description: "Use when implementing queues, workers, scheduled work, retries or duplicate event handling."
---

# Background processing

**Use for:** asynchronous work and delivery behavior. **Do not use for:** synchronous handler-only logic or orchestration of an entire feature.

**Inputs:** trigger, broker/runtime guarantees, payload identity, external effects, failure modes, retry budget and approval constraints. Inspect existing infrastructure; do not introduce a queue if it is unnecessary.

1. Draw the event-to-effect path and distinguish at-most-once, at-least-once and actual ordering guarantees. Never claim exactly-once end-to-end without evidence for every side effect.
2. Define a stable business deduplication key and atomic inbox/result guard when needed. An in-memory seen set is not crash-safe.
3. Specify acknowledgement point relative to persistent state and external effects; when side effects cannot share a transaction, plan outbox, reconciliation or compensating behavior.
4. Bound exponential backoff, timeouts, retries and poison-item/dead-letter treatment; protect payloads in logs. Ensure shutdown/restart is safe.
5. Test duplicated delivery, out-of-order events, partial side effects, restart between effect and acknowledgement, temporary and permanent downstream failure.

**Example:** event E7 is delivered, balance adjustment commits, worker crashes before ack, E7 is redelivered. A durable unique processed-event marker checked in the same storage transaction prevents double adjustment; an external payment call needs its own stable idempotency key or reconciliation.

**Output:** state/ack/retry model, idempotency invariant, observable failures, tested evidence and NOT_MEASURED gaps. No live queues or production workers may be modified without approval.
