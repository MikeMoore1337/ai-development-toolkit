---
name: security-review
description: "Review security of test repositories, CI pipelines and automation helpers. Use before integrating agents, external tools or new test credentials."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Security Review

Inspect secret handling, logging, CI permissions, dependency provenance, shell and code execution, artifact exposure and third-party uploads. Look for unintended access to production data and broad tokens. Compare findings with actual threat model and least-privilege controls. Reference the precise file and abuse path and propose a minimally scoped fix. Do not fetch or display secret values; use approved scanning tools with secure outputs and protect incident evidence.
