# Change impact worksheet

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A shared API field is renamed, but the diff touches only one serialization module.

## Procedure and decision

List direct callers, consumers, persistence schema, queued payloads and clients. Search using the project’s existing tools; label graph findings as observed or inferred. Map each impact to a contract and specific regression oracle.

## Observable oracle

Producer emits old and new formats only if contract demands it; every known consumer remains compatible or has a named migration. Missing graph access means coverage UNKNOWN.

## Failure or exclusion

Do not claim that a text search is a complete call graph. Do not expand to every test suite without a path from change to risk.

## Handoff contract

`changed path | affected consumer | evidence | compatibility risk | focused regression | uninspected boundary`
