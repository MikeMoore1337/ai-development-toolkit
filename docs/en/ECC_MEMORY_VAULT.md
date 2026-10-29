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
