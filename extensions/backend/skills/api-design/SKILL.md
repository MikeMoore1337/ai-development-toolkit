---
name: api-design
description: "Use when defining or evolving server HTTP, RPC or message contracts while preserving consumers."
---

# API design

**Use for:** new endpoints, payload changes, errors, lifecycle or compatibility. **Do not use for:** frontend-only mapping of an existing API (frontend-api-integration) or independent contract test implementation (contract-testing).

**Inputs:** real producer schema, deployed consumer versions, transport, error conventions, validation, auth and rollout constraints. Inspect existing code and approvals before proposing changes.

1. List producers and existing clients; specify requests, responses, field types/nullability, status and error semantics with concrete examples.
2. Compare old and candidate schemas explicitly. Additive optional fields may be compatible for tolerant readers; changing a required field, type or meaning is not silently safe.
3. Define side effects, idempotency, ordering, timeout, retry, pagination and authorization as relevant.
4. Plan expand/adapt/deprecate ordering when clients deploy independently. Keep old behavior while legacy readers exist; document when removal is safe.
5. Verify old and new consumer fixtures against the candidate. Include positive, malformed, unauthenticated, forbidden and conflict cases where relevant; use contract-testing for implementation of dedicated QA suites.

**Output:** contract diff, compatibility matrix by consumer, migration/rollback constraints and executed vs unexecuted evidence.

See [compatible and breaking API evolution](references/compatible-evolution.md). No production API rollout without approval.
