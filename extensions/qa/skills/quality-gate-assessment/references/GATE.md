# Evidence-based quality gate

| Gate | Expected evidence | Observation | Status | Owner |
|---|---|---|---|---|
| Acceptance criteria | Observable behavior mapped to requirements | Attach exact result | PASS/FAIL/NOT_RUN/UNKNOWN | Project owner |
| Regressions | Risk-focused tests | Run/commit details | PASS/FAIL/NOT_RUN/UNKNOWN | QA |
| Security | Required boundary checks | Findings or rationale | PASS/FAIL/NOT_APPLICABLE/UNKNOWN | Reviewer |
| Release | Project policy, rollback, monitoring | Explicit approval/evidence | READY/BLOCKED/UNKNOWN | Release owner |

If a required gate lacks proof, verdict is `INSUFFICIENT_EVIDENCE`, not `READY_FOR_REVIEW`. `READY_FOR_REVIEW` never means automatic deployment permission.
