---
name: forms-validation
description: "Use when implementing forms, user input validation, submission and error feedback."
---

# forms validation

Inspect the actual frontend stack and project conventions before choosing tools or patterns. Follow repository rules and approval gates.

1. List fields, types, required rules, defaults, dependent conditions and authoritative validation layer.
2. Treat client validation as feedback, never access control; server remains authoritative.
3. Define locale, dates, units, trimming and normalization rather than silently altering user input.
4. Cover keyboard interaction, labels, errors, focus, submission state, retry and unsaved changes.
5. Test boundaries, conditional fields, server rejection, duplicate submission and successful recovery.

**Output:** Field contract, validation ownership, UI states and regression checks.
