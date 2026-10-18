---
name: architecture-decisions
description: Compare design alternatives for a cross-cutting or high-impact change without unnecessary infrastructure. Use before changing major component boundaries.
---


# Architecture decisions
1. Inspect the system as built: dependencies, deployment, data boundaries, operational constraints and team capacity.
2. State measurable requirements, scale, reliability and maintenance tradeoffs.
3. Compare the smallest viable design with one or two credible alternatives.
4. Identify migration and rollback implications, failure modes, compatibility and required tests.
5. Do not introduce brokers, microservices, caches, frameworks or agents without concrete need.
6. Record an ADR only when a significant enduring decision benefits from one.
**Output:** option matrix, choice, impact, verification and unresolved assumptions.
