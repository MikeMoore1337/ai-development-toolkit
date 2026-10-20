# Isolated parallel test data

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

Parallel integration tests accidentally reuse the same customer email and cleanup deletes another worker's records.

## Procedure and decision

Give each worker a deterministic unique namespace and fixture ownership tag. Scope credentials, schema, isolation level, creation time and teardown. Verify cleanup targets only owned data.

## Observable oracle

Two concurrently executing tests do not collide; cleanup removes only own tagged rows, preserving an unrelated control record.

## Failure or exclusion

Do not use real personal data or global destructive cleanup without explicit authorization and safeguards.

## Handoff contract

`fixture ID | owner namespace | lifecycle | isolation contract | cleanup evidence | residual shared state`
