---
name: api-testing
description: "Design API tests around contracts, state changes and failure semantics. Use for HTTP endpoints, status handling and API versioning."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Api Testing

1. Establish API contract, authentication rules, valid parameters and expected side effects.
2. Verify response structure, status and semantics; for writes also check persistent state or downstream event where applicable.
3. Test malformed/absent/duplicate inputs, boundary values, auth errors, idempotency and retries relevant to the endpoint.
4. Distinguish client- and server-side failure responsibility; do not hard-code transient identifiers or time-sensitive values.
5. Treat rate limits and third-party failures as explicit outcomes, not generic flaky failures.

Use contract fixtures; prefer targeted response assertions over whole-payload snapshots that include nondeterministic fields.
