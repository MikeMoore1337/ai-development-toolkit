# Provider-consumer compatibility

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A provider adds `status` to a JSON event consumed by independently deployed workers.

## Procedure and decision

Capture actual producer and consumer schema revisions. Test required vs optional fields, enum additions, nullability, defaults, backward/forward compatibility and versioning rules using recorded fixtures.

## Observable oracle

Old consumer accepts the compatible additive event; removing a required field produces a failing consumer-contract assertion.

## Failure or exclusion

A passing provider unit test is not consumer compatibility. Do not invent a contract or require Pact where no provider/consumer contract exists.

## Handoff contract

`producer version | consumer version | field change | contract rule | evidence | compatible/breaking/unknown`
