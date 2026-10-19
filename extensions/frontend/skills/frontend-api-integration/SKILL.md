---
name: frontend-api-integration
description: "Use when implementing frontend API calls and connecting network responses or failures to UI states."
---

# frontend api integration

Inspect the actual frontend stack and project conventions before choosing tools or patterns. Follow repository rules and approval gates.

1. Read the existing API schema, authentication, transport layer and error conventions; do not invent endpoint behavior.
2. Document request/response shapes, nullability, pagination, cache ownership and compatibility expectations.
3. Map validation, authorization, transport and business errors to visible UI outcomes without exposing secrets.
4. Handle stale responses, cancellation and duplicate submissions; retry only explicitly safe operations.
5. Verify a success, a representative failure and recovery, distinguishing mocked and real integration evidence.

**Output:** Contract map, UI response handling and observed checks.
