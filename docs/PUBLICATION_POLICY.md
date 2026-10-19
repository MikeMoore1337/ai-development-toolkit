# Publication policy

The published Toolkit must contain no personal project names, private account IDs, signed individual license grants, credentials, internal paths, deployment targets or employee-only documents.

- **Clear Voice:** user-authored generic edition with its own MIT license and third-party attributions. Source-specific profiles were rewritten to domain-generic profiles; only synthetic examples are retained.
- **QA Engineering Pack:** generalized user-provided work methods. Review employer agreements and internal-data handling before public publication.
- **Make Feature 0.3.0:** original authored by Artemiy Miller and distributed with its MIT source license. The provided tarball also included a personally issued license explicitly forbidding redistribution; the recipient states that the rights holder separately granted authorization for any use, modification and publication. The separate grant was not supplied for independent verification. The public package excludes the personally issued files, names, IDs and address. If a public release is planned, retain written proof of that later permission outside this repository.
- **Third-party dependencies:** preserve applicable notices and track provenance. Installing the pack does not grant operational permissions.

## Mandatory future-release rights gate (Issue #28)

The SPDX/MIT labels in files are claims about licensing, not independent evidence that the complete distributed copy is authorized. See [provenance audit](PROVENANCE_AUDIT.md) and `provenance/skills.json`. Before any **new** tag or GitHub Release run `python scripts/validate_provenance.py --mode release` on the proposed source tree. A failure is a **release blocker**, not a routine warning. This currently includes Make Feature, QA-derived components and branding assets; each needs an owner review with non-secret evidence reference and clear file/version scope. CI inventory PASS does not lift the blocker.

Do not upload personal grants, correspondence or private employer archives. Preserve existing tags, and obtain an explicit separate owner decision before excluding or replacing Make Feature. GitHub post-publication archive checks cannot undo an already published release.
