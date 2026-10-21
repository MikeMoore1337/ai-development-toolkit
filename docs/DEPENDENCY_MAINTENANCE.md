# Dependency Maintenance (Issue #64)

[Русская версия](ru/DEPENDENCY_MAINTENANCE.md)

The optional dependency-maintenance profile is for evidence-based upgrades, not an automatic updater. One new skill is included in the existing Operations extension. It reuses minimal-safe-change, code-review, security-engineering, release-safety and narrow QA/SRE guidance.

## Beginner

A dependency is a library or tool an app relies on. Direct dependencies are declared by an application; transitive dependencies are required by dependencies. A manifest specifies intended versions/ranges; a lockfile holds the resolved graph from a particular installation or resolution. Without verified resolution, the full transitive graph is UNKNOWN.

Example: “Check which dependencies actually need updating, what may break, how to test and undo the changes. Do not change files without my approval.”

SemVer is a major/minor/patch convention, not a guarantee. Even a PATCH can change behavior or underlying dependencies. The newest version is not inherently the most suitable version. A breaking change may alter APIs, returned data, defaults, errors, runtime requirements, formats or protocols despite successful installation.

## Expert process

Inventory → reason (security/compatibility/bug/feature/maintenance/optional) → official release notes and advisories → lockfile and transitive diff → breaking changes and package provenance → compatibility matrix → risk-based static/unit/contract/integration/E2E/runtime checks → owner-approved bounded update → rollback and actual evidence.

| Concern | Evidence |
| --- | --- |
| Security | Exact ecosystem/package/resolved version, official affected/fixed ranges, relevant usage, or UNKNOWN |
| Notes | Verified changelog, migration and deprecations, source-status limitations |
| Lockfile | All added/removed/modified direct/transitive nodes and registry/integrity/license/peer changes |
| Compatibility | Supported by vendor versus actually tested target runtime/platform |
| Rollback | Old source, manifest/lockfile, reinstall environment, data compatibility and verified restoration |

Sources may include maintainer security notices, GitHub Security Advisories, OSV, NVD or ecosystem advisories. No CVE found in checked sources is not proof of safety; offline current checks are NOT_CHECKED. Never invent a CVE, fix or exploitability. Git revert does not roll back deployed dependencies or data. Green CI only demonstrates the tested scenarios in those environments; successful package installation is not full compatibility.

## Offline verification and portability

Two fictional synthetic examples (ordinary upgrade with transitive delta and incompatible API mutant, security-driven upgrade with range/runtime/coupled dependencies) plus 20 negative fixtures. Only normalized synthetic models are parsed. There is no actual package compatibility testing or security scan.

To exercise Toolkit's own fixtures (Python standard library, not a requirement for using the Skill):

    python scripts/validate_dependency_maintenance.py
    python -m unittest discover -s tests -p 'test_dependency_maintenance.py' -v

No paid tool, mandatory API, Dependabot, Renovate, schedule or new package manager. Toolkit is read-only in other projects and reports stay in chat unless otherwise authorized. Real advisories, live package compatibility, production rollback and AI-client skill activation are NOT_MEASURED.

[Skill](../extensions/operations/skills/dependency-maintenance/SKILL.md) · [Contracts](../extensions/operations/skills/dependency-maintenance/references/CONTRACTS.md) · [Fixtures](../fixtures/dependency-maintenance/README.md).
