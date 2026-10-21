# Support contracts

Fields below describe output, not an autonomous ticket store. Unknown values remain UNKNOWN. Every evidence reference needs an ID, source, actual scope, version/environment if known, and classification USER_REPORTED, SOURCE_BACKED, OBSERVED, SYNTHETIC_TESTED, INFERRED or UNKNOWN.

| Contract | Minimum fields |
| --- | --- |
| Intake | Report ID, source, received time if verified, product/component, version and environment with their evidence, symptom, expected/observed result, steps/frequency if known, impact, evidence, privacy, related issue, status, unknowns, next action |
| Classification | DEFECT, FEATURE_REQUEST, HOW_TO, CONFIGURATION, ENVIRONMENT, EXTERNAL_DEPENDENCY, SERVICE_INCIDENT, SECURITY_OR_PRIVACY, DUPLICATE, EXPECTED_BEHAVIOR, UNKNOWN; evidence, alternatives, severity, priority, user/operational impact |
| Duplicate | Issue candidate, same/different symptom, versions, environment, steps, confirmed cause if any, result SIMILAR/POSSIBLE/CONFIRMED/INDEPENDENT, proof of identity before closure |
| Reproduction | ID, Report ID, version/revision, environment, prerequisites, test data, steps, expected/actual, attempts, evidence, confidence and limits; NOT_ATTEMPTED/REPRODUCED/NOT_REPRODUCED/ENVIRONMENT_BLOCKED/INSUFFICIENT_DATA/INTERMITTENT/NOT_APPLICABLE |
| Engineering handoff | Report and Issue IDs, category, impact, reproduction, evidence, requirements R-ID/AC-ID if known, acceptance criteria, affected version, known facts vs hypotheses, scope, unknowns, risks and approvals |
| Fix check | Original failing case, code revision and PR, targeted regression, positive/negative cases, related data, explicit PASS/FAIL/BLOCKED/NOT_RUN; FIX_PROPOSED/FIX_IMPLEMENTED/TESTS_NOT_RUN/VERIFIED_PASS/VERIFIED_FAIL/BLOCKED/INCONCLUSIVE |
| Release mapping | Issue, PR, commit, build, release, deployment, channel, environment, feature flag, user installed version, staged rollout, rollback, user confirmation; every stage separately evidenced |
| Known Issue | Issue, affected versions, confirmed symptoms/triggers, impact, verified workaround and limits, fix state, approved target and actual fixed versions, release status, evidence and update timestamp |
| Changelog | Change, Issue, PR, type, component, version, user-facing effect, compatibility, limitations, actual publication status |
| Release note | Release, publication evidence, actual fixes, known limits, required user action, compatibility and distribution scope |
| Deprecation | Feature, current/proposed behavior, reason, consumers, policy, approvals, announcement, migration, only approved milestones/dates, actual removal and rollback limits |
| Support message | ID, Report ID, audience, purpose, confirmed facts, exact verified status, unknowns, draft, approval, actual send/delivery evidence |
| Lifecycle | Independent report state, fix state, distribution state, evidence history and reopen reason (without discarding prior proof) |

Report CLOSED reason is distinct from fix: ANSWERED, EXPECTED_BEHAVIOR or CONFIRMED_DUPLICATE can be valid without a release; VERIFIED_FOR_USER requires correct installed version/environment and actual user confirmation.
