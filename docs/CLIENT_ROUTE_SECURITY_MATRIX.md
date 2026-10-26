# Client route security and evidence matrix

[Русский](ru/CLIENT_ROUTE_SECURITY_MATRIX.md) | [Task #389](https://github.com/MikeMoore1337/ai-development-toolkit/issues/389)

**Scope:** Toolkit's actual source contracts at this revision, not a promise about any account's installed clients. Toolkit offers reusable guidance and optional local skill/MCP tooling. Client credentials, subscriptions, billing and session capabilities are owned by each client/provider. This page separates what the repository itself can verify from what needs an independent real-world check.

## How to start and what is actually verified

| Route | Toolkit entry point | Current Toolkit proof | Cost and execution boundary |
| --- | --- | --- | --- |
| ChatGPT ordinary chat | [No-terminal guide](BEGINNER_START.md) + reviewed repository URL/files | Instructions only; per-session access NOT_VERIFIED | Toolkit has no API key or billable call. Hosting plan/tool limits are client-specific. |
| ChatGPT plugin | [Plugin installation and archive guide](../integrations/chatgpt-plugin/README.md) | Offline ZIP/source contract; compatible host import and L4/L5 activation require separate evidence | Import alone does not charge through Toolkit. Account/subscription rules depend on host; no model invocation by the configuration preview. |
| Codex Desktop | [Personal MCP instructions](../integrations/personal-mcp/README.md), or repository guidance | Filesystem/MCP source validation; read-only observations documented separately, no universal installed-client assertion | Desktop entitlement and limits belong to its host/account. No Codex CLI is launched by the preference or route resolver. |
| Codex CLI | [Project MCP](MCP_INSTALL.md) or [Skill Manager](CLIENT_MIGRATION.md) | Offline contract and file installation checks; real execution is NOT_VERIFIED | CLI installation may be usable with a user's own plan or paid account. The project does not make CLI calls or enforce provider quotas. |
| Claude Code CLI | [Project MCP](MCP_INSTALL.md) or [Skill Manager](CLIENT_MIGRATION.md) | Offline contract and file installation checks; real execution is NOT_VERIFIED | Authentication, subscription/API charges and CLI runtime are user's responsibility; never assume zero cost. |
| Claude.ai web chat | [Conversation guidance](CLIENT_CAPABILITIES.md) | Static conversational contract; L4/L5 not generally demonstrated | Browser-host entitlement/limits are not verified by Toolkit. |
| Generic MCP | [Integration overview](INTEGRATIONS.md) | Read-only Toolkit server and configuration contracts; host connection is separately tested | Starting a read-only server does not grant filesystem write, network, model calls or client billing privileges. |
| Direct API | [Policy preview](CLIENT_POLICY_ROUTES.md) | **Policy advisory only**. No provider runner or billing-control adapter in this feature | NOT_IMPLEMENTED as real Toolkit execution. A flag cannot supply spend caps, credentials or permission. |
| Other chats and Harness | [DeepSeek chat guide](../integrations/deepseek-chat/README.md), [Harness guide](../integrations/deepseek-harness/README.md) | Reference/harness contracts only; client activation NOT_TESTED | Do not infer account billing, model availability or native skill activation from static documents. |

**Not a claim of universal client compatibility:** only the explicit offline artifacts above are confirmed. Where a named client has no observed invocation, report `NOT_VERIFIED` rather than `PASS`.

## Security checklist for every route

| Control | Default behavior and what the user must verify |
| --- | --- |
| Authentication / secrets | Toolkit JSON preferences reject unknown keys; store no tokens, session cookies or passwords in Git, examples, logs or `.adt/config.json`. Configure credentials in the selected client's supported private mechanism; Toolkit does not provision them. |
| Cost / quotas | Default `allow_paid_api=false`, `allow_cli_agents=false`, `additional_spend_allowed=false`. Opt-in to a *potential* route is not a spending limit. Verify the provider's pricing, hard cap (if supported), current balance and account quotas before any separate real invocation. If the provider cannot enforce a cap, do not present a local setting as enforcement. |
| Filesystem access | Toolkit route previews read only; Skill Manager file modifications require an explicit, separately reviewed `--apply`. A real agent must obtain task-scoped permission, use an approved workspace and respect existing `AGENTS.md`/project policy. |
| Network access | Preview commands do not contact APIs or run clients. `allow_network` is only a preference, not host network permission. Explicitly approve external access and destination trust in the runtime before any action. |
| Isolation | Use a disposable project or a verified sandbox for experiments; local files, SSH keys, MCP and tool permissions remain host controlled. Do not treat source-only tests as a sandbox or as proof of production safety. |
| Confirmation / cancellation | `ask` means confirmation is needed; there is no silent `allow`. The preview always returns `execution_authorized=false`. Stop a real operation using the client/provider's own cancel and revoke controls, not this script. |
| Windows / Linux / macOS | The Python 3.12+ previews use standard library and are covered by CI across all three systems. Specific host apps, CLI availability, service installers and features differ; verify the selected client's platform support and installed version. |
| Evidence | L1-L3 source/schema checks do not establish L4 discovery, L5 invocation or L6 improvement. Require actual client-session evidence before upgrading statuses. |

## Distinct permission gates and historical locks

The read-only configuration precedence is **defaults < local user < project < task**, with project/task permissions allowed to tighten but not loosen security settings. Inspect it with `python scripts/toolkit_preferences.py --target PATH`, and preview a route with `python scripts/client_policy_route.py --client codex-desktop`.

`scripts/agent_eval_runner.py` still contains `OWNER_REAL_AGENT_EXECUTION_LOCKED = True`. Neither setting `allow_cli_agents` nor `allow_paid_api` disables that source-level gate. Real experiments, quotas, adapters and task-specific confirmations need a separate implementation and explicit authorization. No CLI or paid API is invoked by these examples. Historical experiments are not treated as evidence for an arbitrary new user session.

**Safe offboarding:** remove only the optional local `preferences.json` or project `.adt/config.json` after reviewing other use of those files; use the supported Skill Manager uninstall/rollback for managed skills, and disconnect an MCP/plugin from the host UI if needed. Merely removing preferences does not uninstall external software or revoke provider credentials.
