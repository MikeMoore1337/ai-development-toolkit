# Episodic Memory: isolated, optional upstream patch

**Scope:** Toolkit issue [#338](https://github.com/MikeMoore1337/ai-development-toolkit/issues/338). This directory is a reproducible **patch for the original project**, not a second memory engine, bundled plugin, installed client, or production deployment.

- Original: [obra/episodic-memory](https://github.com/obra/episodic-memory)
- Immutable source revision: `7e06519357777badd7a115d2014a7ef845904310`
- Upstream release: `1.6.0`, license: **MIT**
- Patch: `patches/0001-mcp-read-scoping-and-zero-inference-verify.patch`
- Fork decision: **only if native client adoption is authorized and upstream does not accept the small security correction**. Do not rebuild semantic search.

## Why this patch exists

In upstream 1.6.0, MCP `read` takes an arbitrary absolute path and checks only that the file exists. In an offline synthetic reproduction, an explicitly `DO NOT INDEX THIS CHAT` transcript was readable through MCP even though it did not appear in the index.

The minimal patch:

1. Requires an absolute path under the canonical archive (including realpath traversal checks).
2. Permits `read` only for files present in local SQLite `exchanges.archive_path`.
3. Re-checks explicit no-index markers **at read time**, including a file marked private after indexing.
4. Makes `index --verify` treat deliberately absent AI summaries as normal when `EPISODIC_MEMORY_SKIP_SUMMARIES=1`; `--repair` also respects this flag.
5. Adds positive and negative upstream MCP regression tests.

**Important limitation:** indexed transcripts can still contain sensitive text. No raw personal sessions, private vault, or automatic session scan is authorized. A read-only MCP command is not by itself an OS or data-isolation boundary.

## Reproduction and safety rules

Use a **throwaway copy** of the original source, never the user's live Codex folder. Verify the patch integrity and upstream applicability without installation or execution of upstream code:

```sh
python3 scripts/check_episodic_memory_patch.py --upstream-dir /absolute/disposable/episodic-memory
```

The verifier checks the upstream SHA and patch digest `26202d49f6a37fa3dabbe53a4f048398b1a0e129624e1c20d2da90166c2ba5e6`. Check the exact source revision and apply this file with `git apply --check` before `git apply`; reject any revision drift. Example, after cloning the upstream into an isolated folder and checking out the pinned SHA:

```sh
git rev-parse HEAD
git apply --check /path/to/toolkit/integrations/episodic-memory/patches/0001-mcp-read-scoping-and-zero-inference-verify.patch
git apply /path/to/toolkit/integrations/episodic-memory/patches/0001-mcp-read-scoping-and-zero-inference-verify.patch
```

Upstream does **not** commit a root `package-lock.json`; `npm ci` cannot run on a fresh original clone without creating a local lock. Installation may invoke native addon builds and network downloads. Dependency inspection and separate permission are required **before** installation in an actual client; never run unattended install scripts. Disable model-based summarization and automatic ingestion:

```sh
export EPISODIC_MEMORY_SKIP_SUMMARIES=1
export EPISODIC_MEMORY_DISABLE_AUTO_SYNC=1
export EPISODIC_MEMORY_CONFIG_DIR=/absolute/synthetic-only/location
export CODEX_HOME=/absolute/synthetic-only/location
```

These are examples for a disposable Linux sandbox. Windows environment configuration must be separately reviewed. Do not call Codex CLI, enable hooks, perform inference, or connect private user sessions as part of this pilot.

## Executed evidence (25 October 2026)

- Approved BRC Linux/Docker isolated sandbox; Node `24.22.0`, upstream exact SHA as above.
- Original Episodic Memory offline search indexed one **synthetic** Codex-shaped JSONL session with two exchanges: English/Russian queries retrieved intended exchanges as top matches (64%, 73%, 71%). Local embeddings and SQLite; summaries disabled; no paid calls.
- Confirmed original MCP `read` exposed a synthetic explicitly excluded file. Reproduced and fixed in isolated source.
- Patched TypeScript `tsc --noEmit`: PASS; MCP bundler: PASS; `vitest test/mcp-server.test.ts test/verify.test.ts --maxWorkers=1`: **13/13 PASS**.
- Manual end-to-end stdio check: allowed indexed read PASS, indexed-to-private transition DENIED, non-indexed archive DENIED, direct excluded input DENIED, traversal DENIED.
- `index --verify` with skip-summaries now exits 0 for a healthy index; no summary/inference call performed.
- **Native Windows deployment and client activation: NOT_RUN** (the native Windows BRC endpoint was unavailable and Codex CLI is explicitly prohibited). Full third-party dependency safety beyond the inspected components: NOT_VERIFIED.

## Promotion / removal

Do not publish the upstream plugin as bundled Toolkit content, expose a remote endpoint, grant vault access, or modify production services. The only change in Toolkit is this optional patch and its documentation. For rollback, discard the isolated patched upstream worktree and its dedicated synthetic-only archive, after confirming it is not the canonical vault. No production changes to revert.

**Decision:** offline functional security patch `PASS`; real user-data activation `NO_GO` pending an allowed, verifiable local client pathway, native Windows proof, and explicit data-scope review.


## Windows-hosted source compatibility smoke (no Codex CLI)

A narrowly scoped GitHub Actions workflow (`.github/workflows/episodic-memory-windows.yml`) checks the **actual pinned upstream source** on a temporary Windows runner. It is invoked on related PRs / pushes and can be started manually. It fetches the exact upstream SHA, validates the patch checksum, applies the patch, installs npm dependencies with lifecycle scripts disabled, rebuilds local `better-sqlite3`, verifies `sqlite-vec`, compiles TypeScript, and exercises the real patched MCP/verify regression tests.

The workflow has `contents: read` permissions. No API keys, external model calls, Codex CLI, native personal Windows files, or real chat history are supplied. All data and compiled files reside in the disposable runner. A Windows CI `SUCCESS` proves **source compatibility on that runner**, not installation, rollback, or activation on the owner's device.

The upstream source intentionally lacks a committed npm lockfile; therefore this runner's dependency installation is **not fully reproducible**. A native client deployment still requires a separate reviewed dependency lock and an approved writable connection to the actual Windows host. The offline pilot remains opt-in and must not change `CODEX_HOME` for a real user.
