# Cross-tenant authorization checks

These are synthetic, stack-conditional examples, not executed project evidence. Inspect the target repository, actual contract, tool version and permissions before applying. Keep Toolkit copies read-only when operating on another project; put reports in chat unless an output location is explicitly requested. Record unavailable evidence as NOT_VERIFIED/NOT_RUN, never PASS.

## Worked situation

User A and user B each own a private invoice and the API accepts an invoice ID.

## Procedure and decision

With authorized nonproduction principals and fixtures, test own-ID success, foreign-ID deny, unauthenticated deny, revoked permission and non-mutation for forbidden writes. Check server-side response and state.

## Observable oracle

User B cannot fetch or modify user A's invoice even by guessing the ID; legitimate user A operations still succeed.

## Failure or exclusion

UI invisibility is not authorization. Do not send security probes to unapproved hosts or use real customer accounts.

## Handoff contract

`policy | actor | object | request | expected deny/allow | state-readback | observed result`
