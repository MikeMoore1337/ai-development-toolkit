# Lockfile comparison and safe upgrade workflow

## Reuse-first matrix

| Capability | Existing coverage | Remaining gap | Decision |
| --- | --- | --- | --- |
| Minimal updates | minimal-safe-change | Package-specific scope | REUSE |
| Diff review | code-review | Lockfile/transitive delta | REUSE + NEW guidance |
| Dependency inventory | Existing managers | Declared vs resolved completeness | NEW contract |
| Security notices | security-engineering / SUPPLY_CHAIN | Resolved-version applicability | REUSE + NEW handoff |
| Provenance, license | security-engineering, external-skill-review | Registry/checksum/license in diff | REUSE |
| Compatibility | QA contracts and integration-testing | Project-specific upgrade matrix | NEW contract |
| Rollback | release-safety, devops-infrastructure, reliability-testing | Dependency/data/production distinctions | REUSE + NEW handoff |
| Post-release | observability-sre | Verified regressions in running service | REUSE |

## Method

1. Pin old source SHA, declared manifest, resolved lockfile, platform, toolchain, environment and known-good checks.
2. Choose the project's native manager (npm/pnpm/Yarn, pip/uv/Poetry, Maven/Gradle, NuGet, Cargo, Go modules, Composer, Bundler); verify installed version and command semantics. Never run upgrade-all automatically.
3. Establish normalized stable package IDs, including namespace and registry. Compare old/new version, directness, scope, source, checksum, license, platform/peer constraints. Do not guess absent transitive edges.
4. Detect added, removed and modified nodes. A single direct upgrade that changes 20 transitives is a 21-package resolution change, not merely a direct change.
5. Manifest changed with unchanged lockfile => do not call candidate installed. Lockfile changed without requirements => investigate provenance. Unexpected registry or checksum change requires independent supply-chain review.
6. Check release notes, migration guide, deprecations, API/errors/defaults/persisted formats and actual consumer compatibility. A green build does not establish functional correctness.
7. MINIMAL: one dependency plus necessary linked nodes. COORDINATED: only genuinely coupled packages/runtime migration with documented reason. Do not mix unrelated upgrades in one PR.
8. Reviewer independently checks source and diff; QA selects static/unit/contract/integration/E2E/runtime checks based on affected behavior. Owner approves significant changes, merge and deployment under project rules.
9. Recheck actual diff and tests after *authorized* application. Record exact evidence and stop before unapproved operations.

## Two fictional examples

**Ordinary:** alpha-core 1.2.0 to 1.3.0; resolved gamma-lib changes 0.9.0 to 1.0.0 indirectly. Fictional notes claim a fix and retained legacy_fetch API. A mutated candidate lacking legacy_fetch is rejected as BREAKING_API. Both changed nodes must appear in the report.

**Security:** secure-client 1.4.0 to 1.5.0, transport-core 2.0.0 to 2.1.0 (coupled). Fictional SYNTH-ADV-001 describes affected range [1.0.0, 1.5.0). This is **not** a CVE. Check exact resolved version and range before classification. An unverified notice yields APPLICABILITY_UNKNOWN, a too-new runtime blocks the automatic recommendation. Negative security regression and integration tests are required in this synthetic contract.

Executable normalized oracle: [script](../../../../../scripts/validate_dependency_maintenance.py), [fixtures](../../../../../fixtures/dependency-maintenance/README.md). No real package is fetched, changed or security-scanned.
