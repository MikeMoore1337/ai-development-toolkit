---
name: state-management
description: "Use when selecting or changing frontend state ownership, synchronization, derived values and caching."
---

# state management

Inspect the actual frontend stack and project conventions before choosing tools or patterns. Follow repository rules and approval gates.

1. Classify state by lifetime and source of truth: UI, URL, server, session or persisted preference.
2. Keep mutable state at its narrowest owner; derive data rather than store duplicated mutable values.
3. Define async transitions, stale responses, cancellation, concurrent updates and rollback where applicable.
4. Use existing state primitives and justify global stores or caching layers with a concrete need.
5. Test remounts, navigation, racing requests, invalidation and recovery using available project tooling.

**Output:** State ownership and transitions, consistency risks and evidence.
