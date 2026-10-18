---
name: security-testing
description: "Derive negative security tests for permissions and trust boundaries. Use when access rules, session behavior, user data or agent actions change."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Security Testing

1. Map actors, protected resources, trust boundaries and actions before selecting tools.
2. Verify authorization at the protected resource, not just UI visibility; include cross-tenant/object IDOR, missing permissions, expired sessions and replay where relevant.
3. Test malformed inputs, rate limits, secret exposure and unsafe tool argument handling proportionally to product risk.
4. Use test accounts and approved environments; do not probe real third-party systems without authorization.
5. Check that failures are observable without leaking sensitive details. Record which scenarios were not executed.

Evidence must tie each test to an explicitly documented policy or threat. No automated red-team activity without authorization.
