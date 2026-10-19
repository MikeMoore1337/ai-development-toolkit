# Evolving an API with existing consumers

**Context:** Existing GET /orders/42 returns {"id":"42","total":100} where total is a number in minor currency units. Client v1 deserializes a numeric total.

**Candidate A (usually compatible):** keep id and total unchanged; add optional {"displayLabel":"Order 42"}. A tolerant v1 ignores the unfamiliar field, v2 may display it. Verify v1 actually tolerates extras; some strict deserializers do not.

**Candidate B (breaking):** replace numeric total with {"amount":100,"currency":"USD"} under the same field name. A v1 client expecting a number can fail at decode/runtime. Making total mandatory when it was optional (or changing null to non-null without migration) can also break producers/consumers.

**Safer plan:** add a new optional money object while retaining numeric total; deploy dual response; migrate readers; confirm version distribution and contract tests; remove old total only in a coordinated version or documented break window.

| Test | v1 with A | v2 with A | v1 with B |
| --- | --- | --- | --- |
| Decode response | PASS if tolerant | PASS if optional field handled | FAIL for numeric-total reader |
| Missing optional displayLabel | PASS | PASS with fallback | not relevant |
| Server error 409 or 422 | preserve original status and code | preserve original status and code | must not silently remap |

**Negative case:** asserting that every additive field is safe is false for strict schemas or signed payloads.

**Acceptance:** compare actual legacy client contract fixture against candidate; record error codes, rollout order, migration/rollback strategy, and evidence for every client. Unsupported runtime behavior is NOT_MEASURED.

**Limits:** Illustrative HTTP/JSON; apply equivalent compatibility reasoning to RPC or event schemas using their concrete serialization rules.
