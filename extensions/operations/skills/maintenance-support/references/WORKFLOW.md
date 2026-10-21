# Evidence-led workflow

User report -> intake -> classification -> duplicate candidate -> authorized reproduction -> diagnosis with falsifier -> engineering issue with acceptance -> implementation and QA -> merge -> release -> environment/channel distribution -> user-specific reply -> closure.

| Requirement | Reused skill | Specific support gap |
| --- | --- | --- |
| Bug and possible duplicate | defect-management | General user intake; POSSIBLE != CONFIRMED |
| Reproduction / RCA | failure-triage, observability-sre | Conflicting reports, unknown cause, access BLOCKED |
| Issue, AC and ownership | project-delivery-management, requirements-traceability | Report-to-implementation links; no invented owner |
| QA result | quality-gate-assessment | Original failing test and targeted regression |
| Merge/release/rollback | release-safety | User version and channel availability after staged rollout |
| Feature, privacy, deprecation | product-discovery, security-engineering, documentation-maintenance | Explicit approval, notices and reply status |

Each of these requires **separate evidence**: REPRODUCED (attempt/observed output); FIX_IMPLEMENTED (revision); QA_VERIFIED (executed test at revision); MERGED (target-branch merge); RELEASED (published artifact with included fix); DEPLOYED (version, channel, environment); USER_VERIFIED (specific user scenario and version). Rollback execution is not rollback planning. Changelog publication is not delivery. Old tests remain historical evidence even when deployment is rolled back.

Identify possible duplicates by symptom, affected component/version, environment, trigger and confirmed cause (if any). Same words can hide independent defects; regression in later version can require reopening. Keep both contradictory user statements with distinct scopes. Do not call an untested hypothesis CONFIRMED. When no logs or production access, avoid observed claims and request minimum needed detail.

All real external operations need owner-scoped permission. An Issue draft is not an Issue creation; a message draft is not SENT. No mandatory external Helpdesk or paid runtime.
