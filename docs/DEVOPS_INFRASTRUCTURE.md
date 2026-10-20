# DevOps & Infrastructure (Issue #61)

[Русская версия](ru/DEVOPS_INFRASTRUCTURE.md)

The optional provider-neutral `devops-infrastructure` skill helps examine real CI/CD, container and Infrastructure as Code (IaC) configurations, separate environments and plan safe deployments. It is not a CI orchestrator, a deployment engine or another release/security skill. Docker, Kubernetes, Terraform, paid APIs and cloud accounts are **not** required.

## Beginner - start by asking in plain language

> Help configure automatic checks and a safe release process for my current application. Inspect what already exists, prefer free tools and do not install Docker or deploy anything without my explicit approval.

**CI** runs automated checks against a specific source revision. **CD** organizes delivery and possibly deployment. Building an artifact is not deploying it. Containers bundle an application runtime, but many local applications require no container or server.

## Steps and gates

1. Inventory the project's actual language, build/test commands, CI, existing environments, data, migrations, permissions and recovery mechanism. Classify findings CONFIRMED, ASSUMED, UNKNOWN or NOT_APPLICABLE; do not invent infrastructure.
2. Reuse `security-engineering`, `database-migrations`, `reliability-testing` and `failure-triage` where relevant. Preserve existing CI workflows and avoid another controller.
3. Design a minimal pipeline: exact SHA, trigger/trust, dependency validation, stages with pass/fail oracles, required checks, permissions, secret *references*, immutable artifact provenance/SHA256, evidence and environment gates.
4. Only inspect containers if used or requested: base image and build context, secrets, user, startup, health and resource assumptions. Reviewed Dockerfile != image built != container running != deployment verified.
5. For IaC distinguish current state, desired state, diff/deletions/cost, syntax check, real provider plan, explicit approval, apply and verified result. A synthetic IaC plan does not attest real state.
6. Check environment ownership, trust, data, secrets, limits and cost; staging may share production resources despite its name. Fail closed if an environment is unknown.
7. Prepare deployment ID, target/owner, exact artifact, dependency and schema migration order (expand/migrate/contract), strategy, prechecks, stop conditions, health/smoke checks, monitoring, rollback/forward-fix and evidence. Hand readiness to existing `release-safety`.
8. Do not advance from PLAN_VALIDATED to APPLY_AUTHORIZED without specific authorization. Green CI, successful dry-run or merged PR never imply APPLIED or POST_APPLY_VERIFIED.

**Recovery:** code rollback does not reverse data migration. A backup's existence does not establish successful restore; a real restore test is separate evidence. Record SOURCE_REVIEWED, CONFIG_VALIDATED, PLAN_VALIDATED, APPROVAL_VERIFIED, APPLY_EXECUTED, DEPLOYMENT_VERIFIED, RECOVERY_TESTED, NOT_TESTED and BLOCKED independently.

## Expert contracts and offline demonstration

See [portable contracts](../extensions/devops/skills/devops-infrastructure/references/CONTRACTS.md) and [examples](../extensions/devops/skills/devops-infrastructure/references/EXAMPLES.md). In an authorized Toolkit checkout:

```bash
python scripts/validate_devops.py
python -m unittest tests.test_devops -v
```

The Python-standard-library-only `fixtures/devops/cases.json` represents a fictional pipeline with 18 deliberately broken cases, validated by identical rules against the passing reference. No actual deployment, Docker execution, IaC plan/apply, migration, server access, cloud access, restore or paid service. Real AI activation is NOT_MEASURED. Toolkit copies used for another project remain read-only; return reports in chat unless the user explicitly requests another destination.
