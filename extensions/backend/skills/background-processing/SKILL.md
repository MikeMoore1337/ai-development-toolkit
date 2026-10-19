---
name: background-processing
description: "Use when implementing queues, workers, scheduled tasks and asynchronous backend processing."
---

# background processing

Discover the application's actual language, framework and infrastructure first. Reuse existing conventions and respect project approvals.

1. Identify the existing trigger, runtime, duration, workload, retry strategy and job visibility.
2. Document actual delivery and ordering guarantees; never claim exactly-once delivery without end-to-end proof.
3. Define idempotency, deduplication, cancellation, deadlines, backoff and poison-item handling as applicable.
4. Keep progress/failure states observable, bound retries and protect private payloads in logs.
5. Test duplicate delivery, transient and permanent failures, worker shutdown and partial side effects.

**Output:** Job states, delivery guarantees, retry and idempotency policy, observed checks.
