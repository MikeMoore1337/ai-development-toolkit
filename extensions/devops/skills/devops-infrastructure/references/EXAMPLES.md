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
