# Queue and database integration contract

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A worker handles an at-least-once message and writes a ledger row.

## Procedure and decision

Use an approved isolated queue and database or explicitly declare simulated boundaries. Send duplicate and delayed messages with correlation keys. Observe durable write, acknowledgement and retry state with bounded polling.

## Observable oracle

Exactly one ledger effect occurs when idempotency is required; repeated delivery produces no duplicate and legitimate future messages still work.

## Failure or exclusion

A mocked queue plus mocked database is a component test, not proof of real integration. Do not assert exactly-once delivery absent a documented contract.

## Handoff contract

`dependency versions | real/fake boundaries | injected input | observed state | retry evidence | outcome`
