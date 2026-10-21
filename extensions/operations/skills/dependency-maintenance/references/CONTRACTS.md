# Portable dependency inventory and upgrade contracts

## Inventory

Each component: package_id (ecosystem + namespace), package_name, ecosystem, declared_range, resolved_version or UNKNOWN, direct_or_transitive, scope (production/development/build/optional/platform/toolchain), registry/source, lockfile_reference, platform, confirmed license or UNKNOWN, known_advisory_status, used_by and evidence. A manifest is declared intent; a lockfile records resolved state. A requirements.txt is not necessarily the full dependency graph. If graph completeness cannot be established, set TRANSITIVE_DEPENDENCIES = UNKNOWN.

Support a generic process for Python (pip/uv/Poetry), JavaScript/TypeScript (npm/pnpm/Yarn), Java/Kotlin (Maven/Gradle), .NET (NuGet), Rust (Cargo), Go modules, PHP (Composer) and Ruby (Bundler). Use only the real project's package manager and verify its version/commands before any update. Do not build parsers for all ecosystems.

## Upgrade Assessment Contract

| Required field | Purpose |
| --- | --- |
| assessment_id, project, source_revision | Bound to exact source |
| ecosystem, package_id, current_declared, current_resolved, candidate | Distinguish intended and resolved |
| upgrade_reason, project_impact | Security/compatibility/bug/feature/maintenance/optional |
| advisory_source, advisory_status, affected_range, fixed_version, applicability | Independently sourced security claims |
| release_notes_source, release_notes_status, breaking_changes | Official notes, migrations, deprecations or UNKNOWN |
| old_graph, candidate_graph, lockfile_diff | Direct/transitive/source/checksum/license delta |
| compatibility_constraints, compatibility_matrix | Actual target runtime/platform/framework/API |
| security_implications, license_implications | Supply-chain and rights review |
| test_plan, test_executions, test_evidence | Executed results distinct from planned checks |
| change_plan, rollback_plan, approval | Authorization and recoverability |
| decision, actual_verification_status, change_status, release_status | Never infer later stage |

Decisions: UPGRADE_RECOMMENDED, UPGRADE_OPTIONAL, DEFER, REPLACE, REMOVE, BLOCKED, INSUFFICIENT_EVIDENCE. Version novelty alone is not a reason to upgrade.

Advisory proof status: ADVISORY_CONFIRMED, ADVISORY_NOT_VERIFIED, NO_KNOWN_ADVISORY_IN_CHECKED_SOURCES. Separately record PACKAGE_AFFECTED, NOT_AFFECTED_BY_RANGE or APPLICABILITY_UNKNOWN. Source result: SOURCE_CONFIRMED, PARTIAL, UNKNOWN, NOT_CHECKED. Official notice does not automatically prove a reachable vulnerability.

## Compatibility Matrix

For each relevant runtime, OS, framework, database driver, API, build, container, browser, compiler/toolchain or deployment target record target_value, source_support_status, support_evidence, test_status, test_environment, exact_test_case, test_evidence. Status: SUPPORTED_BY_SOURCE, TESTED_PASS, TESTED_FAIL, NOT_TESTED, UNKNOWN, NOT_APPLICABLE. Source-support and actual local test results are different dimensions.

[Ordinary synthetic model](../../../../../fixtures/dependency-maintenance/ordinary.json) and [security model](../../../../../fixtures/dependency-maintenance/security.json) are normalized fictional data for offline oracles, not actual package-manager lockfiles or published release notes.
