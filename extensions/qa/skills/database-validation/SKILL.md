---
name: database-validation
description: "Validate persistence semantics and migrations without coupling to one database product. Use for schema or data integrity changes."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Database Validation

1. Identify business invariants, constraints, isolation requirements and transactional boundaries.
2. Validate state via a separate read where practical; ensure test queries are scoped to owned test data.
3. Cover uniqueness, referential integrity, nullability, concurrency and rollback if relevant.
4. For migrations, verify pre/post conditions and compatibility with mixed application versions, plus backout constraints.
5. Avoid production writes and destructive SQL; require explicit authorization for schema operations.

A successful SQL statement is not enough; compare persisted values to the intended business invariant.
