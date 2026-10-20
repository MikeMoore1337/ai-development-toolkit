# Reproducible defect report

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A user intermittently sees duplicated checkout confirmation after an interrupted request.

## Procedure and decision

Distinguish one-off report from reproduced defect. Capture environment, revision, actor, sanitized input, sequence, expected behavior, actual observation, timing and relevant evidence. Link related prior defects before creating a new issue.

## Observable oracle

A reproducer triggers the observed duplicate on a controlled fixture; failing to reproduce is recorded with attempts and environment, never silently converted into confirmed defect.

## Failure or exclusion

Do not invent severity, root cause, screenshots or linked issue IDs. Avoid leaking personal data in reproduction steps.

## Handoff contract

`summary | environment | exact steps | expected | observed | frequency | evidence | confidence | priority rationale`
