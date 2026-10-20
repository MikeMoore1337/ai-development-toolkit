# Optional dependency graph inspection

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

An approved code graph tool is available to inspect service callers, but another user has only plain source files.

## Procedure and decision

Confirm tool access and repository scope; request only the necessary symbol/caller graph. Cross-check paths against source. Without graph access use targeted search, public contracts and project documentation; disclose coverage.

## Observable oracle

Impact statements cite actual symbol path and consumer plus source evidence; fallback output is explicitly bounded to inspected files.

## Failure or exclusion

Do not install a graph provider, send private source away or claim complete reachability from a grep result.

## Handoff contract

`entry point | observed callers | inferred edges | source evidence | uncovered modules`
