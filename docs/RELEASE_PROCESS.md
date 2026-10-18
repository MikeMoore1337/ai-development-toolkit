# Reproducible release procedure

The repository follows PR-based delivery. CI on a PR is necessary, not a
substitute for independently verifying a tagged public release.

1. Work on a feature branch and document what changed and any migration risks.
2. Run `python -m pip install -r requirements-dev.txt`.
3. Run `python scripts/check_public_package.py` and
   `python scripts/validate_pack.py`.
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
10. After successful CI on `main`, tag the exact validated SHA, publish
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
$tag = "v5.3.1"
$zip = Join-Path $env:TEMP "adt-$tag.zip"
$dest = Join-Path $env:TEMP "adt-$tag-source"
if (Test-Path $dest) { throw "Destination must be fresh: $dest" }
Invoke-WebRequest "https://github.com/MikeMoore1337/ai-development-toolkit/archive/refs/tags/$tag.zip" -OutFile $zip
Expand-Archive -LiteralPath $zip -DestinationPath $dest
$root = Get-ChildItem $dest -Directory | Select-Object -First 1
python scripts/verify_checksums.py --archive-root $root.FullName
```

The archive check compares SHA256 values **and requires every extracted source
file to appear exactly once** in `SHA256SUMS.txt`. It rejects missing, extra,
linked and unlisted files. Git worktree mode uses `git ls-files -z` for the
canonical tracked inventory, so new tracked files also require checksums.

This does not authenticate the download or prove publisher identity: verify
the intended tag commit and GitHub workflow results separately. Publication
requires a real execution record for archive verification; merely documenting
this procedure is not evidence that the archive was downloaded.
