---
name: adt-security
description: Use for authentication, authorization, exposed secrets, dependency risks, application security, threat boundaries, hardening or DevSecOps audits, even without an ADT mention.
---
# Targeted security review
1. Define threat model, exact scope and trust boundaries. Inspect permitted task-relevant files; do not enumerate secrets or scan arbitrary projects.
2. If useful, call toolkit_prepare_task once with max_skills: 1; use relevant full skill, no automatic catalog, repeated info calls or unapproved network.
3. On a new finding or transition to remediation/verification, use toolkit_prepare_stage with max_skills: 1, confirmed full consulted_skills digests and justified candidates. Read references only as needed.
4. Preserve security rules and review approvals. No paid APIs/model calls, packages or repo mutations without permission.
5. Record reproducible findings, observed tests and residual risks; distinguish static analysis from live checks.
