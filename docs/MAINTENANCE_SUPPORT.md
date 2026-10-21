# Maintenance & Support (Issue #66)

[Русская версия](ru/MAINTENANCE_SUPPORT.md)

Optional `maintenance-support` adds one Operations skill and reuses QA, Management, Incident and Release skills. It is **not** a Helpdesk, CRM, separate ticket tracker, autonomous agent or delivery controller.

## User experience

Beginner: "A user says the application stopped saving after an update. Help investigate and write an accurate reply." Only ask for necessary missing version, action or environment; never invent anything. Expert: "Establish support intake, classification, deduplication, reproduction and RCA confidence, linked handoff AC, fix verification, release/version mapping, Known Issues, lifecycle notices and truthful user replies."

Categories include DEFECT, FEATURE_REQUEST, HOW_TO, CONFIGURATION, ENVIRONMENT, EXTERNAL_DEPENDENCY, SERVICE_INCIDENT, SECURITY_OR_PRIVACY, DUPLICATE, EXPECTED_BEHAVIOR and UNKNOWN. Distinguish severity, priority, user and operations impact; no manufactured counts or SLAs.

## Reuse-first matrix

| Task | Existing skills | Added support duty |
| --- | --- | --- |
| Bug description / similar symptoms | defect-management | General intake; POSSIBLE is not CONFIRMED duplicate |
| Investigation / recovery | failure-triage, observability-sre | Contradictory or non-reproduced user claims; BLOCKED access |
| Engineering / AC | project-delivery-management, requirements-traceability | Report-to-issue/PR evidence |
| Quality / publication | quality-gate-assessment, release-safety | Differentiate test, merged, release, deployed channel and user confirmation |
| Lifecycle and risks | documentation-maintenance, product-discovery, security-engineering | Scoped Known Issues, deprecation approval and privacy-safe messages |

Do not automatically declare a non-reproduced issue nonexistent, assume a shared cause from matching errors, infer root cause from one hypothesis, or claim live observations without access. A local PASS does not mean merge; merge does not mean release; release does not prove user delivery; a canary rollout may not cover the user's build. Rollback can revoke availability without losing historical QA results.

Known Issues describe affected versions and verified workarounds. Changelog captures changes, release notes describe one actually published artifact, and support messages apply to individual reports. Deprecation requires product-specific approval, notice, compatibility and migration steps - no universal retirement dates.

Replies default to DRAFT; sending, external Issues, merges and deployments need explicit separate permission. Toolkit copies used as references by another project stay read-only; no actual reports or private logs enter Toolkit.

## Offline evidence

`python scripts/validate_maintenance_support.py` and `python -m unittest tests.test_maintenance_support -v`

Five synthetic reference journeys and deliberately broken records, checked by the same independent read-only oracle. No outside network/API, production, email or user data. Real AI-client activation, live delivery, support quality and satisfaction: NOT_TESTED/NOT_MEASURED.

[Skill](../extensions/operations/skills/maintenance-support/SKILL.md) - [Contracts](../extensions/operations/skills/maintenance-support/references/CONTRACTS.md) - [Fixtures](../fixtures/maintenance-support/README.md).
