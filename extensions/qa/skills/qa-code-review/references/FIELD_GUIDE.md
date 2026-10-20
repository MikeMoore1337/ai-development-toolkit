# QA automation review counterexample

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A regression test compares a mock response to the mocked expected response and always passes.

## Procedure and decision

Read requirement and changed test separately; check fixtures, monkeypatching, assertions, cleanup, concurrency, and whether a product defect would cause the test to fail. Use independent mutation when authorized.

## Observable oracle

Disabling the intended production validation should break a relevant assertion; if only static review occurred, report that limitation.

## Failure or exclusion

Do not treat formatting feedback as a blocking correctness defect or silently change an expected business outcome to match code.

## Handoff contract

`path:line | mechanism | counterexample | impact | change proposal | reproduction status`
