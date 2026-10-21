# Incident response, classification and handoff

## Timeline and evidence

For every event retain `incident_id`, `event_id`, `event_timestamp` (source clock), `observation_timestamp` (when recorded), `source`, `component`, `environment`, `observed_event`, `evidence`, `correlation`, `confidence`, `interpretation` and `uncertainty`. Sort by validated event time but disclose clock uncertainty. Row order never establishes occurrence order; a sequence alone does not establish causality. Do not merge production/test data or backdate executed actions. Absent evidence is explicit.

Diagnosis categories: APPLICATION_FAILURE, INFRASTRUCTURE_FAILURE, EXTERNAL_DEPENDENCY, DEPLOYMENT_REGRESSION, DATA_INTEGRITY, RESOURCE_EXHAUSTION, OBSERVABILITY_FAILURE, UNKNOWN. Severity uses affected journeys, verified impact scope, duration, workaround, data risk and urgency; count of error lines alone is not enough. Unknown impact => `IMPACT_UNKNOWN`; never invent affected user count.

Alert assessment: actual signal/owner, conditions and duration, data freshness, affected journey, deduplication key, related event evidence, severity and separately **verified** recovery. A single spike, stale sample or duplicate flood is not an independently confirmed incident. Deduplication must preserve distinct impact scopes.

## Investigation and RCA

Separate: `OBSERVED` symptom, `HYPOTHESIS`, checked `ALTERNATIVE`, `TRIGGER`, `CONTRIBUTING_FACTOR`, `ROOT_CAUSE`, `DETECTION_GAP` and `RECOVERY_LIMITATION`. Give every hypothesis a falsifiable check, disconfirming evidence, precise source link and confidence CONFIRMED/LIKELY/POSSIBLE/UNDETERMINED. Confirmed cause needs credible independent supporting evidence, not mere time proximity, a single timeout or an AI-generated narrative. Use existing `failure-triage` for detailed origin assessment.

## Status discipline

Allowed milestone vocabulary: DETECTED, INVESTIGATING, IMPACT_CONFIRMED, MITIGATION_PROPOSED, APPROVAL_PENDING, MITIGATION_EXECUTED, RECOVERY_OBSERVED, RECOVERY_VERIFIED, RCA_PENDING, RCA_COMPLETED, CLOSED. Retain dated **actual** transitions; never infer steps from their neighbors. No transition to MITIGATION_EXECUTED without an authorized and independently observed execution record. No RECOVERY_VERIFIED without stated indicators, complete periods and relevant critical user journeys. RCA_COMPLETED can legitimately conclude UNDETERMINED with documented open questions. CLOSED does not mean prevention tasks have finished.

## Operational handoff and human gate

Detection -> triage -> engineering/security review -> mitigation **proposal** -> scoped owner approval -> recorded authorized action -> recovery verification -> RCA -> prevention QA. Each proposal states expected effect, risk, reversibility, data impact, cost, owner authority and stop criteria. Release-safety owns rollback decision, security-engineering owns confidentiality and security threats, reliability-testing owns state invariants, performance-load-testing owns bounded workload measurements, QA owns regression acceptance. Do **not** autonomously restart production, switch routes, change DNS/firewall/VPS, disable workers, migrate data, apply configurations, deploy or roll back. Recommendation != approval != execution != recovery.
