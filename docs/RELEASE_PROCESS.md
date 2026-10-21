# Reproducible release procedure

[Русская версия](ru/RELEASE_PROCESS.md)

The repository follows PR-based delivery. CI on a PR is necessary, not a
substitute for independently verifying a tagged public release.

## Published v5.5.0 archive erratum (2026-10-21)

The actual latest public GitHub Release is [v5.5.0](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.0), tagged at `04d60055e93c04dda26fb3868689ab4031fbf617`. **The published tag still contains `MANIFEST.json.version = 5.4.0`, and its changelog/release instructions still describe v5.4.0 as the last release.** This is a documented metadata discrepancy, not a reason to move or rewrite an immutable release tag. Treat the tag as the published identity, report the stale in-archive version accurately, and track corrective forward-only work in [Issue #153](https://github.com/MikeMoore1337/ai-development-toolkit/issues/153). Historical v5.4.0 examples and SHA below are retained as historical examples, **not** current-release status. Recheck rights gates, manifest/tag identity and archive evidence before the next release.


## Version and release state

- `MANIFEST.json.version` identifies the **last published baseline release** (currently `5.5.1`), not the version of every subsequent `main` commit.
- `CHANGELOG.md` has an `Unreleased` section for changes merged after the published tag. The latest tagged release section is marked `released`, not `prepared`. Historic entries remain unchanged.
- Published release identity is the immutable Git tag and GitHub Release **at its exact SHA**. `main` is a development branch, potentially ahead of that tag. Do not install `main` and describe it as the published archive.
- Only after the release preflight and explicit owner decision may the next version be chosen, the manifest updated, and a separate release PR/tag prepared. CI never publishes a version automatically.
- Source status is not runtime evidence: verified static format or successful copy does not prove client discovery, activation or improvement.

Current baseline: [v5.5.1](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.1) (2026-10-21). Resolve its exact commit using the published tag; compare [v5.5.1...main](https://github.com/MikeMoore1337/ai-development-toolkit/compare/v5.5.1...main) for subsequent changes. Historical [v5.5.0](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.0) contains stale 5.4.0 metadata and must remain immutable.


1. Work on a feature branch and document what changed and any migration risks.
2. Run `python -m pip install -r requirements-dev.txt`.
3. Run `python scripts/check_public_package.py`,
   `python scripts/validate_pack.py` and
   `python scripts/validate_provenance.py --mode inventory`.
4. Run `python -m unittest discover -s tests -v`.
5. After reviewing the change, regenerate digests with
   `python scripts/verify_checksums.py --write` and **review its diff**.
   The inventory covers tracked files at the time of regeneration, except itself.
   Do not regenerate blindly to conceal unexpected changes.
6. Run `python scripts/verify_checksums.py` to verify recorded file bytes.
7. If the upstream demo CLI is installed and trusted, run
   `python scripts/validate_with_skills_ref.py --scope all`. Its installation
   and test execution are separate from CI; no automatic network install occurs.
8. Check no keys, tokens, private data, unlicensed material or unexpected
   executables entered the diff. The built-in publication script is only a
   basic safeguard, **not** a complete secrets or supply-chain scanner.
9. Open a PR, require all CI matrix jobs (Linux 3.12/3.13, Windows 3.14),
   resolve review discussions, then merge. Do not bypass owner approvals or
   deploy gates. Ruleset settings live on GitHub, not in this repository.
10. **Before creating any tag or publishing a GitHub Release**, run
    `python scripts/validate_provenance.py --mode release` on the intended
    source tree. If BLOCKED, do not publish: resolve each owner-gated item
    based on private rights checks and a non-secret audit record, or obtain
    explicit authorization for a reversible exclusion in a separate PR.
    This is a mandatory manual publication step **even when the required PR CI has already passed inventory and release-preflight checks**. The CI additionally verifies a clean offline `git archive` export (Ubuntu 3.12); GitHub-generated archives of new tags must still be verified separately. The owner-reported decision ID1337 is tied to SHA256 fingerprints and classifications of 44 source units (75 files); any changed, added or relabeled files in that scope require fresh owner review. Passing the snapshot gate confirms only that the files match the recorded decision, NOT independent rightsholder or employer permission.
11. After successful CI on `main` AND the release rights gate, tag the exact validated SHA, publish
    release notes describing changes and compatibility, and verify that the
    public archive contains the expected artifacts. Never describe a tagged
    release as tested on real agents without actual evaluation records.

For the current Ruleset configuration, see [branch protection](BRANCH_PROTECTION.md).
Skills' structure is checked in CI, but real-agent portability and effectiveness
are separate experimental claims.

## Independent verification of a GitHub source archive

Before publishing a new release, download the actual GitHub-generated ZIP and
extract it into a **fresh, empty folder**, not a Git clone or reused worktree.
For example, on Windows (replace the tag for the release under review):

```powershell
$tag = "v5.5.1"
$zip = Join-Path $env:TEMP "adt-$tag.zip"
$dest = Join-Path $env:TEMP "adt-$tag-source"
if (Test-Path $dest) { throw "Destination must be fresh: $dest" }
Invoke-WebRequest "https://github.com/MikeMoore1337/ai-development-toolkit/archive/refs/tags/$tag.zip" -OutFile $zip
Expand-Archive -LiteralPath $zip -DestinationPath $dest
$root = Get-ChildItem $dest -Directory | Select-Object -First 1
python scripts/verify_checksums.py --archive-root $root.FullName
$manifest = Get-Content (Join-Path $root.FullName "MANIFEST.json") -Raw | ConvertFrom-Json
if ("v$($manifest.version)" -cne $tag) { throw "TAG_MANIFEST_VERSION_MISMATCH" }
```

The archive check compares SHA256 values **and requires every extracted source
file to appear exactly once** in `SHA256SUMS.txt`. It rejects missing, extra,
linked and unlisted files. Git worktree mode uses `git ls-files -z` for the
canonical tracked inventory, so new tracked files also require checksums.

This does not authenticate the download or prove publisher identity: verify
the intended tag commit and GitHub workflow results separately. Publication
requires a real execution record for archive verification; merely documenting
this procedure is not evidence that the archive was downloaded.

After publication, the GitHub Actions `Verify release source archive` workflow
runs for a pushed release tag and for `release: published`. It can also be triggered manually
with a valid `vX.Y.Z` tag. Review the completed job and its
`release-source-verification` artifact before declaring archive acceptance.
This workflow checks actual downloaded bytes and rejects an archive whose `MANIFEST.json.version` does not equal the `vX.Y.Z` tag. This post-tag control detects a mismatch but cannot undo a tag or release that has already been published; verify the manifest version before tagging.

New tagged archives are checked against the provenance release gate after SHA verification. Historic archives without the provenance script are reported as `NOT_VERIFIED` for licensing while retaining their independent checksum verification; they are never retroactively considered cleared for redistribution.
