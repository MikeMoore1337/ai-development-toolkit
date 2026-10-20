# Can this test catch a regression?

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A POST /orders test asserts only 200 although the feature must persist a unique order.

## Procedure and decision

Trace acceptance criterion to setup and assertion. Ask what intentional broken implementation still passes. Examine fake boundaries, timeouts, broad matches, skipped assertions and result data. Run a negative probe only if authorized.

## Observable oracle

Removing the persistence step makes the test fail because read-back is asserted; otherwise report a false-pass gap.

## Failure or exclusion

Do not self-label a review independent when the same agent authored and reviewed the tests. Do not hide unverified behavior.

## Handoff contract

`test ID | requirement | false-pass counterexample | verification action | severity | review independence`
