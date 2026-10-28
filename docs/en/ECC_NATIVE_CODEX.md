# Archive: external ECC Codex plugin is superseded (#424)

**Owner decision, 28 October 2026:** Toolkit is a **standalone competitor** to ECC, not an upstream ECC wrapper/add-on. Installing or registering `affaan-m/ECC`, `ecc-universal`, `ecc-memory-mcp`, the ECC Codex marketplace/plugin, hooks or sidecar must **not be required** for any Toolkit product feature. [Issue #424](https://github.com/MikeMoore1337/ai-development-toolkit/issues/424) is closed as `NOT_PLANNED`; [program #431](https://github.com/MikeMoore1337/ai-development-toolkit/issues/431) and [migration #446](https://github.com/MikeMoore1337/ai-development-toolkit/issues/446) are authoritative.

## Historical source review

ECC 2.2.3 was inspected at commit `25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`. The original Codex plugin advertises skills, MCP and hooks including executable SessionStart and Chrome DevTools MCP surfaces. This information is for source/permission comparison only, **not for installing the plugin**. Upstream: https://github.com/affaan-m/ECC. Root MIT license claims do not independently certify all third-party components.

## Native product direction

- Port permissible upstream source with attribution, or implement genuine missing capabilities **inside existing Toolkit modules**: Skill Manager, MCP, security/QA, memory and handoffs, learning, receipts/evals, hooks, profiles and worktree orchestration.
- Do not add a parallel model router, authority, controller or mandatory ECC CLI/sidecar; do not copy overlapping capabilities or bypass client permission gates.
- Upstream CI source-smokes from [#432](https://github.com/MikeMoore1337/ai-development-toolkit/issues/432), [#433](https://github.com/MikeMoore1337/ai-development-toolkit/issues/433), [#434](https://github.com/MikeMoore1337/ai-development-toolkit/issues/434) and the [601 component source inventory #435](https://github.com/MikeMoore1337/ai-development-toolkit/issues/435) are **reference evidence**, not Toolkit-native feature availability. Upstream comparison workflows are maintenance-only manual tests, not ordinary PR runtime dependencies.
- For this owner: no Codex CLI, Claude CLI, paid API or added expenses; existing Codex Desktop Plus permissions apply. Optional client choices for other users must never require ECC.

**Acceptance:** a user installs only Toolkit, can invoke the integrated feature through supported Toolkit interfaces, passes deterministic positive/negative, permissions, rollback and exact-head CI gates. Live client activation is separately VERIFIED or NOT_VERIFIED, not inferred from upstream tests.
