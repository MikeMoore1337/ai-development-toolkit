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

## Evidence and completion contract

Apply to API behavior and contracts, not a UI-only visual change or an unapproved production write. Establish endpoint, contract/version, auth role, fixture, initial state, expected outcomes, permissions and a reproducible oracle. Stop before destructive writes without approval.

For each scenario record: request/method and redacted relevant input; expected and **actually observed** response status, fields and semantics; persistent-state read-back when writes should mutate state; and downstream side effects **only when the contract specifies them**. Attach observed values, trace or record reference, environment and observation window, plus confirmed defects. A 200/201 alone never proves persistence or event delivery. Do not expose tokens or full sensitive payloads.

Mark each assertion `PASS` when executed and satisfied, `FAIL` when executed and contradicted, `SKIPPED` with the reason for intentional omission, or `NOT_VERIFIED` when evidence/access is missing. Unchecked results never count as PASS. A test set is complete only when in-scope assertions have these explicit outcomes, cleanup is addressed, and required checks have passed or verified failures and blockers are disclosed. If required evidence is missing, overall `INCOMPLETE`, not success.

Illustration, **not executed evidence**: `POST /orders` with authorized `order=A` expects `201`, an ID and read-back state `created`; one `order.created` event is expected **only if documented**. Example report: response `PASS (201, id observed)`; DB read-back `PASS (created)`; event `NOT_VERIFIED (no subscriber or event log access)`; overall `INCOMPLETE`. For `GET /orders/unknown`, expected `404` and documented error shape are a passing negative test when the assertions succeed. Where appropriate verify no unexpected mutation.

For asynchronous side effects, poll with a correlation key and a **bounded timeout** only when such a channel exists; report timeout vs inaccessible observer accurately. Do not invent events, arbitrary sleeps or a successful assertion for anything not observed.
