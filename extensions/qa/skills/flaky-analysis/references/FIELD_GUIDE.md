# Flakiness hypothesis matrix

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

The same test passes locally and fails in some CI workers near a time boundary.

## Procedure and decision

Pin commit and environment; collect multiple independent attempts, random seeds, worker count and timestamps. Distinguish race, time zone, order-dependent fixture, eventual consistency, resource pressure and external network causes. Change one variable at a time.

## Observable oracle

After a specific cause is fixed, a repeatable stress/replay probe no longer reproduces it and neighboring deterministic assertions still fail on intentional product defects.

## Failure or exclusion

A test passing after retries does not explain the cause. Avoid blanket sleeps, disabled checks and claims of statistical confidence from two samples.

## Handoff contract

`hypothesis | differentiating experiment | attempts | observations | conclusion | unresolved variability`
