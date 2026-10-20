# Synthetic cases - not actual user research

All figures, users and scenarios below are **synthetic**. They do not claim real demand, market size, interviews or measured conversion.

## A. New app - household expenses (beginner, incomplete input)

**Input:** "I want a simple app for home expenses." Segment: `ASSUMPTION` = a person who wants a manual view of household spending. Unknowns: whether this user wants shared accounts; what record keeping they currently do.

**Evidence:** `USER_PROVIDED`: an app idea. `UNKNOWN`: pain severity, frequency, alternatives, market, willingness to pay. `OBSERVED`: none.

**Hypothesis H1 (UNTESTED):** If a person can record an expense with amount/category/date and immediately see a category total, they can complete the primary tracking task. Measure: user-task completion in a consented prototype study; falsifier: participants cannot complete without external guidance. Minimum test: clickable prototype or local paper flow with voluntary testers, no real expense data.

**MVP - must now:** manual entry (amount, category, date); view current totals; correct or remove an entry. **After validation:** recurring entries. **Not needed:** bank synchronization, sign-in, paid API, cloud or analytics dashboards. Constraint: use synthetic values for demos; avoid collecting real financial details. Rescope if shared spending is actually the core user task.

**PRD (DRAFT_WITH_ASSUMPTIONS)**

1. **Title:** Manual expense journal.
2. **Context/problem:** Tracking expenses is the proposed pain point; not empirically verified.
3. **Target users:** One individual logging own spending (ASSUMPTION).
4. **User jobs:** Record expense; review total by category; correct mistake.
5. **Evidence/assumptions:** see ledger above; no interviews performed.
6. **Objective:** Provide one usable manual expense-recording flow.
7. **MVP in:** Add, list, aggregate and correct/delete records.
8. **Functional requirements:** R1: add an expense with amount/category/date; R2: display totals; R3: edit/delete.
9. **Non-functional constraints:** no external services or real personal data in prototype; accessible error feedback.
10. **Acceptance criteria:** AC1 for R1: given an empty list, entering valid amount/category/date shows the entry and updates the total. AC2 for R1: invalid/blank amount is rejected without creating an entry. AC3 for R2: totals equal the sum of displayed entries after edits/deletions. AC4 for R3: deleting one item removes it and updates totals.
11. **Metrics:** Task completion = completed prototype scenarios / attempted eligible scenarios, unit %, event = consented test results, baseline UNKNOWN, target PROPOSED (choose after pilot), actual NOT_MEASURED, period = pilot sessions, verification = inspect task logs, owner UNKNOWN, limitation = small synthetic sample not population behavior.
12. **Risks/dependencies/questions:** offline persistence choice TBD; shared budget needed? Study must be authorized.
13. **Explicit exclusions:** bank API, subscriptions, account system, live user profiling.
14. **Next action:** Validate the one manual flow with a consenting target participant and revise hypotheses; not implementation or market-fit proof.

**Handoff:** #54 objective/scope/AC1-AC4; #55 R1-R3 rules and totals; #56 first-run add/view/edit journey. No schedule, API design or UI kit supplied.

## B. Existing product - feature proposal

**Input:** "Add recurring tasks to my existing to-do app." First inspect stated existing capabilities; if unavailable mark UNKNOWN. Product hypothesis: one-click recurring creation reduces repetitive input, `UNTESTED`. MVP: one fixed repeat interval and visible next instance; exclude calendar sync and notifications. PRD: describe R1 / AC1 next occurrence creation and AC2 safe cancellation. Do not edit the app or pretend user interviews exist. Handoff should mention current-data-model dependency as unresolved, not prescribe schema changes.

## C. Inadequate segment

**Input:** "AI app for everyone." Do not claim "everyone" is a target segment, invent TAM/SOM/revenue or select a paid API. A hypothesized initial segment could be freelancers summarizing their own non-sensitive notes, if allowed. Ask what concrete job must be completed and what information will be handled; until then mark product `DRAFT_WITH_ASSUMPTIONS`.

## D. Negative activation

**Input:** "Fix my broken Python API endpoint." Route to engineering/QA, NOT Product Discovery; existing product decision is not being requested.

## E. Sensitive data

**Input:** "Medical diary of patient symptoms." Mark regulatory/privacy/legal assumptions `UNKNOWN`. Do not collect personal health records; propose a local synthetic prototype and a specialist privacy/regulatory review before any live study.
