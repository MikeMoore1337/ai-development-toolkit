# Minimal change to shared fixtures

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A shared authenticated-user fixture must accept another role without breaking existing tests.

## Procedure and decision

Inventory consumers, data lifetime and side effects. Plan minimum compatible change and migration only if needed. Verify old and new consumers, isolated fixture cleanup and CI invocation.

## Observable oracle

Tests for old role and new role both exercise their intended account permissions and leave no shared mutable test state.

## Failure or exclusion

Do not edit golden snapshots or project-level policies without explicit approval; do not claim release ready from a local fixture test.

## Handoff contract

`change boundary | existing consumers | modified files | observed regressions | rollback plan`
