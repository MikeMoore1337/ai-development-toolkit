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
