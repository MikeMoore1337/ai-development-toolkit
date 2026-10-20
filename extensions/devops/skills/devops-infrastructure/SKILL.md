---
name: devops-infrastructure
description: "Discover real project infrastructure, review CI/CD, container and IaC configuration, and prepare verifiable deployment, approval and recovery plans. Use for DevOps and infrastructure planning, not isolated CI failures, security-only checks or deployment execution."
metadata:
  pack: "devops"
  version: "1.0.0"
---

# DevOps & Infrastructure

**Use for:** designing CI/CD, reviewing Dockerfile/Containerfile, inspecting IaC, planning infrastructure changes, environment separation, deployment and rollback; "Настрой CI/CD", "Проверь инфраструктуру", "Подготовь безопасный план обновления сервера".

**Do not use for:** a single failed CI job (use `failure-triage`), secret scanning (use `security-engineering`), a specific database migration (`database-migrations`), performance testing (`performance-load-testing`), React UI design or general feature delivery. This skill is neither a workflow controller nor a release gate.

1. **Inventory first.** Inspect actual build commands, CI, containers, IaC, configurations, environments, secret *references*, migrations, workers, health checks, backups and permissions. Mark findings `CONFIRMED`, `ASSUMED`, `UNKNOWN`, `NOT_APPLICABLE`. Never assume Docker/Kubernetes/Terraform/cloud/VPS are required.
2. **Reuse existing controls.** `security-engineering` owns threats and CI credential trust; `release-safety` owns release readiness; `database-migrations` owns schema safety; `reliability-testing` owns state recovery invariants; `failure-triage` diagnoses isolated failing jobs; `architecture-decisions` compares meaningful alternatives.
3. **Define a pipeline contract** with source SHA, triggers and trust, dependencies, stage prerequisites/success/failure/permissions/evidence, required checks, provenance and artifact checksum, environment, approval, post-deploy verification and recovery. Failed required checks, unknown source, wrong artifact or untrusted deployment must block release.
4. **Review only applicable infrastructure.** Inspect container base/digest, build context/secrets, user, startup, health, writable paths and limits only when containers exist or are requested. For IaC record current/desired state, changes, deletions, blast radius, cost and actual provider-plan evidence; never equate static parsing with a real plan.
5. **Separate plan from apply:** `DRAFT -> PLAN_PREPARED -> PLAN_VALIDATED -> APPROVAL_PENDING -> APPLY_AUTHORIZED -> APPLIED -> POST_APPLY_VERIFIED`. Each advancement requires its own evidence. Never infer a change from green CI, a merged PR or a created file. Production, real apply, VPS access, migration, DNS/IAM/firewall and destructive rollback require explicit scoped authorization.
6. **Respect environment and migration boundaries.** Identify owners, trust, data, secrets, costs and permitted actions for local/CI/test/staging/prod; staging labels alone do not prove isolation. Assess expand/migrate/contract sequencing, partial failures and backward compatibility.
7. **Plan recovery** with previous artifact, stop conditions, health/smoke checks, validated backup/restore evidence where needed, forward-fix and residual data risks. Code rollback is not data rollback. Forward readiness to `release-safety`, rather than issuing release permission.
8. **Report exact evidence levels:** `SOURCE_REVIEWED`, `CONFIG_VALIDATED`, `PLAN_VALIDATED`, `APPROVAL_VERIFIED`, `APPLY_EXECUTED`, `DEPLOYMENT_VERIFIED`, `RECOVERY_TESTED`, `NOT_TESTED`, `BLOCKED`. Preserve uncertainty and return user-project reports in chat by default. Toolkit copies used in other projects are read-only.

See [technical contracts](references/CONTRACTS.md), [worked examples](references/EXAMPLES.md), English/Russian guides are at `docs/DEVOPS_INFRASTRUCTURE.md` and `docs/ru/DEVOPS_INFRASTRUCTURE.md`.

**Synthetic local verification:** `python scripts/validate_devops.py`; `python -m unittest tests.test_devops -v`. No Docker build, IaC provider, cloud, VPS, network, paid tools, production deployment or real restore.
