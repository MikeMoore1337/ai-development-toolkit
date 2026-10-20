# Acceptance criteria from uncertainty

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A product request says 'admins can approve refunds' without defining amounts or tenant boundaries.

## Procedure and decision

Separate known roles/business rules from open decisions. Draft scenarios for positive and negative authorization, state transitions, duplicate actions, expiry and observable results; label proposals explicitly.

## Observable oracle

Every criterion has a precondition, actor, action and observable result; a missing amount threshold remains UNKNOWN until decided.

## Failure or exclusion

Do not invent refund policy, access rights, latency objectives or declare draft scenarios approved.

## Handoff contract

`requirement ID | confirmed facts | proposed acceptance criterion | owner decision | unresolved oracle`
