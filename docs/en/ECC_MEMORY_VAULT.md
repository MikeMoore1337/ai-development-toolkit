# Toolkit Native Memory / Handoff (#433)

Toolkit now provides **manual, project-bound cross-client handoff references** in its existing Git checkpoint utility, without ECC, `ecc-universal`, `ecc-memory-mcp`, a separate daemon or a model API. This is a **first native tranche**, not a full Memory Vault search/write service.

## What is implemented

The existing [#374 Git checkpoint](../../scripts/session_handoff_checkpoint.py) now supports `capture-handoff` and `verify-handoff`. A version-2 JSON packet contains: a GitHub Issue, up to eight **same-project** Issue/PR links, sender/recipient client identifiers, a fixed next-action category and the original local Git checkpoint. It never contains free-form instructions, transcripts, private keys, conversation text or arbitrary memory. No chat/client history is accessed.

The packet is **unreviewed, not policy, not owner consent**. The SHA-256 detects accidental modification of the file, **not malicious forgery**: any actor can recompute it. A successful check establishes only local repo-path identity, branch, commit and tracked status correspondence, not the truth of cited claims. Cross-machine relocation yields a stale `repo_id` rather than a false PASS; review the authoritative GitHub Issue/PR before continuing.

## Explicit opt-in usage

Create a file in an existing directory **outside the project checkout**. The destination path must be absolute and not pass through a symlink:

```sh
python scripts/session_handoff_checkpoint.py capture-handoff --repo /path/to/project \
  --issue https://github.com/OWNER/REPO/issues/123 \
  --from-client codex --to-client hermes \
  --ref https://github.com/OWNER/REPO/pull/124 \
  --next-action REVIEW_PR --file /path/to/external/handoff.json

python scripts/session_handoff_checkpoint.py verify-handoff --repo /path/to/project \
  --to-client hermes --file /path/to/external/handoff.json
python -m unittest discover -s tests -p test_session_handoff_checkpoint.py -v
```

The writer uses create-only, fails if the file already exists, and sets mode 0600 on POSIX. The recipient explicitly verifies the packet before manually opening its links. Actions are `REVIEW_ISSUE`, `REVIEW_PR`, `RUN_TESTS`, `CHECK_CI`, `WAIT_FOR_OWNER` or `NONE`. A wrong recipient, cross-project link, unrecognized/missing GitHub `origin`, stale Git state, tampered data, symlink or malformed packet fails closed. The checkout must have a GitHub HTTPS or SSH `origin` matching the Issue's owner/repository (checked locally, no network). Do not commit these local handoffs; delete the specific file to roll back. No global AGENTS, MCP configuration, hooks or user-scope files are changed.

## Overlap and remaining work

- [#338 Episodic Memory](../../integrations/episodic-memory/README.md) is historical-session search, not replaced here.
- #374 remains a standalone Git metadata checkpoint; existing v1 capture/verify work unchanged.
- GitHub Issues/PRs and explicitly approved project docs remain authoritative; a packet is a pointer, never an instruction.
- The historical [original ECC source-smoke workflow](../../.github/workflows/ecc-memory-vault.yml) proves only an ephemeral upstream test. **Installing or launching ECC is not a Toolkit requirement.**
- Search, persistence in Toolkit-owned memory, explicit reviewed decision summaries, secure cross-device authentication, optional MCP read surfaces, live Codex Desktop ↔ Hermes use and published Toolkit release are **NOT_IMPLEMENTED / NOT_VERIFIED**. Keep #433 OPEN until independently accepted.

Pinned comparison source: [ECC 2.2.3 at `25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`](https://github.com/affaan-m/ECC/tree/25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b), MIT. This specific packet implementation uses Toolkit's existing Python code, not copied ECC source. No Codex CLI, Claude CLI, paid APIs, hidden client activation or additional spending.

## Exact-issue native handoff search (#433)

An additional **manual, read-only** capability finds previously created handoff packets in an **explicit** directory (outside the checkout). It does not create a database, ingest chat transcripts, index user data globally, or run an external ECC component. It searches only the exact GitHub Issue URL and named recipient, not natural language:

```sh
python scripts/session_handoff_checkpoint.py search-handoffs --repo /path/to/repo --directory /path/to/external/packets --issue https://github.com/OWNER/REPO/issues/123 --to-client hermes
```

Only up to 16 strictly named small JSON packet files are accepted in that folder. Linked directories/files, unexpected extensions, mixed GitHub projects, forged digests, unexpected schema, duplicates and paths inside the repository are refused. A matching `PASS` requires the existing complete v2 digest check, same-project origin, recipient and unchanged local Git state. Stale handoffs can be listed with `git_check=STALE`, but their references and next action are **withheld**. No matching valid record produces `REVIEW_REQUIRED` rather than a false search success. The result includes at most the known public GitHub Issue/PR URLs, safe digest, fixed action enum and statuses - never absolute paths or handoff file names.

**Scope:** exact-link lookup for an explicitly captured packet, not semantic memory, authenticated sender identity, human-approved reusable practice or cross-device sync. The older #338 Episodic Memory remains separate. No Codex Desktop runtime or true client handoff E2E has been verified. This source-level slice does not close #433.

## Toolkit Project MCP read-only handoff surface (#433)

The existing opt-in Toolkit Project MCP now exposes two **native read-only** tools; you do not need to install ECC Memory Vault or another MCP service:

- `toolkit_search_handoffs`: arguments `project` (exact absolute Git root), `directory` (existing absolute external folder), `issue_url` (same-repo GitHub Issue), `to_client` (recipient slug). Delegates to the already released `search_handoffs` parser, including its 16-packet bound, integrity and stale-state rules.
- `toolkit_verify_handoff`: arguments `project`, `file` (one absolute named `.json` packet outside checkout), `to_client`. Delegates to the existing `verify_handoff` verifier. Does not produce a new packet or modify the repository.

These tools only work **after the user explicitly installs Toolkit Project MCP** in an approved client and explicitly invokes them. The server does not automatically enumerate a home folder, listen in the background, sync other machines, ingest conversation text or make requests to GitHub. In responses, `trust=UNREVIEWED` and `owner_approval=NOT_GRANTED` remain fixed; a SHA-256 match does not attest the sender or authorize execution. A stale handoff supplies no reference links or next action. Invalid project roots, foreign Issue URLs, extra arguments, linked files and malformed packet data fail closed. There are no new API fees or CLI agents.

**Source-level tests do not prove Codex Desktop discovery or real Codex→Hermes→Codex handoff.** The historical #338 episodic memory and versioned release are separate. No semantic search, reviewed-memory persistence or authenticated cross-device transfer is claimed. Rollback: disable the Toolkit Project MCP tool or revert this repository revision.

## Project MCP in-memory packet preparation (#433)

A third **read-only** Project MCP tool, `toolkit_prepare_handoff`, returns a complete native v2 `packet` **in memory only**. It needs the exact absolute `project` Git root, same-project `issue_url`, `from_client`, `to_client`, `references` (0–8 same-project public Issue/PR URLs), and an explicit enumerated `next_action` (`REVIEW_ISSUE`, `REVIEW_PR`, `RUN_TESTS`, `CHECK_CI`, `WAIT_FOR_OWNER`, or `NONE`). No arbitrary prose, raw chat history, secrets or shell commands are accepted in the packet schema.

The result embeds `packet` with `trust=UNREVIEWED`, `owner_approval=NOT_GRANTED`, SHA-256 integrity (not a signature), and `packet_storage=NOT_PERSISTED`. **The MCP does not write the packet to a file**, transfer it to Hermes or authorize the proposed action. The operator can choose to save it outside the repository and run existing `toolkit_verify_handoff` / `toolkit_search_handoffs` later; the existing native CLI `capture-handoff` is the supported create-only disk operation.

A synthetic real-Git test constructs the same packet via MCP, explicitly writes it in an isolated external temporary folder, then verifies/searches via the MCP tools. It verifies only source-level protocol interoperability, **not** real Codex Desktop or Hermes handoff, persistent reviewed memory or client permissions. There is no ECC runtime, paid API, additional daemon or automatic state transition.

## Explicit cross-device Git comparison (#433)

Toolkit Project MCP additionally offers **read-only** `toolkit_verify_portable_handoff` with exact `project`, external `file`, and `to_client`. The matching native CLI mode is:

```sh
python scripts/session_handoff_checkpoint.py verify-portable-handoff --repo /path/to/recipient/repository --file /path/to/manual/handoff.json --to-client hermes
```

This optional mode is for an **operator-copied v2 JSON packet**, not automatic file transfer or synchronization. Unlike strict `verify-handoff`, it tolerates a different machine's absolute project path. It still requires a matching GitHub `origin`, packet integrity, recipient, branch, commit and tracked Git status. Any mismatch other than the local path identity returns `BLOCKED` or `STALE` with **no references**. The response on a match is always `REVIEW_REQUIRED` (CLI exit code 2), `sender_identity=NOT_VERIFIED`, `owner_approval=NOT_GRANTED`, and a fixed `REVIEW_ISSUE` next step; the packet's suggested action is never authorized. SHA-256 remains a non-authenticating checksum. A changed origin or a malicious packet cannot be treated as an authenticated sender, even when the hash matches. Read the authoritative GitHub Issue/PR before deciding what to do.

**Not delivered by this mode:** human-reviewed persistent memory, semantic retrieval (#338), authenticated sender/device identity, transport, Codex Desktop ↔ Hermes real-client activation, or a public Toolkit release. Roll back by reverting the revision or not invoking the new MCP tool/CLI mode. No new state, service, paid inference, ECC dependency or client settings are created.

## Project-reviewed reference records - explicit opt-in (#433)

The existing manual, create-only JSON writer is reused by `scripts/reviewed_memory.py`: **no extra database, ECC runtime, MCP server or #338 semantic index** is created. An operator can inspect an actual public GitHub Issue/PR comment, then explicitly record a small project-scoped reference. The record contains only an exact same-repository Issue URL, a specific GitHub comment/review permalink, one `DECISION`/`PRACTICE`/`LIMITATION` category, a one-line 8-240 character summary, up to 8 public same-project references and a non-authenticating SHA-256 checksum. The summary is untrusted **data**, not executable instructions. Secret-like strings, paths, emails, arbitrary URLs, multiline text and cross-project references are rejected. The writer refuses overwriting and checkout-path writes.

```sh
python scripts/reviewed_memory.py prepare --repo /path/to/repo --issue https://github.com/ORG/REPO/issues/123 --review-url https://github.com/ORG/REPO/issues/123#issuecomment-456 --kind DECISION --summary "Manual review chose the existing integration path."
python scripts/reviewed_memory.py record --repo /path/to/repo --issue https://github.com/ORG/REPO/issues/123 --review-url https://github.com/ORG/REPO/issues/123#issuecomment-456 --kind DECISION --summary "Manual review chose the existing integration path." --file /external/manual-memory/decision-123.json --operator-reviewed
python scripts/reviewed_memory.py search --repo /path/to/repo --directory /external/manual-memory --issue https://github.com/ORG/REPO/issues/123
```

`prepare` **never saves**. The opt-in `record` command is a separate local operator action; no Project MCP write capability is added. Three Project MCP **read-only** tools `toolkit_prepare_reviewed_memory`, `toolkit_read_reviewed_memory`, and `toolkit_search_reviewed_memory` expose previews, one explicit external file, and exact-Issue lookup in one selected directory (max 16 entries). A record can be copied between machines manually because its project key is the same-repository GitHub origin, not a private absolute filesystem path. Deleting the selected JSON file removes the record; no background process or user-scope scan is involved.

**Limits:** `--operator-reviewed` represents a *local operator claim*, **not authenticated human review**. The stored review permalink is **not fetched or verified** and may be forged; SHA-256 protects against accidental corruption, not malicious authors. All retrieval returns `REVIEW_REQUIRED`, `trust=UNTRUSTED_REFERENCE`, `review_attestation=NOT_VERIFIED`, `owner_approval=NOT_GRANTED`, with no action execution. The memory index is lexical/exact-Issue, not #338 episodic semantic memory or a canonical policy source. Cross-device transport, authenticated reviewers, client opt-in installation, real Codex Desktop ↔ Hermes E2E and a versioned Toolkit release remain **NOT_VERIFIED**.
