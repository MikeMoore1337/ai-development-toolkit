---
name: authentication-authorization
description: "Use when implementing backend identity checks, resource permissions, session boundaries and tenant isolation."
---

# Authentication and authorization

**Use for:** backend access control implementation or correction. **Do not use for:** frontend visibility-only changes or an independent security audit (security-review/security-testing).

**Inputs:** actors, identity/session mechanisms, resource ownership, tenant boundaries, available test principals and project approvals.

1. Separate authentication (who is making the request) from authorization (whether this actor may perform this action on this resource).
2. Build an actor x action x resource matrix, including tenant and ownership checks; enforce it at trusted backend boundaries, even when frontend hides controls.
3. Reuse validated expiry, issuer/audience, revocation and permission resolution mechanisms; do not trust client-provided owner/tenant identifiers without server-side checks.
4. Return safe errors, avoid leaking existence or sensitive fields to unauthorized users, and keep tokens, cookies and personal data out of logs.
5. Test allowed, missing identity, insufficient role, foreign resource, cross-tenant and manipulated ID cases with isolated principals. Negative authorization tests must inspect denied side effects, not only response status.

**Output:** permission matrix, enforcement locations, allowed/denied test results and remaining threat assumptions. Do not change production roles or access policies without explicit approval.
