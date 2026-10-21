# Changelog

## Unreleased (main after v5.5.0)

No changes recorded yet.

## 5.5.0 (released, 2026-10-21)

- QA Engineering Pack v2: task-specific references for all 27 QA skills, strengthened contracts for 11 roles and evidence-based handoffs (#124, #125).
- Cross-client workflows, capability matrix and conservative ZIP onboarding for Codex, Claude Code and conversational assistants (#68).
- Evidence-oriented idea-to-delivery workflow and resumable handoff contracts (#67).
- UX/UI Design Orchestra with independent review safeguards and approval before interface changes (#121, #123).
- Added offline engineering, security, reliability, accessibility, data, DevOps, maintenance and SRE guidance with deterministic checks.
- Expanded Russian and English documentation, client compatibility diagnostics and regression testing without introducing mandatory paid APIs or live-agent claims.


- Added UX/UI Design Orchestra: bounded independent specialist analysis, single read-only design proposal, explicit pre-implementation owner approval, honest sequential fallback, offline receipt validator and RU/EN integration guides (#121).

- Added a full Russian Skill Quality Metrics guide with pinned historical evidence, matching CLI examples and offline translation regressions (#87).

- Added Russian specification validation and reproducible release guides with unchanged official CLI commands and owner rights gates (#87).

- Added bilingual Universal Engineering, Skill Quality v2 and historical Source Evaluation guides without changing canonical skills; extended reverse-link and drift checks (#87).

- Added bilingual Clear Voice human-use guides with exact offline install examples and explicit limits; the Russian-primary canonical SKILL.md remains unchanged (#87).

- Added full Russian beginner workflow and quality rubric, normalized the canonical rubric to English, with translation consistency checks (#87).

- Added English counterparts to four Russian-first guides (adaptation, integration matrix, portability trials, task prompt), with reversible source revision tracking (#87).

- Audited two-way RU/EN documentation coverage; added a bilingual Make Feature *human* guide and explicit language policy, preserving the Russian canonical source skill and owner-gated snapshots (#87).

- Added a single beginner journey contract with three personas, observable acceptance examples, 13 negative guard fixtures and deterministic offline regressions (#49). No live agent or human usability evidence is claimed.
- Extended Russian documentation with client migration, compatibility evidence, publication rules and an offline first-run CLI acceptance smoke; human novice usability remains NOT_TESTED (#78).

- Added non-blocking, pinned-source freshness warnings for Russian translations and negative regression fixtures (#78); strict review remains manual.

- Added Russian installation, curated profile guide and catalog covering 65 skills, 16 roles and 27 profiles, with cross-language navigation and coverage checks (#78).

- Started a Russian documentation entry point and safe beginner walkthrough, with offline localization navigation/CLI regression checks (#78); priority technical manuals are still English.

This release includes the changes made since [v5.4.0](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.4.0). See the [v5.4.0...v5.5.0 comparison](https://github.com/MikeMoore1337/ai-development-toolkit/compare/v5.4.0...v5.5.0). Official client activation and effectiveness remain unmeasured unless separately evidenced.

- Added offline Codex/Claude trial harness and hidden-oracle protections; live model evaluations remain owner-gated and unmeasured (#19-23).
- Added pinned official Agent Skills validation, source quality/link/profile checks, provenance inventory and release preflight (#25, #27, #28).
- Added managed Codex/Claude migration, offline client contract checks, curated task profiles and reproducible static quality metrics (#31, #33, #37, #38).
- Added optional, framework-neutral Frontend, Backend and Fullstack skills, then improved their quality contracts and documentation (#41, #75).
- Added Skill Quality v2 templates, negative fixtures and evidence rules; recorded the semantic audit and resolved identified quality issues (#43, #44, #45).
- Bounded and de-duplicated superseded PR validation runs; these changes do not establish real-client activation or effectiveness (#72).

## 5.4.0 (released, 2026-10-18)

- Skill Manager v2: owned-only install/status/update/uninstall/rollback/recover, local backups, exclusive locking, drift checks, and deterministic file diff previews.
- SHA256 inventory checks now reject omitted or extra Git-tracked files and support verification of GitHub-generated source archives.
- Publication security and compatibility checks remain required across Ubuntu/Python 3.12/3.13 and Windows/Python 3.14.
- Added a read-only GitHub Actions release workflow that downloads, extracts, and checks the published source archive and retains verification evidence.
- No independent real-agent effectiveness benchmarks have been completed yet; Skill Evals #11 remains open.

## 5.3.0 (2026-10-18)

- Validates the declared inventory with the optional upstream Agent Skills reference CLI, including the QA and Make Feature extension packs; fail closed when an expected skill is missing.
- Checks recorded package SHA256 digests in Linux/Windows CI, accounting for Git-normalized LF/CRLF endings; provides explicit regeneration for maintainers.
- Adds regression tests for cross-platform text, malformed manifests, stale hashes, duplicates, and unsafe paths.
- Updates maintained GitHub Actions and documents evidence requirements for releases.
- Official GitHub Release and real-agent performance evaluation are separate work, not implied by these checks.

## 5.2.0 (2026-10-18)

- Clear Voice: full, generic source skill with four portable domain profiles and 61 synthetic checks; removed private project identifiers from the public edition.
- Make Feature 0.3.0: opt-in source, scripts, reference material, templates and unit tests; normalized Agent Skills metadata; excluded personal issuance license document.
- Updated manifest, profiles, public checks, integration docs and regression tests.

## 5.1.0 (2026-10-18)

- Restored full MIT-licensed Clear Voice 1.0.0, source attribution, project profiles and original offline evaluations.
- Added the `editorial` / `editorial-qa` installation profiles; retained lightweight `editorial-naturalness` compatibility.
- Made optional personal Make Feature installation explicit; no proprietary files or personal license are redistributed.
- Added regression coverage for Clear Voice packaging and Make Feature publication boundaries.

## 5.0.0 (2026-10-18)

- Added opt-in, portable QA Engineering Pack: 27 skills and 11 reference roles, with provenance mapping to the owner-provided work-project material.
- Added QA profiles for Python, fullstack, CI, release, contracts, security, management and collaboration.
- Updated installation and validation to resolve skills across core and QA packs and test against malformed metadata and missing references.
- Kept Make Feature personal package, third-party snapshots and credentials out of the public release.

See the [QA portability note](docs/QA_PORTABILITY.md) for constraints.
