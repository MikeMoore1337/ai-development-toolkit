# ECC as an external Codex plugin (Issue #424)

**Status (2026-10-27): SOURCE_VERIFIED / CODEX_DESKTOP_NOT_VERIFIED / NOT_INSTALLED_BY_THIS_REPOSITORY.** This is an original-upstream integration guide, not an installer, runtime attestation, or authorization for additional agent privileges.

## Verified source

- Upstream: https://github.com/affaan-m/ECC
- Inspected commit: [`25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`](https://github.com/affaan-m/ECC/tree/25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b).
- Original `.codex-plugin/plugin.json`: `ecc`, version `2.2.3`, `skills: ./skills/`, `mcpServers: ./.mcp.json`, `hooks: ./hooks/codex-hooks.json`.
- Git blob SHAs (**not** SHA-256): manifest `c24f7453c8a455105a839842a2408688e3b2b559`; MCP `9860a4dbeafc26ce2233df1a0914916feb543582`; hook `2028143428bc5b09ddf3c4af82ba9a6036d1e1f7`.
- Root LICENSE declares MIT; it does not establish third-party dependency rights or executable-script safety.
- [Original Codex plugin instructions](https://github.com/affaan-m/ECC/blob/main/.codex-plugin/README.md). Updating requires a fresh source review and version pin.

## As-is contents and overlap

| ECC surface | Inspected fact | Existing Toolkit / decision |
|---|---|---|
| Skills | External `./skills/`; plugin description advertises 281 | Toolkit already has scoping, implementation, QA, review, security and release skills. Do not copy or replace; invoke a deliberately selected ECC skill |
| MCP | `.mcp.json` starts `npx -y chrome-devtools-mcp@1.10.1` | Potential download and browser access. **Never authorize launch automatically**; check permissions, network, session sensitivity and cost first |
| Hook | `SessionStart` runs `node -e ...` and ECC bootstrap scripts | Executable code; requires separate inspection and trust in the client's native hook UI |
| Configuration | Plugin is enabled for active `CODEX_HOME` | One original installation across projects, no repository copies, no AGENTS.md/Model Advisor/personal MCP replacement |
| Memory and related integrations | Upstream descriptions are not proof of activation | Do not enable shared memory, background jobs or new providers without separate approval |

## Toolkit-managed discoverability (#424)

Toolkit's `.agents/plugins/marketplace.json` now includes **only an opt-in marketplace entry** for the original ECC (`source: url`, `https://github.com/affaan-m/ECC.git`, `sha: 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, `installation: AVAILABLE`, `authentication: ON_INSTALL`). This retains the existing Toolkit plugin and **does not install ECC**, run `npx`, enable hooks or start MCP. In a supported graphical Codex trusted project, ECC should appear under `AI Development Toolkit (local)` after a marketplace refresh/restart; the user must install `ecc` separately and review permissions. Listing is not execution; Windows Desktop display and install remain `NOT_VERIFIED`. Source format: [official documentation](https://developers.openai.com/plugins/build/plugins#marketplace-metadata).

## Graphical Codex installation (no Codex CLI)

1. In **Codex inside the ChatGPT desktop app**, where supported, open **Plugins** and choose **Add plugin marketplace**, with source `affaan-m/ECC`. If supported, pin the reviewed Git commit above. If the UI cannot pin a ref, **do not claim a pinned install** and inspect the actual source before proceeding.
2. Choose the upstream `ecc` entry and review its version, manifest and requested permissions. Do not implicitly approve `npx`, browser access, or lifecycle hooks.
3. Install through the client UI only after explicit permissions review. Restart the Codex session and perform one small **synthetic** test with an original ECC skill; installed registration is not execution evidence.
4. Review `SessionStart` independently in the native hooks UI before any trust decision. Confirm the Chrome DevTools MCP can remain inactive/untrusted until explicitly needed, without production browser profiles or cookies.
5. If a supported GUI, review/deny controls or trust boundary are unavailable, report **BLOCKED/NOT_VERIFIED** rather than switching the repository owner to Codex CLI, Claude CLI or paid APIs. Other users may independently opt in to routes allowed by their own policy.

**Not observed in this work:** the owner's Codex Desktop version, actual ECC registration/execution, hook approvals, network effects or verified zero-spend. See [OpenAI plugin documentation](https://developers.openai.com/plugins/build/plugins) for the generic graphical marketplace flow.

## Verification, uninstall and rollback

- **Before:** inspect existing `AGENTS.md`, `MANIFEST.json`, `docs/EXTERNAL_METHODS_ADOPTION.md`, model permissions, active MCPs, and installed plugin inventory. Similar skill names do not imply equal contracts.
- **Live acceptance:** record Codex Desktop build, selected source revision if observable, ECC presence, one observed original skill invocation on synthetic data, separate MCP/hook permissions, and outputs. Unavailable evidence is `NOT_VERIFIED`; a denied permission is `BLOCKED`.
- **Disable/remove:** use the client Plugins UI to disable ECC; if appropriate, remove the plugin and marketplace. In a new session verify ECC is unavailable and Toolkit still works. Never delete unrelated CODEX_HOME content or other project assets.
- **Update:** review upstream commit/manifest/MCP/hooks/dependencies afresh, re-review changed hook hashes and do not auto-update.
- **Authority:** plugin installation does not authorize secrets, shell, network, publication, production changes or spending. Observed cost and authorization remain separate from documentation.

## Definition of done

The documentation can be delivered by ordinary Toolkit PR/CI without executing ECC. **Issue #424 still requires real Windows Codex Desktop acceptance**, including explicit permission review and a verified original-skill invocation. Source review/green CI is not equivalent to an installed, working plugin; keep the issue open until this is observed.
