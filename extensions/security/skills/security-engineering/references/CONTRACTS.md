# Security Engineering contracts (Issue #60)

All identifiers are local to a particular project and must link to an actual scoped system. A missing value is `UNKNOWN`, not an invented fact.

## Threat Model Contract
`threat_id, source, component, asset, actor, trust_boundary, entry_point, scenario, preconditions, potential_impact, existing_controls, proposed_controls, verification_method, related_requirement, risk_status, evidence, residual_risk, required_decision`.

Valid risk statuses: `HYPOTHETICAL, POTENTIAL, CONFIRMED, MITIGATED, NOT_VERIFIED, NOT_APPLICABLE`. Keep test execution status separate. `MITIGATED` requires confirmed mitigation evidence, not just a proposed control.

## Risk Register
`risk_id, threat_id, description, source, asset, preconditions, impact, likelihood, detectability, priority, confirmed_controls, missing_controls, owner, fix_plan, fix_verification, residual_risk, required_permissions`. Likelihood may be `UNKNOWN`. Do not assign CVSS to every architecture hypothesis. A human risk owner accepts serious residual risk.

## Verification Contract
`control_id, source, threat_id, protected_asset, trust_boundary, invariant, expected_allow, expected_deny, forbidden_side_effects, level, scenario, actual_evidence, status, limitations, responsible_decision, residual_risk`.

The invariant must describe actor, resource, action, ownership scope and observable result. Expected ALLOW and DENY behavior must both be meaningful. `PASS` requires executed evidence; `NOT_TESTED` for unexecuted verification.

## Acceptance Finding
`finding_id, threat_id, component, source_location, evidence_classification, observed_behavior, expected_invariant, reproduction_conditions, impact, confidence, priority, minimal_fix, verification_plan, actual_status, residual_risk`.

Evidence classes: `NOT_TESTED, SOURCE_ONLY, STATIC_VALIDATED, SYNTHETIC_TESTED, REAL_TESTED, HUMAN_REVIEWED`. Record scope and revision. Synthetic unit tests cannot be marked `REAL_TESTED` or `HUMAN_REVIEWED` by the test runner.

## Example: two-owner fictional notes
Assets: private notes, authorizations; actors: user-A, user-B, anonymous; boundaries: client -> trusted service -> notes store. Owner A may read/update/delete own tenant-A note; B may do the same for tenant-B. A -> B note = DENY with unchanged store. Expired session -> DENY. Client-provided owner ID has no authority. No actual HTTP or third-party accounts are involved.

For each remediation: `Finding -> Risk -> Minimal Fix -> Negative Regression -> Verification -> Residual Risk`. Keep legitimate ALLOW functioning, and verify effects as well as status.
