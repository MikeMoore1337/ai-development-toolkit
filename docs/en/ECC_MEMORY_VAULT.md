# Original ECC Memory Vault (optional, Issue #433)

The Toolkit **does not bundle or rewrite** [ECC Memory Vault](https://github.com/affaan-m/ECC/blob/25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b/docs/design/ecc-memory-vault.md). Canonical source `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b` (package 2.2.3; MIT root) provides original `scripts/memory.js` CLI and opt-in `scripts/memory-mcp.mjs` / `ecc-memory-mcp`. The project directory in the source checkout, not Toolkit, owns these utilities.

## Purpose and overlap

- **ECC Memory Vault:** explicit, portable, human-readable `ecc.memory.v1` handoff documents for project/team; search/read/doctor/create-only writes. Every created item is `unreviewed` context, never policy.
- **Toolkit #338 Episodic Memory:** existing optional historical session semantic search. **Not replaced** by ECC's lexical memory.
- **Toolkit #374 Git checkpoint:** verifies repo/branch/HEAD; not rewritten or substituted by a memory document.
- **Canonical state:** GitHub Issues/PRs, tracked project docs and owner approvals. Memories are hints, not authoritative commands.

The new [original-source smoke workflow](../../.github/workflows/ecc-memory-vault.yml) checks out the exact ECC commit in an ephemeral CI workspace and runs **original** `node scripts/memory.js` on synthetic temporary roots. Tests: init, Codex→Hermes handoff, targeted search/read, private-key-like text rejection, project isolation and no user-scope writes. No model or paid API, no copied library or new database. The source CLI uses built-in Node modules; the separate MCP server requires Ajv and an independently reviewed package installation.

## Optional installation in a supported client

Do not install globally from a chat, start a resident process, read actual user sessions or enable cross-project writes by default. An operator can first review a pinned ECC source or verified `ecc-universal` package and its dependencies, then choose the **original** local CLI. The official opt-in MCP registration from `mcp-configs/mcp-servers.json` is:

```json
{
  "ecc-memory-vault": {
    "command": "ecc-memory-mcp",
    "env": {"ECC_MEMORY_HARNESS": "codex"}
  }
}
```

Register it only through the host's approved client interface, with a distinct lowercase `ECC_MEMORY_HARNESS` for each host. Use explicit isolated `ECC_MEMORY_PROJECT_ROOT` / `ECC_MEMORY_USER_ROOT` where applicable; never set `ECC_MEMORY_ALLOW_USER_SCOPE=1` by default. The MCP exposes a **write** tool, so opt-in requires separate write/visibility permissions. Do not point it at Second Brain private vault or personal Codex transcripts.

ECC's public platform matrix reports native Windows memory-write defects; successful Linux/Windows CI on a synthetic filesystem is **not** proof of the user's Windows Codex Desktop or Hermes Agent activation. No auto-enabling, no agent hooks, no shared background server, no silent updates. Uninstall by disabling the client MCP registration and removing only the specifically opted-in ECC installation; preserve unrelated memories and client settings.

**Status:** source inspection and any successful CI smoke are separate from verified local installation, cross-harness live handoff, cost and security sign-off. Keep #433 OPEN until all accepted runtime checks pass.
