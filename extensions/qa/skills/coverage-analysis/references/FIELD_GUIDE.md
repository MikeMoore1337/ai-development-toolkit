# Risk-based coverage gap analysis

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A payment permission check has 96% line coverage but no test with a second customer's ID.

## Procedure and decision

Map critical requirements, actor/state partitions and negative actions to actual assertions. Record whether tests run, only exist, or cannot observe side effects. Rank gaps by plausible failure consequence.

## Observable oracle

Unauthorized cross-account read and write attempts fail at the resource boundary and preserve protected state; coverage percentages are supporting data only.

## Failure or exclusion

Do not equate unexecuted test names, mocks or high line coverage with proven behavior.

## Handoff contract

`risk | requirement | evidence-backed tests | missing observable case | priority | proposed owner`
