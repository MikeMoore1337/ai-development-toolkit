---
name: test-management
description: "Plan mappings between automated tests and test management systems without requiring any particular vendor. Use for linking requirements to test IDs and reports."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Test Management

Model stable test identity, ownership, requirement traceability and lifecycle independently of a particular service. Separate read, create and update permissions for Jira, Test IT or alternative systems. Check uniqueness, deduplication, idempotency and expected update policy before any synchronization. Never push to a live tracker unless access and authorization are explicit. Preserve test IDs across harmless refactors when the product behavior is unchanged. Provide proposed mappings and actual API effects separately.
