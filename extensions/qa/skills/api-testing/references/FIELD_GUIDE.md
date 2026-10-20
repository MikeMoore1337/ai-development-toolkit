# API state and failure oracles

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

POST /items is documented to create a record and GET /items/{id} exposes its state. Authorized and unauthorized principals are available.

## Procedure and decision

Record API version, actor, request, pre-state and expected side effects. Assert status, schema and business fields. For writes, read back state with a different request. Exercise malformed, absent, duplicated and unauthorized inputs where specified.

## Observable oracle

Authorized POST returns documented 201 plus a stable ID; subsequent GET reveals the created state. Unauthorized POST is denied AND leaves state unchanged. A 201 without read-back is not proof of persistence.

## Failure or exclusion

Do not invent downstream events or call a live write endpoint without approval. If no read access exists, persistence is NOT_VERIFIED, not PASS.

## Handoff contract

`case ID | role | request | expected status and state | observed status and state | evidence | result`
