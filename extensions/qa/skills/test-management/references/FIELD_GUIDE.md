# Stable case identity and reconciliation

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

One parameterized test is renamed and one scenario is split into two distinct behaviors.

## Procedure and decision

Read existing requirement and test management IDs. Preserve stable ID for unchanged behavior despite file renames; assign new IDs to genuinely new behaviors. Produce dry-run reconciliation before external sync.

## Observable oracle

Every external case maps to one intentional behavior and revision; duplicate mapping and stale test links are reported, not silently rewritten.

## Failure or exclusion

Do not invent Jira/Test IT IDs or silently create remote cases when credentials or permission are missing.

## Handoff contract

`source ID | old test | new test(s) | same/changed behavior | sync action | approval status`
