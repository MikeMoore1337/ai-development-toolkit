# Publishing AI Development Toolkit

The official repository [MikeMoore1337/ai-development-toolkit](https://github.com/MikeMoore1337/ai-development-toolkit) **already exists** and has published [versioned GitHub Releases](https://github.com/MikeMoore1337/ai-development-toolkit/releases). Check the release list for the actual latest tagged version; neither an updated README nor an untagged `main` commit is a release. Do not recreate the official repository or rerun the first-publication script for maintenance.

## Maintaining this repository

1. Create a branch from current `main` and submit a reviewed PR. Keep release history and existing tags unchanged.
2. Run validation, quality, provenance inventory, tests and checksum verification; regenerate the tracked SHA256 inventory through `python scripts/verify_checksums.py --write` only after reviewing the exact diff.
3. Require the existing Linux/Windows GitHub Actions checks on the **exact PR HEAD** before asking for merge approval.
4. Treat merged, untagged `main` work as **Unreleased**. `MANIFEST.json.version` remains the last published baseline until an explicitly approved next release.

## Publishing a new version

Follow the complete [release process](RELEASE_PROCESS.md), including the release-mode provenance gate, owner sign-off for the exact source, checksums, archive verification and tagged SHA checks. CI passing is **not** itself permission to publish. Do not automatically select a future version, create a tag or issue a GitHub Release.

After publication, verify the actual downloaded GitHub-generated archive, inspect the [release workflow](RELEASE_PROCESS.md#independent-verification-of-a-github-source-archive) and retain its evidence.

## Initial publication of a separate fork or new repository only

The legacy `scripts/publish_github.ps1` script was designed for first publication: it validates files, requests an explicit `PUBLISH` confirmation, creates a **public** GitHub repository and pushes `main`. This conditional workflow is **not appropriate** for the already-published official repository. Review its behavior and licensing boundaries separately before using it for a new independent project. Never publish private licenses, credentials or prior distribution archives.

For repository appearance settings, see [GitHub setup](GITHUB_SETUP.md).
