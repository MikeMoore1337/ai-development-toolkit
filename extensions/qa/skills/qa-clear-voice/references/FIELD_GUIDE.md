# Evidence-preserving QA writing

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

The original report says '18 passed, 2 skipped, prod not checked' but wording is unclear.

## Procedure and decision

Rewrite for a human reader while keeping original counts, statuses, scope, timezone and uncertainty. Separate actual tests from planned checks and observed failures from hypotheses.

## Observable oracle

'18 PASS; 2 SKIPPED with reasons; production NOT_VERIFIED' preserves the underlying meaning and no new action is claimed.

## Failure or exclusion

Do not convert SKIPPED into PASS, invent severity or certify a legal/release decision by polishing wording.

## Handoff contract

`input source | rewritten statement | retained evidence | ambiguity requiring confirmation`
