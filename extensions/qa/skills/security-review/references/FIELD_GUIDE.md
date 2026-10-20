# CI and QA repository trust review

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A workflow runs on untrusted pull requests while a job has write permissions and accesses environment secrets.

## Procedure and decision

Map trigger, actor, token scope, checkout revision, untrusted inputs, command interpolation, dependency sources and artifacts. Identify exploit prerequisites with actual workflow evidence, then propose least-privilege edits.

## Observable oracle

Untrusted PR execution cannot read or modify privileged assets; trusted release behavior remains available with explicit authorization.

## Failure or exclusion

Do not execute an exploit in production or claim a vulnerability based solely on a tool's label. Separate confirmed reachability from hypothesis.

## Handoff contract

`boundary | affected file/line | attack preconditions | evidence | verified risk status | mitigation test`
