# Changelog

## 5.3.0 (prepared, 2026-10-18)

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
