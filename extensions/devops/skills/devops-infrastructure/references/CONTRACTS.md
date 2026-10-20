# DevOps contracts

## Discovery
Record repository, build, CI trigger/trust, dependencies, container/IaC presence, secret references, services, data and migrations, health, backups, environment owners, permissions and costs. Mark each CONFIRMED, ASSUMED, UNKNOWN or NOT_APPLICABLE. No inferred infrastructure.

## Pipeline
For every stage require unique ID, prerequisites, input, success/failure oracle, dependencies, permissions and evidence. A DAG has no cycles; stage inputs and source SHA must match the artifact; all required tests must pass before release. Untrusted PRs get read-only permissions, no deployment identity or secrets. Reuse `security-engineering` for detailed controls.

## Container
Only when applicable: base image provenance/pinning, build context and secret exposure, non-root rationale, workdir, ports, health, startup, shutdown, writable paths, resource bounds. Static reviewed != image built != container running != runtime verified != deployed.

## IaC, configuration and environments
Current state -> desired state -> change/deletion/cost/risk -> plan -> owner approval -> apply -> verification. Static syntax != real provider plan. Do not write an IaC engine. Detect invalid parameter types/ranges, conflicts, secrets in public config, incorrect environment endpoints and unauthorized debug behavior. Staging may share prod assets.

## Deployment and recovery
Plan requires deployment ID, target, owner, source revision, artifact checksum/provenance, dependencies, checks, migrations, prechecks, deployment strategy, smoke/health, monitoring, stop criteria, rollback/forward-fix, evidence and approval. Choose recreate/rolling/blue-green/canary only if actually supported. Restore-tested proof is needed to claim data recovery. A previous Git SHA does not reverse irreversible data changes.

## Evidence discipline
`SOURCE_REVIEWED`, `CONFIG_VALIDATED`, `PLAN_VALIDATED`, `APPROVAL_VERIFIED`, `APPLY_EXECUTED`, `DEPLOYMENT_VERIFIED`, `RECOVERY_TESTED`, `NOT_TESTED`, `BLOCKED` are distinct. A passing synthetic test never implies live production readiness. Real actions are prohibited in the bundled offline demonstration.
