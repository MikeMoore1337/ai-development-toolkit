---
name: maintenance-support
description: "Manage customer reports, issue classification, duplicate checks, reproduction evidence, fix and release status, known issues, deprecation and accurate support replies. Not for isolated coding, failed CI, incident RCA or deployment."
metadata:
  pack: "operations"
  version: "1.0.0"
---

# Maintenance & Support

Use for "handle a user complaint", "is the fix available to this customer?", "prepare known issues", "write an accurate bug update", «обработай обращение», «проверь доставку исправления», «подготовь ответ пользователю». Do **not** activate for a standalone Python fix (implementation), failed CI (failure-triage), creating just a bug report (defect-management), live incident (observability-sre), security audit (security-engineering), feature planning (product-discovery) or publishing a release (release-safety).

1. **Intake** - preserve original user symptoms, expected/observed behavior, source, privacy and unknowns. Ask a novice only the smallest useful question, not for technical details they cannot know. Do not invent version, time, environment, logs, root cause or owner. See [contracts](references/CONTRACTS.md).
2. **Classify** - DEFECT / FEATURE_REQUEST / HOW_TO / CONFIGURATION / ENVIRONMENT / EXTERNAL_DEPENDENCY / SERVICE_INCIDENT / SECURITY_OR_PRIVACY / DUPLICATE / EXPECTED_BEHAVIOR / UNKNOWN. Keep severity distinct from priority and impact. Similar symptoms are not proof of a duplicate.
3. **Investigate carefully** - record attempts, version, environment, competing explanations, contradictory reports, missing access and evidence type (USER_REPORTED / SOURCE_BACKED / OBSERVED / SYNTHETIC_TESTED / INFERRED / UNKNOWN). NOT_REPRODUCED is not disproven. An inference is not confirmed RCA. See [workflow](references/WORKFLOW.md).
4. **Reuse existing skills** - defect-management for reproduced bugs; failure-triage for CI and origin; observability-sre for production incidents; project-delivery-management and requirements-traceability for handoff; quality-gate-assessment for tests; release-safety for release and rollback. No second Helpdesk, Issue Tracker or feature controller.
5. **Track independent axes** - report, fix/QA, merge, published release, deployment channel, user-visible version and user confirmation. Each status requires its own proof. Rollback must re-evaluate current availability without erasing old evidence. A green CI run does not prove production deployment.
6. **Communicate** - maintain Known Issues and scoped changelog/release notes. Deprecation requires approvals and accurate notices; never invent SLA, retirement dates or guaranteed fixes. Customer replies begin as DRAFT, not SENT. See [messages](references/MESSAGES.md).
7. **Honor scope** - when Toolkit is referenced from another project, all copies are read-only; default output stays in chat. Do not save user reports, emails, logs, secrets, or third-party results in Toolkit. External tracker writes, sending, merge, deployment and rollback require separate authorization.

Offline example: `python scripts/validate_maintenance_support.py` and `python -m unittest tests.test_maintenance_support -v` from an authorized Toolkit checkout. These tests are fully fictional and do not establish real user satisfaction or model skill activation. [Worked cases](references/EXAMPLES.md).
