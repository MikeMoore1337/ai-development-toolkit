# Synthetic delivery examples (not completed software)

## Beginner: home expenses

Source: [Product Discovery synthetic PRD](../../../../product/skills/product-discovery/references/EXAMPLES.md). All task statuses are `PLANNED`. User value and technologies are **assumptions**, no implementation, real users, timings or CI are observed.

**Plain language:** Start by agreeing how one expense is stored, then implement the first entry, then show totals, finally allow correction. Check the result before claiming it works.

| Task | R / AC | Prerequisite | Expected result and check | Risk / open decision |
| --- | --- | --- | --- | --- |
| T1 Clarify local storage | R1,R3 / AC1,AC4 | None | Confirm offline persistence approach; decision evidence | D1 storage format UNKNOWN |
| T2 Add expense and validate | R1 / AC1,AC2 | T1 BLOCKS | Entry appears; bad amount rejected without saving | K1 invalid input |
| T3 Show aggregate totals | R2 / AC3 | T2 BLOCKS | Sum matches records | K2 calculation |
| T4 Edit and remove expense | R3 / AC3,AC4 | T2 BLOCKS | Removing entry changes total correctly | K3 data loss |
| T5 Verify acceptance | R1,R2,R3 / AC1,AC2,AC3,AC4 | T3,T4 BLOCKS | QA tests all four AC including invalid amounts | K4 environment unknown |

If persistence choice is unresolved, T1 has `REQUIRES_DECISION` D1 and is `BLOCKED`; T2/T3/T4 cannot be marked ready. No fake schedule or assignee. Proposed MVP includes only manual entry, totals and correction; cloud, bank API and real data are excluded. **Next action:** decide the smallest local persistence format for a synthetic prototype.

**Risk register:** K1 invalid sums (detect: negative tests; mitigate: input validation); K2 wrong totals (detect: invariant comparing sum of records); K3 accidental deletion (detect: AC4 and empty-state tests); K4 unavailable verification environment (detect: cannot run tests; contingency: stop at NOT_RUN). Probability for all `UNKNOWN`; severity depends on actual deployment and remains an explicit review decision.

## Expert: scope change and truthful evidence

Given PRD baseline R1-R3, new R4 cloud sync is `NEW_REQUIREMENT`, not silently part of MVP. Record affected storage architecture, migration and privacy risks, task changes, revised regression checks and approval D2. Until accepted, R4 stays proposed, existing AC remain unchanged. For a PR with green checks but not merged: implementation may be `VERIFIED` if actual AC evidence was examined, never `MERGED` or `RELEASED`. A closed-unmerged PR remains not merged. A test that was not run is `NOT_RUN`, not success.

## Negative and recovery examples

- Circular BLOCKS (T1 depends on T2 and T2 on T1) → report exact cycle and stop dependent scheduling.
- Conflicting requirements (delete immediately vs never delete) → preserve both and request a blocking decision; do not invent business rule.
- Missing API contract → mark dependent client task BLOCKED, continue unrelated work.
- User says "seems done" → not VERIFIED without independently checked AC evidence.
- Github offline → label last retrieved state SNAPSHOT_NOT_CURRENT and date.
- New UI request added after MVP → compare baseline and require scope decision if material.
- One-line Python bug → use feature implementation/QA instead of this management workflow.

No Issue or PR is created from this synthetic example.
