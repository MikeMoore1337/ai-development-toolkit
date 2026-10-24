# Reproducible release procedure

[Русская версия](ru/RELEASE_PROCESS.md)

The repository follows PR-based delivery. CI on a PR is necessary, not a
substitute for independently verifying a tagged public release.

## Published v5.5.0 and v5.5.1 archive errata (2026-10-21)

The historical public GitHub Release [v5.5.0](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.0), tagged at `04d60055e93c04dda26fb3868689ab4031fbf617`. **The published tag still contains `MANIFEST.json.version = 5.4.0`, and its changelog/release instructions still describe v5.4.0 as the last release.** This is a documented metadata discrepancy, not a reason to move or rewrite an immutable release tag. Treat the tag as the published identity, report the stale in-archive version accurately, and track corrective forward-only work in [Issue #153](https://github.com/MikeMoore1337/ai-development-toolkit/issues/153). **The subsequently published [v5.5.1](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.1) is also mismatched:** immutable tag SHA `64f163acc322acc6aecf5b1f44b6f76744505f46` includes `MANIFEST.json.version = 5.4.0`. The intended fix from PR #169 was not merged before the tag was created. Do not rewrite either tag. The v5.5.2 GitHub Release was subsequently published on 2026-10-21 with a matching manifest. Release `v5.5.3` was published on 2026-10-22 with matching manifest version and tag. The previous release workflow lacked tag/manifest matching; the new source-archive workflow includes a fail-closed guard but cannot prevent a release already published. Verify both identities BEFORE creating tags and recheck rights/archives.

## Version and release state

**Release preparation:** `5.5.6` (candidate, NOT PUBLISHED). Its source manifest is ahead of the last published `v5.5.5` tag. This is not a GitHub Release; tag, exact-SHA preflight and verified release archive remain mandatory.

**Latest published release:** [v5.5.5](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.5) (2026-10-24), annotated tag pointing to `2fcc1efb858670a17aa251ba7264cef89cab1c71`. The published archive's `MANIFEST.json.version = 5.5.5`; SHA256 and provenance release checks passed in [tag/release archive CI](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/40090538576). The owner's exact-source rights approval is recorded in [Issue #293](https://github.com/MikeMoore1337/ai-development-toolkit/issues/293#issuecomment-6383332045), not an independent legal assessment. Installed MCP packages and ChatGPT plugins have NOT been updated by this release.

- `v5.5.4` was published on 2026-10-23 from immutable tag commit `5affd7f18e9963eee6cb7692ad4d21d3b6f2c8c7` ([GitHub Release](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.4)); `MANIFEST.json.version = 5.5.4` in the tag. Later `main` commits do not become part of this release automatically.

- The last published tag is **`v5.5.5`**, containing `MANIFEST.json.version = 5.5.5` at commit SHA `2fcc1efb858670a17aa251ba7264cef89cab1c71`. Later `main` commits are not automatically published.
- `CHANGELOG.md` has an `Unreleased` section for changes merged after the published tag. The latest tagged release section is marked `released`, not `prepared`. Historic entries remain unchanged.
- Published release identity is the immutable Git tag and GitHub Release **at its exact SHA**. `main` is a development branch, potentially ahead of that tag. Do not install `main` and describe it as the published archive.
- Only after the release preflight and explicit owner decision may the next version be chosen, the manifest updated, and a separate release PR/tag prepared. CI never publishes a version automatically.
- Source status is not runtime evidence: verified static format or successful copy does not prove client discovery, activation or improvement.

Last published tag: [v5.5.5](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.5) at commit SHA `2fcc1efb858670a17aa251ba7264cef89cab1c71` (2026-10-24), with matching manifest version `5.5.5`. [Compare v5.5.5...main](https://github.com/MikeMoore1337/ai-development-toolkit/compare/v5.5.5...main) for subsequent changes.


After publication of a new GitHub Release, align both README files, this RU/EN guide and the latest CHANGELOG section in a follow-up PR. The `release: published` workflow independently compares the published tag with the documents on `main`; a stale reference fails a separate documentation job. This cannot undo a published release or rewrite historical tags.

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
11. Before tagging, run the read-only **live pre-tag gate** on the clean, already-merged exact SHA:

    ```bash
    python scripts/pre_tag_preflight.py --tag vX.Y.Z --sha EXACT_40_CHAR_SHA
    ```

    Replace the placeholders with the intended **new** release tag and merged commit. The gate verifies the local manifest, clean worktree, local HEAD, unused local and GitHub tag, exact remote `main` SHA, and all three required GitHub CI check runs on that SHA. GitHub read access and network are required; `GITHUB_TOKEN` is optional if public anonymous requests are available. It **fails closed** on missing information and never creates a tag or authorizes rights, publication or release. The command can be run on Windows, Linux or macOS from a clean checkout. For CI, the offline unit tests use synthetic GitHub results only.

12. Before tagging, verify the intended release **on the exact commit** rather than assuming `main` and the PR HEAD are identical. Replace `vX.Y.Z` with a new unused tag and verify that GitHub does not already contain it. The example is read-only and does not create a tag:

    ```powershell
    $tag = "vX.Y.Z"
    if ($tag -notmatch '^v[0-9]+\.[0-9]+\.[0-9]+$') { throw "RELEASE_TAG_NOT_SELECTED" }
    if (git tag --list $tag) { throw "RELEASE_TAG_EXISTS_LOCALLY" }
    $sha = "<EXACT_MERGED_AND_CI_VERIFIED_40_CHAR_SHA>"
    if ($sha -notmatch '^[0-9a-f]{40}$') { throw "RELEASE_SHA_NOT_PINNED" }
    if ((git rev-parse HEAD).Trim() -cne $sha) { throw "RELEASE_WRONG_HEAD_SHA" }
    $taggedManifest = git show "${sha}:MANIFEST.json" | ConvertFrom-Json
    if ($taggedManifest.version -cne $tag.Substring(1)) { throw "TAG_MANIFEST_VERSION_MISMATCH" }
    ```

    Also check all required CI results **for this exact SHA**, inspect the final diff and get separate owner release-rights approval for that artifact. Never tag a different main HEAD or reuse any previously published tag.
13. After successful CI on `main` AND the release rights gate, tag the exact validated SHA, publish
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
$tag = "vX.Y.Z"
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
This workflow checks actual downloaded bytes and rejects a mismatched `MANIFEST.json.version` versus tag. **It runs after a tag event and cannot undo an incorrect release already created.**

New tagged archives are checked against the provenance release gate after SHA verification. Historic archives without the provenance script are reported as `NOT_VERIFIED` for licensing while retaining their independent checksum verification; they are never retroactively considered cleared for redistribution.
