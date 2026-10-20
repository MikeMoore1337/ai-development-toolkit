# Worked examples and reuse-first matrix

| Capability | Decision |
| --- | --- |
| CI trust, secret lifecycle | REUSE security-engineering |
| Release readiness | REUSE release-safety |
| Migration compatibility | REUSE database-migrations |
| Failure recovery | REUSE reliability-testing |
| Failed job diagnosis | REUSE failure-triage |
| Infrastructure inventory, CI pipeline, container/IaC review, plan/apply, environment and deployment contract | NEW devops-infrastructure |

**Beginner:** "Help me prepare automatic tests and safe publication for my local Python app, for free. Inspect the project first; do not touch a server." Respond with minimal optional checks, their failure conditions and a non-executing plan. No default Docker or cloud.

**Expert:** "Audit exact-SHA artifact provenance, trusted and untrusted CI stages, an IaC plan, migration ordering, canary rollout, approval gates and data recovery." Require stage DAG, real evidence classification, blast radius, compatibility, exact approval, stop conditions and post-apply proof. A synthetic plan is not a provider plan.

**Excluded routing:** "Fix the failing CI job", "Scan for secrets" and "Create a React page" go to neighboring skills. Real AI skill activation: NOT_MEASURED.

## Static Dockerfile fixtures
`fixtures/devops/docker/good/` and `fixtures/devops/docker/bad/` are fictional container configurations, not deployment targets. The good example defines a local health endpoint, non-root identity and resolvable startup. The broken example deliberately violates those contracts, copies a broad context containing a synthetic debug file, and names a nonexistent startup script. `tests/test_devops.py` checks both using the same independent static oracle, without Docker, shell commands or networking. Base image provenance, build, container runtime and actual health are NOT_TESTED.
