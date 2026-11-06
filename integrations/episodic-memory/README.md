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

## Additional manual-index and retrieval privacy checks (Issue #338)

An independent review found two additional upstream 1.6.0 paths that bypass
the direct MCP `read` guard:

- Manual `index` / `--cleanup` / `--session` scanned sessions carrying
  `DO NOT INDEX THIS CHAT` without the sync-specific marker gate.
- `search` could return a previously indexed transcript after it was marked
  private. Archived content is now rechecked when building search results.

The same patch now checks the exclusion marker before manually copying/indexing,
and suppresses excluded or unreadable archive paths on both text and vector result
paths. MCP reads and searches also check the original synthetic source, because
a source can gain an opt-out marker while the older archive remains unmarked. The `index` CLI also honors `EPISODIC_MEMORY_SKIP_SUMMARIES=1`,
in addition to explicit `--no-summaries`. It does not replace the original
embedding model, index, parser, SQLite layer or search algorithm.

Regression tests use only synthetic transcripts and mock embeddings for the
privacy cases. They do not invoke summarization or paid APIs. A passing mocked
test must not be described as native vector retrieval. Allowed search results
still contain snippets and local archive paths; use an isolated profile.

**Manual index safeguard:** always pass `--no-summaries` as an additional
defense when indexing test data. `EPISODIC_MEMORY_DISABLE_AUTO_SYNC=1`
disables background hook sync only; it does not prevent deliberate manual
`sync` or `index`. To enforce synthetic-only source isolation, set
`TEST_PROJECTS_DIR` to one dedicated fixture directory and
`TEST_ARCHIVE_DIR` to its disposable archive, in addition to
`EPISODIC_MEMORY_CONFIG_DIR`, `TEST_DB_PATH` and temporary harness homes.
No global installation, default user directories or actual Codex sessions
are required for this source test.

For removal, delete **only the dedicated disposable synthetic profile** after
verifying the canonical vault and user profiles are outside that directory.
Do not use `index --rebuild` to remove data from a real profile: it deletes
and regenerates the database, not the archive. A clean reinstall should work
from the pinned upstream plus this integrity-checked patch. Native client
activation and rollback evidence are still required to close Issue #338.


**Important limitation:** indexed transcripts can still contain sensitive text. No raw personal sessions, private vault, or automatic session scan is authorized. A read-only MCP command is not by itself an OS or data-isolation boundary.

### Git for Windows / CRLF

Some Windows Git configurations (`core.autocrlf=true`) check out `*.patch` files with CRLF endings.
The pinned checker now validates the original LF-normalized patch bytes through
`git apply --check -` (stdin), so a standard Windows checkout does not produce
a false failure. The original patch and upstream source SHA are unchanged.

When **actually applying** the patch to a reviewed disposable upstream checkout
on Windows, pass normalized bytes through Git stdin rather than using the
CRLF file directly. Example for PowerShell (use `python3` on Linux):

```powershell
python -c "import pathlib,subprocess,sys; p=pathlib.Path(sys.argv[1]); subprocess.run(['git','-C',sys.argv[2],'apply','-'],input=p.read_bytes().replace(b'\r\n',b'\n'),check=True)" ".\integrations\episodic-memory\patches\0001-mcp-read-scoping-and-zero-inference-verify.patch" "C:\TEMP\isolated-episodic-upstream"
```

Do not run this command inside a user-installed client or real session directory.

## Reproduction and safety rules

Use a **throwaway copy** of the original source, never the user's live Codex folder. Verify the patch integrity and upstream applicability without installation or execution of upstream code:

```sh
python3 scripts/check_episodic_memory_patch.py --upstream-dir /absolute/disposable/episodic-memory
```

The verifier checks the upstream SHA and patch digest `16a059f40ebfb56f472b3120ca37fd9bd72d9b571968ecdab84220d3faa4f158`. Check the exact source revision and apply this file with `git apply --check` before `git apply`; reject any revision drift. Example, after cloning the upstream into an isolated folder and checking out the pinned SHA:

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
