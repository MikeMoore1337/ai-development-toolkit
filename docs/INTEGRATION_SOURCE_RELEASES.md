# Pinned releases for integration source archives (#190)

[Русская версия](ru/INTEGRATION_SOURCE_RELEASES.md) | [CI source build](../integrations/build_packages.py) | [GitHub Actions workflow](../.github/workflows/publish-integration-sources.yml)

The independent MCP and ChatGPT plugin **source packages** are not Toolkit
`v5.x` releases, not automatic installed-plugin upgrades and not compiled
executables. `mcp_server_version`, Toolkit manifest version and a personal
ChatGPT plugin version are **three distinct values**.

## One-time human promotion, no paid APIs or Codex CLI

1. Identify a 40-character lowercase SHA on protected `main` whose
   [Validate toolkit](../.github/workflows/validate.yml) push run succeeded
   on Ubuntu 3.12/3.13, Windows 3.14, both macOS platforms and the final
   integration source archive job.
2. In GitHub **Actions → Publish pinned integration source ZIPs → Run
   workflow**, choose the default `main` branch and supply `source_sha`.
   This is an explicitly initiated release, never a release on every push.
3. The workflow checks that the SHA is an ancestor of `main`, re-runs
   SHA256/provenance checks, fetches real exact-SHA GitHub CI evidence,
   rebuilds source ZIPs, checks ZIP contents/hash and requires **all six**
   named jobs to have succeeded. Missing permissions/network, unverified
   revision, failed/skipped jobs or unreviewed files abort the publication.
4. The workflow creates a **draft** GitHub Release tagged
   `adt-integrations-<full SHA>` with both versioned source ZIPs,
   `INTEGRATION_SHA256SUMS.txt` and `INTEGRATION_EVIDENCE.json`.
   It re-downloads all four draft assets and compares SHA256 before
   publication. On failure the release stays unpublished for inspection.
   Existing tags/releases cannot be overwritten.
5. If successful, the GitHub Release is published, **not marked Latest**,
   leaving the latest Toolkit application release unaffected. Use the
   archived release assets rather than a 14-day Actions artifact.

**Latest-label safety:** GitHub may still select a newly published source
release as `/releases/latest` even if `--latest=false` was passed. The
manual workflow now requires a pre-existing stable `vX.Y.Z` Latest,
restores that exact tag if GitHub changes the pointer, and checks it again.
If the repository currently shows an integration source tag as Latest, a
maintainer must first mark the actual Toolkit application release Latest
using GitHub's release edit UI. Do not move or recreate ZIP assets.

Do not assume the plugin ZIP from the public repository upgrades a
**separately installed, privately owned ChatGPT plugin**. Confirm the
installed plugin ID and version with the authorized Plugin Creator metadata;
perform any update separately under the plugin's own change controls.
Existing public source ZIP version and live personal plugin version need not
match. Publication must never include private plugin source, tokens or IDs.

## Rollback and verification boundaries

The Windows `Install-ADT-Personal.ps1 -McpOnly` procedure prechecks and
stages both `adt_mcp.py` and `adt_discovery.py`, makes user-local
`*.adt-backup-*` copies and restores the previous pair **if installation
self-check fails**. If the installed client later misbehaves, do not
blindly copy a single old module: the backup can predate the support module.
First inspect the Codex MCP launcher path and both installed source paths,
keep a second copy of the present installation outside project directories
and record hashes. Use a verified matching previous pair or reinstall an
approved pinned package; verify the installed launcher with `--check` and
repeat a real Codex Desktop tool call. Do not reset Git checkout or delete
working backups automatically.

A source ZIP integrity check, synthetic rollback test, or plugin metadata
lookup is not evidence of a live client activation. On a working client,
there is no reason to force a destructive rollback demonstration. Report
`REAL_USER_CLIENT_ROLLBACK=NOT_RUN` until the user explicitly performs it.
