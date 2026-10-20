# Cross-boundary journey oracle

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

An authenticated buyer submits an order through a UI that calls an API and stores an order.

## Procedure and decision

Specify a critical user path and final business state. Drive the actual UI with stable interactions, observe persisted/API result through approved channels and check failure recovery. Isolate test data and define cleanup.

## Observable oracle

After confirmation the created order is retrievable by the buyer and inaccessible to another account. A green UI toast alone does not prove the order exists.

## Failure or exclusion

Do not call a single HTTP request an E2E journey or require browser automation for a headless service.

## Handoff contract

`journey | layers crossed | observed final state | evidence | clean-up | status | unverified layer`
