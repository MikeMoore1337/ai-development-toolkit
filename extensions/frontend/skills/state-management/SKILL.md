---
name: state-management
description: "Use when assigning frontend state ownership or fixing synchronization, stale results, optimistic updates and caching."
---

# State management

**Use for:** inconsistent UI state, overlapping requests, derived values or cache ownership. **Do not use for:** API schema evolution (api-design), isolated form rules (forms-validation) or general delivery orchestration.

**Inputs:** user action and expected screen, current state owners, async operations, concurrency assumptions and available test environment. Inspect the existing stack and repository approval gates; do not require a new state library.

1. Identify one source of truth for UI, URL, server and persisted state. Derive display values instead of duplicating mutable copies.
2. Map events to states (idle/loading/success/error), including navigation and cancellation. Give each async request a version or current-key guard so an older result cannot overwrite a newer intent.
3. For conflicting writes, distinguish cancellation of a read from server-side conflict prevention. Define optimistic update, acknowledgement, reconciliation and rollback; handle failure after the user moves away.
4. Choose local primitives first. Introduce shared stores, cache invalidation or deduplication only for observed shared ownership problems.
5. Verify reverse-order completions, rapid repeated actions, remount, failed writes and recovery with the project test tools. A cancelled request is not proof that a remote mutation was undone.

**Output:** ownership table, transition map, stale-result/conflict policy, tested cases with evidence and untested cases marked NOT_MEASURED.

See [reverse-order response example](references/stale-response.md) when requests can overlap. No production mutation or dependency installation without approval.
