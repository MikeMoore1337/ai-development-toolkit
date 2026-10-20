# Non-overlapping QA handoffs

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

Two contributors need to modify tests touching the same shared user fixture.

## Procedure and decision

Inventory owned files and the fixture schema. Serialize fixture edits under a single owner; allow separate test modules on isolated branches/worktrees only when independent. Declare merge order and integration check.

## Observable oracle

After convergence, each branch’s tests and the shared-fixture consumer regression run against the integrated tree with recorded commit IDs.

## Failure or exclusion

Do not launch parallel edits to the same path or report a second worker's review without a real separate worker.

## Handoff contract

`task | owner | files | invariant | commits | executed tests | merge conflicts | open risks`
