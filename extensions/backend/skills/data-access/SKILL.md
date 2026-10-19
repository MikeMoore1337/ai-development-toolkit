---
name: data-access
description: "Use when designing backend data access queries, transaction scopes, storage integrity and concurrency."
---

# data access

Discover the application's actual language, framework and infrastructure first. Reuse existing conventions and respect project approvals.

1. Discover storage engine and model, owner, consistency guarantees and transaction capabilities.
2. Define invariants and where they are enforced; prevent duplicate and partially committed mutations.
3. Use safe parameterized interfaces, check permissions and exposure, pagination and query shape.
4. Check concurrency, conflict handling, rollback, retry behavior and representative data volumes.
5. Measure slow paths and validate missing records, conflict and partial-failure handling using isolated data.

**Output:** Persistence contract, concurrency/integrity risks, query evidence and tests.
