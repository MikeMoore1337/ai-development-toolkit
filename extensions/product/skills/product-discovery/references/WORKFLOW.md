# Product Discovery workflow

1. Reuse `task-scoping` for project constraints and acceptance boundaries; `research-verification` for external claims; `requirement-analysis` only when formal requirement traceability is needed; `architecture-decisions` only after an actual high-impact technical decision exists. Product Discovery owns **which users/problems/MVP/value**, not how to implement software.
2. Establish an evidence ledger: `claim | status | provenance/date | confidence/limitations | next test`. `USER_PROVIDED` is an attributed report, not independent validation. `OBSERVED` requires actual permitted observations. A citation alone does not prove a market hypothesis.
3. Identify a single first segment and journey (trigger, current workaround, friction, desired outcome). Treat personas without interviews as hypothetical; avoid invented demographics. When the input says "AI for everyone", propose one narrowly scoped segment as a testable assumption and identify the blocker.
4. Build a hypothesis backlog: `H-ID | segment | problem | change | expected outcome | measure | falsifier | cheapest permitted test | status`. For example: "If recurring expenses can be entered in one step, the synthetic task is completable without a tutorial" is a **design hypothesis**, not observed user benefit. User outcomes must be validated by actual users before calling them proven.
5. Scope the MVP around one end-to-end user result. Define in/out explicitly. Prioritize into `must now`, `after MVP validation`, `not needed`. Numeric Impact/Confidence/Effort is `UNKNOWN` unless defensible evidence exists. Identify explicit conditions for rescoping.
6. Map requirements `R-ID -> AC-ID -> verification method`. Acceptance criteria describe observable behavior: initial state, user action, result, failure/recovery path. Mark `PENDING_DECISION` if verification cannot yet be defined.
7. Only choose metrics that support a product decision. Specify numerator/denominator for rates, event eligibility, measurement window, baseline or UNKNOWN, target as PROPOSED when suggested, actual as NOT_MEASURED until measured, source, data quality, responsible person if known, and next decision threshold. When tracking might use medical/financial/personal data, first assess necessity and consent; offer aggregated anonymous or synthetic prototype validation.
8. Assemble the 14 PRD sections listed in `PRD_CONTRACT.json`; include evidence and hypothesis ledger, priority and traceability. Technical plan, API schemas, a delivery schedule, UI kit or executable application are explicitly **not created**.
9. Handoff summary for #54/#55/#56 should point to the same stable requirement/hypothesis IDs and acknowledge unknowns. If request has insufficient evidence, deliver `DRAFT_WITH_ASSUMPTIONS` and a specific validation task, not `VALIDATED`.

## Recovery and output destination

- Contradictory requirements: preserve both, flag conflict, ask only a decision that blocks the MVP.
- No internet: `SOURCE_BACKED` stays empty unless genuine provided sources exist; do not invent competitive analysis.
- No baseline: `UNKNOWN`; suggested target: `PROPOSED`; actual: `NOT_MEASURED`.
- No power to interview: propose a script/sample *only*, never say interviews happened.
- When Toolkit is merely a referenced guidance repository, default to chat. Do not write a user's files anywhere inside any Toolkit copy. Writing a new user-project file requires explicit user request and permitted destination.
- User asks only for a bug fix or API implementation: do not activate this workflow.
