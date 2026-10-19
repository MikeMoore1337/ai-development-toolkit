---
name: frontend-api-integration
description: "Use when connecting frontend screens to existing API contracts, including nullability, errors, pagination and retries."
---

# Frontend API integration

**Use for:** client network calls and UI responses. **Do not use for:** changing server contract semantics (api-design), selecting a global state system or running end-to-end orchestration.

**Inputs:** actual API contract and consumers, authorization method, current transport adapter, sample success/error payloads, pagination rules and available test seams. Follow repository approval gates; never invent endpoint behavior.

1. Record fields with types, nullability, defaults, units, request identity and version; confirm who produces each value on the backend.
2. Map response classes to loading, empty, partial, validation error, unauthorized, conflict, transient error and success UI states. Missing, null and empty values may differ.
3. Keep tokens and credentials out of logs and UI. Avoid blind authentication retries; preserve typed server errors for actionable feedback.
4. For retries, identify idempotent operations or established idempotency keys. Handle cursors and partial pages without treating a partially fetched list as complete.
5. Guard against stale responses and duplicate submissions; test a successful response, 4xx, 5xx/network error, nulls, partial success and recovery as applicable. Check old/new client compatibility with backend owners.

**Output:** request/response-to-UI mapping, retry/authorization policy, client compatibility assumptions, actual evidence and NOT_MEASURED gaps.

For producer schema changes, coordinate with the separately selected api-design skill; keep the client contract and UI mapping here. Do not add a new HTTP library without a justified need and approval.
