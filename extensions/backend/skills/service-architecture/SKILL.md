---
name: service-architecture
description: "Use when changing backend module or service boundaries, ownership and dependencies."
---

# service architecture

Discover the application's actual language, framework and infrastructure first. Reuse existing conventions and respect project approvals.

1. Map entry points, domain invariants, owners, shared data and synchronous/asynchronous dependencies.
2. Identify real change pressure and operational constraints; avoid creating microservices without a measurable need.
3. Define public interfaces, data ownership, failure containment and transaction/consistency boundaries.
4. Consider compatibility, observability, deployment ordering and service failure without mandating infrastructure.
5. Verify representative contract and failure scenarios; distinguish observed runtime behavior from hypotheses.

**Output:** Service boundary map, decisions, contract evidence and operational caveats.
