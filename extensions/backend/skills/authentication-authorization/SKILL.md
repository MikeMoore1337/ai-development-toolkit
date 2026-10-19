---
name: authentication-authorization
description: "Use when implementing protected backend operations, identities, sessions and resource permissions."
---

# authentication authorization

Discover the application's actual language, framework and infrastructure first. Reuse existing conventions and respect project approvals.

1. Map actors, resources, trust boundaries, identity entry points and explicit permission matrix.
2. Enforce permissions at trusted backend boundaries; client-side visibility is not authorization.
3. Use existing token/session validation, expiry, revocation and tenant ownership mechanisms.
4. Apply least privilege, safe error messages and logging without exposing credentials, personal data or session secrets.
5. Verify allowed, denied, unauthenticated and cross-resource cases with safe test principals.

**Output:** Permission matrix, enforcement points, negative tests and unresolved threats.
