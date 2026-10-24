# Changelog

**v5.5.4 publication confirmed (2026-10-23)**

[GitHub Release v5.5.4](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.4) was published on 23 October 2026 from tag commit `5affd7f18e9963eee6cb7692ad4d21d3b6f2c8c7`. The tagged manifest version is `5.5.4`. Later `main` changes are not part of this release.

**v5.5.3 publication confirmed (2026-10-22)**

[GitHub Release v5.5.3](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.3) was published on 22 October 2026 from commit `14b96569528ab9544c0d28aa1a00343496066445`. The tagged manifest version is `5.5.3`. Earlier candidate entries below preserve their historical context.

**v5.5.2 publication confirmed (2026-10-21)**

The [v5.5.2 GitHub Release](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.2) was published on 21 October 2026 at commit `bf8d469f7402ed1a99e19ba6797d841751801ea5`. The published tag's `MANIFEST.json.version` is `5.5.2`. Earlier candidate statements below remain historical pre-publication records; they are **not** the current release status. The existing v5.5.0 and v5.5.1 mismatches are unchanged.


**v5.5.0 published-tag metadata erratum (2026-10-21)**

GitHub [v5.5.0](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.0) was published at tag SHA `04d60055e93c04dda26fb3868689ab4031fbf617`. Its **tagged source still declares `MANIFEST.json.version = 5.4.0`**, and its historical changelog incorrectly listed released material as `Unreleased`. This entry is a forward-only erratum, **not** a rewritten historical tag or proof that the archive manifest was updated. Follow [#146](https://github.com/MikeMoore1337/ai-development-toolkit/issues/146) and [#153](https://github.com/MikeMoore1337/ai-development-toolkit/issues/153) for the forward-only v5.5.2 correction; this release-candidate changelog does not claim v5.5.2 exists as a published GitHub Release.

**v5.5.1 published-tag metadata erratum (2026-10-21)**

GitHub [v5.5.1](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.1) was published at immutable tag SHA `64f163acc322acc6aecf5b1f44b6f76744505f46`. **Its tagged `MANIFEST.json.version` is still `5.4.0`.** The v5.5.1 correction from PR #169 was not merged before tagging. This is a second actual release-identity discrepancy, not a valid correction of v5.5.0. Do not force-move the existing tag. New forward-only candidate v5.5.2 requires exact tag/manifest identity, source rights approval and downloadable archive verification (#146, #153).

## Unreleased (main after v5.5.4)

## 5.5.4 (released, 2026-10-23)

- Published the forward-only changes since v5.5.3 as [v5.5.4](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.4), at immutable commit `5affd7f18e9963eee6cb7692ad4d21d3b6f2c8c7`.
- Completed all five offline acceptance criteria for routing [#189](https://github.com/MikeMoore1337/ai-development-toolkit/issues/189): 82 current declared skills, 416/416 curated lexical checks, explicit unsupported abstentions, bounded negative clauses, auditable primary versus auxiliary candidate roles, and additional case-level RU/EN label diagnostics.
- Added 12 additional AI-authored RU/EN **diagnostic-only** requests to inspect primary/auxiliary label overlap, non-gold candidate frequency and abstention. Historical untouched holdout 18/38 supported; prior exploratory 6/18 supported; fresh diagnostic 4/12 supported. These figures are **not** independently adjudicated semantic accuracy, and must not be tuned against their own prompts.
- Added source-only comparison and negative-control unit tests, refreshed matching checksum/provenance inventory and translated diagnostic guidance.
- **Limits:** Client skill choice NOT_OBSERVED, real task effectiveness NOT_TESTED, reviewer independence NOT_VERIFIED. Actual A/B client tests remain [#141](https://github.com/MikeMoore1337/ai-development-toolkit/issues/141); no paid API, provider setup or client activation is introduced.

## 5.5.3 (released, 2026-10-22)

**Status: published as v5.5.3 on 2026-10-22 from commit `14b96569528ab9544c0d28aa1a00343496066445`.** Changes merged since [v5.5.2](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.2):

- Added portable ChatGPT plugin source with task routing, engineering, QA and UX/UI guidance, without local project access or paid API requirements (#184).
- Added user-level read-only Codex MCP and source auto-update support on Windows, Linux and macOS, including tests and bilingual installation guides (#183, #184).
- Added project-scoped MCP for Codex/Claude Code with guarded installation and removal flows (#183).
- Added Prompt Refinement, SEO audit and cross-client routing skills, while documenting truthful activation and access limits (#182).
- Fixed colloquial RU/EN task routing for prompt refinement, SEO and visual requests in the bundled and project-scoped MCP adapters, with offline regressions (#187).
- Improved macOS ARM64/Intel portability checks and complete Windows/Linux/macOS setup documentation (#181).
- Enforced equal visibility of ChatGPT and Codex integrations, added regression coverage and updated provenance inventory (#185).
- Expanded bilingual documentation and refreshed the evidence-first repository presentation (#87, #178).


- Added dependency-free local stdio Toolkit MCP server, read-only skill routing/search/preview/status and guarded per-project Codex/Claude Code installer for Windows, Linux and macOS.
- Added bilingual MCP installation, removal and safe update instructions with regression tests on all five CI environments.

- Added bilingual Windows, Linux and macOS installation and update instructions, preserving client/file ownership boundaries.
- Added focused macOS ARM64/Intel GitHub Actions portability checks without paid runners or real agent clients.

- Reorganized bilingual README onboarding around tasks, real execution boundaries, and compact navigation.
- Added the Evidence Desk vector hero and count-free social preview proposal without modifying approved legacy PNG files.
- Added offline README/presentation regression checks and recorded the verified v5.5.2 release status.

## 5.5.2 (candidate, 2026-10-21)

- Prepared a forward-only, version-consistent source candidate after both v5.5.0 and v5.5.1 shipped with a stale manifest; publication of this candidate remains pending (#146, #153).
- Added fail-closed GitHub source-archive verification of Git tag against MANIFEST.json.version. The gate detects errors but does not undo a published tag (#172).
- Kept the QA Pack v2, Make Feature and source-rights snapshots unchanged; refreshed translation revision pin, version-independent negative tests and SHA256 inventory.
- Stabilized Go offline oracle and cleanup behavior on Windows/Linux without weakening failure checks (#143, #149).
- Added stricter UX/UI Design Orchestra routing and design-quality gates (#144).
- Introduced offline zero-cost orchestration A/B evidence contracts, **not** real agent effectiveness results (#141).
- Added a nonblocking bidirectional RU/EN coverage report and translated publishing and branch-protection guides (#87; PRs #159, #160).
- Added Russian zero-spend real-agent pilot operating guide with pinned source revision and strict offline evidence caveats (#87; PR #164).
- Require three distinctly rendered low-fidelity comparison sketches before UX/UI Design Orchestra approval, with an offline fail-closed gate (#166).
- Add Russian evaluation, GitHub setup and Windows-first-publication operator guides and correct dangerous first-publication instructions for the already existing official repo (#87; PR #168).
- Published forward-only metadata errata for both immutable v5.5.0 and v5.5.1 tags (#153).
- Added guarded on-demand ChatGPT personal plugin live-guidance source loading (source-only contract; automatic plugin binary update is NOT provided) (#170).

## 5.5.1 (released, 2026-10-21)

- Actual immutable tag: `64f163acc322acc6aecf5b1f44b6f76744505f46`. It contains previously merged documentation, QA and UX/UI work, **but also `MANIFEST.json.version=5.4.0`**. The tag was published without the intended version correction. SHA256/provenance-only CI did not check the tag identity.

## 5.5.0 (released, 2026-10-21)

- Shipped QA Engineering Pack v2, cross-client capability and handoff workflows, UX/UI Design Orchestra and other engineering packs from v5.4.0 to 21 October 2026.
- Historical archive limitation: tag v5.5.0 was actually published from a tree whose MANIFEST.json and README still said v5.4.0; the immutable archive has not been altered. v5.5.1 did not correct the tagged metadata; v5.5.2 is the next proposed forward-only fix.


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

These changes are included in the [published v5.5.0 release](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.0), despite the stale 5.4.0 version metadata inside that historical source archive. The v5.5.0 tag is preserved; compare [v5.4.0...v5.5.0](https://github.com/MikeMoore1337/ai-development-toolkit/compare/v5.4.0...v5.5.0) for the recorded source changes.

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
