---
name: requirements-traceability
description: "Connect requirements to test cases, executions and evidence. Use when auditability or cross-team handoff is needed."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Requirements Traceability

1. Assign stable, repository-appropriate IDs or reuse existing tracker IDs; do not invent external issue IDs.
2. Create links `requirement -> test design -> implemented check -> execution -> evidence`.
3. Mark planned, implemented, executed, passed, failed and unknown as distinct statuses.
4. Store links in the existing issue/PR artifacts when possible; avoid creating a shadow source of truth.
5. Update mapping when scope changes, including approved exclusions and outstanding risks.

Use [traceability worksheet](references/TRACEABILITY.md) for a concise example. Jira and Test IT are optional integrations, not dependencies.
