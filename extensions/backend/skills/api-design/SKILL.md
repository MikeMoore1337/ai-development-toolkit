---
name: api-design
description: "Use when defining or evolving server-side HTTP, RPC or message API contracts and compatibility."
---

# api design

Discover the application's actual language, framework and infrastructure first. Reuse existing conventions and respect project approvals.

1. Identify actual consumers and transport, naming, error, pagination, authorization and versioning conventions.
2. Define request/response shape, nullability, validation, errors and examples reflecting real implementation.
3. Make side effects, idempotency, ordering, timeouts and retry expectations explicit where relevant.
4. Assess old clients and plan additive migration or deprecation rather than silent breakage.
5. Test successful, invalid, unauthorized and conflicting operations; use contract-testing separately for QA automation.

**Output:** Contract diff, compatibility rationale, migration notes and evidence.
