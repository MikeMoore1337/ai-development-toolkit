# Rollback and evidence gates

Before update: record original source SHA, manifest, lockfile and resolved graph revisions, package origins/integrity, toolchain/runtime, configuration, data migrations, deployment artifact and known-good tests.

Rollback contract: what is reverted, exact versions, how to reinstall previous resolution, old manifest/lockfile/source revisions, config and data-format migration compatibility, repeatability, verification tests, owner gate, status and forward-fix when blocked.

**Git revert is not a deployed dependency rollback. Dependency rollback is not data rollback. Restoring a lockfile is not proof of restored production.** Incompatible persistent data changes require ROLLBACK_BLOCKED rather than false promises; use a forward-fix strategy with explicit authority.

Evidence contract: assessment_id, source_sha, package identity and versions, lockfile_revision, upgrade_reason, advisory_provenance, compatibility, full diff, actual tests and environment, limitations, approval evidence, change status, rollback readiness and release status.

Valid stages with evidence: INVENTORIED, ASSESSMENT_PREPARED, CHANGE_PROPOSED, CHANGE_APPLIED_LOCALLY, TESTED, READY_FOR_REVIEW, MERGED, RELEASED, ROLLBACK_REQUIRED, ROLLED_BACK, BLOCKED. A proposal cannot silently become APPROVED; READY_FOR_REVIEW is not authorization; MERGED is not deployment; ROLLED_BACK is not independently verified recovery.

Following an authorized real upgrade, use observability-sre for factual application health/error rates, latency, workers, resource regressions and affected journeys. Change assessment, test regression, observed production impact and rollback decision are separate evidence stages. No scheduled monitor or production operation is part of this skill.

For external users Toolkit copies are read-only. Return the report to chat by default; write only at an approved destination. Never export secrets or private lockfiles into public Toolkit.
