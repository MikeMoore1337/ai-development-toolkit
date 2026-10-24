# Contributing

[Русская версия](CONTRIBUTING.ru.md)

Thanks for improving AI Development Toolkit.

## Submit a change

1. Open an issue describing a concrete problem or skill proposal, including the intended clients and project context.
2. Prefer one skill/role or small, measurable change per pull request.
3. For each skill, add a compliant `SKILL.md`, a clear `description` stating **when** to use it, and any necessary references/tests.
4. Run metadata validation and unit tests. Report manual tests separately.
5. Record provenance and rights for third-party content. Do not paste material from private archives.

## Review criteria

- Is the skill genuinely reusable across projects?
- Does it conflict with another skill or override the project's instructions?
- Can its outcome be evaluated using acceptance criteria?
- Is its cost (latency, context, maintenance) justified by an observed benefit?
- Does it respect user-granted execution/release permissions?

## Keep the skill catalog current (#301)

This is a **manual, change-scoped maintenance process**, not a second skill manager or a background updater. Start with the concrete task, not a target catalog size. To check local lexical coverage without installing anything, run `python scripts/skill_candidate_review.py --query "your task"`. `FOUND_LOCAL` means a readable matching skill name; `MISSING` does **not** prove a semantic gap.

| Decision | Minimum evidence and required action |
| --- | --- |
| **Add** | Show an actual uncovered task, expected improvement and acceptance example; inspect overlap with existing skills/profiles; define a precise trigger in `SKILL.md`, owner/rights/source evidence, tests and affected catalog/profile/docs entries. Decline additions with no measurable benefit. |
| **Update** | State why the existing skill needs a change; pin the before/after scope, client compatibility and regressions; update only affected references, profiles, examples and tests. Upstream freshness alone is not sufficient. |
| **Deprecate** | Document the reason, supported alternative, impacted clients/profiles and migration instructions; give notice through the relevant guides. Keep it usable during the agreed transition unless a specific risk requires immediate restriction. No universal retirement date is assumed. |
| **Revoke / remove** | For a confirmed rights, security or compatibility problem, block further distribution/installation of the affected material, identify dependent profiles and documentation, and record an owner-approved removal/migration decision. Do not silently delete history or assume that removing repository files also uninstalls copies in client projects. |

