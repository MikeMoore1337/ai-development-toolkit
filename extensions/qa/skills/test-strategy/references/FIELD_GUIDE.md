# Cost-aware QA layering decision

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

A single-service CRUD API has limited CI minutes; a different project uses several independently deployed services.

## Procedure and decision

List actual critical paths, failure costs and dependencies. Choose the cheapest observable oracle for each: unit, API, contract, integration, E2E or exploratory. Say which layers are deliberately omitted.

## Observable oracle

Single-service scenario proves validation and create/read via unit/API/DB test without inventing a provider contract; distributed services add contract checks where consumers actually exist.

## Failure or exclusion

Do not mandate a universal pyramid or full browser coverage. Do not label a planned test executed.

## Handoff contract

`business risk | selected layer | oracle | CI frequency and budget | excluded layer/rationale | owner`
