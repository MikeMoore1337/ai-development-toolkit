# Cross-functional handoff without automatic approval

| From → To | Carry forward | Explicitly unresolved |
| --- | --- | --- |
| Product → Delivery | Goal, PRD, MVP in/out, R-ID, AC-ID, evidence labels, hypotheses | Unvalidated hypotheses and product decisions |
| Delivery → Analyst | Deliverables, original R/AC IDs, priorities, dependency/blocker graph | Missing business rules; no invented behavior |
| Analyst → Designer | User journeys, interaction requirements, error/empty states, constraints | Unconfirmed rules and state details |
| Designer → Engineer | Approved scenarios, actual interface/component contracts if available, responsiveness, AC | Screens and decisions not yet approved |
| Engineer → QA | Actual diff/HEAD, R/AC links, checks, known limits, reproducible setup | Untested paths and failed checks |
| QA → Delivery | AC evidence, PASS/FAIL/NOT_RUN, defects, blockers, quality assessment | Owner review and release approval |

A handoff is information transfer, not proof of work, no implied delegated authority. Keep GitHub as the source of truth if it is in use. Issue creation, merge, release and deployment require explicit authorization and applicable gates. If no actual artifacts exist, put `UNKNOWN` / `NOT_PROVIDED` rather than inventing them.