**Reuse existing gates rather than introducing another runtime.** For third-party candidates, use the existing [local coverage and pinned-source review](docs/EXTERNAL_SKILL_CANDIDATE_REVIEW.md) (#199), [offline security gate](docs/EXTERNAL_SKILL_GATE.md) (#200) and [provenance/publication review](docs/PROVENANCE_AUDIT.md) (#195). Review an independently sourced exact commit, hashes, license, dependencies, permissions, cost and removal plan. The candidate and its review manifest must be separate, and an allowed source must be explicitly supplied. An offline `ALLOW_FOR_REVIEW` is **not** permission to import, enable, install or publish. No automatic remote refresh, paid API or unreviewed redistribution.

### Check only what changed, while retaining required CI

Inspect `git diff --name-only origin/main...HEAD` on a feature branch and record the base/head SHA. These additional checks are selected by affected files; **do not skip repository-wide required CI**:

| Changed area | Specific review |
| --- | --- |
| Skills, roles, profiles, catalog or external candidate | Verify `SKILL.md` trigger/format, references, overlapping skill choice, manifest/profile links, provenance, source pin, rights, offline security gate when applicable, and focused regressions. Run `python scripts/validate_pack.py` and `python scripts/validate_provenance.py --mode inventory`; release eligibility additionally requires `--mode release` and manual owner review where applicable. |
| A user-facing guide (EN or RU) | Review the corresponding translation and links. If a registered source changes, update its entry in `docs/ru/SOURCE_REVISIONS.json` **after human translation review**, then run `python scripts/check_translation_freshness.py --strict`. This verifies source revision, not meaning or readability. |
| Versions, packaging, installation or release process | Compare `MANIFEST.json`, `CHANGELOG.md`, installation/migration instructions and the exact Git tag versus `main`. Only change the version when a release decision requires it; a docs-only PR is **not** a new release. Never claim installed MCP/ChatGPT clients were upgraded by a repository merge. |
| Client support, compatibility or deprecation | Update only affected support, compatibility, migration and Known Issues sections with actual tested environments, limitations and rollback guidance. Distinguish source validation, real client activation and production behavior; mark unavailable evidence `NOT_TESTED` / `NOT_VERIFIED`. |

For every PR, existing CI retains public-content checks, metadata, provenance, checksum integrity and relevant offline tests. When source files change, regenerate `SHA256SUMS.txt` with `python scripts/verify_checksums.py --write`, review the **actual checksum diff**, then run `python scripts/verify_checksums.py` and `python -m unittest discover -s tests -v`. A successful CI run does not supersede human rights, translation, client-runtime or release acceptance.

### Periodic reconciliation and evidence

**Once per quarter**, and before a release that alters the skill catalog, a maintainer manually compares `MANIFEST.json`, skill/profile references, `provenance/skills.json`, relevant support docs and published release identity. Recheck external upstream sources **only when a pin, advisory or affected skill calls for it**; do not expand the catalog or bump all dependencies on a schedule. Record in the existing Issue/PR: checked source SHA/date, changed paths or `NO_CHANGE`, mismatch or decision, existing gate/test run links with actual results, and unresolved limitations/owner approval. Create a focused Issue only for an actionable discrepancy. This procedure needs **no cron, new CI service, new tracker, paid model/API or write access to other projects**.

## Source material

Include upstream repository, commit/tag, license and a clear explanation of what is copied versus independently adapted. Personal license grants and source repositories are not assumed to allow public redistribution. See `docs/PUBLICATION_POLICY.md`.

## Third-party or work-derived material

Before contributing a skill, role, template, script or reference copied/adapted from elsewhere, add its source and license facts to `provenance/skills.json`. Keep complete notices, review the exact upstream revision and record non-secret evidence of applicable rights. When rights are unresolved use `requires_owner_review` and `owner_gate`, not `verified`. Run `python scripts/validate_provenance.py --mode inventory`. See `docs/PROVENANCE_AUDIT.md` and `docs/PUBLICATION_POLICY.md` for scope and release controls.

## Writing documentation for beginners and engineers

Documentation should support two reading depths on the **same accurate source**, not split into simplified but misleading instructions and a separate technical truth.

1. **Lead with the outcome.** Say who the page is for, what it helps the reader do, and whether installation or terminal access is required. Put the first actionable steps before long background tables.
2. **Explain unfamiliar terms once.** Link to the [glossary](docs/GLOSSARY.md). Preserve exact command names, paths, version numbers and status codes.
3. **Make commands safe to copy.** State prerequisites and the current directory. Label placeholder paths and Python versions; provide Windows, Linux and macOS variants where behavior differs. Keep preview and write operations (`--apply`) in **separate code blocks** with an explicit review step.
4. **Show a way to verify the result.** Describe expected output, failure handling and rollback where relevant. Distinguish file installation, live client discovery, actual skill usage and tested application behavior.
5. **Keep language versions aligned.** Review the corresponding Russian/English user guide and update `docs/ru/SOURCE_REVISIONS.json` when a registered original changes. A matching checksum or green CI is not proof of understandable text or equivalent meaning.
6. **Preserve engineering detail.** Keep limitations, security and authorization gates, alternative flows and implementation contracts in linked technical sections. Do not rewrite protected third-party/QA source snapshots solely for stylistic consistency.

For documentation-only PRs, report which pages were read, changed and checked. If real client behavior or human comprehension was not tested, say `NOT_RUN` or `NOT_VERIFIED` instead of claiming success.

## Static checks before a PR

Run `python scripts/check_public_package.py` and
`python -m unittest discover -s tests -v` before opening a PR. The
Ubuntu 3.12 matrix also runs pinned Ruff correctness rules and checksum-verified
actionlint on workflow definitions. See
[static quality rules](docs/QUALITY_RUBRIC.md#static-quality-and-publication-hygiene-issue-48)
for commands, decisions and limitations. These checks complement, not replace,
manual review of sensitive data and provenance.
