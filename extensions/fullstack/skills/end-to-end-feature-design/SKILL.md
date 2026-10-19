---
name: end-to-end-feature-design
description: "Use when designing a user-visible vertical feature slice through UI, API and persistence."
---

# end to end feature design

Inspect the existing project boundaries, technology and deployment constraints before proposing a change. Follow project approval gates.

1. Describe the user outcome, roles, primary interaction, acceptance examples and exclusions.
2. Map the vertical slice across interface, transport, service and persisted state using existing architecture.
3. Specify success, empty, loading, invalid, unauthorized, conflict and recovery paths where relevant.
4. Determine contract compatibility and release ordering; do not introduce a new language or framework by default.
5. Map each acceptance example to testable evidence, and use one existing feature-delivery controller for overall task orchestration.

**Output:** Slice map, cross-layer contracts, acceptance-to-evidence map and open decisions.
