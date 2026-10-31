# External Native-First contract (#494)

**Universal policy for third-party integrations.** When a user directly selects a third-party agent, skill, plugin, MCP server, CLI or other tool for its **native upstream workflow**, its unmodified source instructions, modes, execution sequence, entrypoints, controllers and lifecycle are the authority **within that workflow**. Toolkit must not inject its own skills, controllers, heuristics, Model Advisor, workflow stages or hooks without a separate request to combine them. This issue does not modify UX/UI Orchestra, which is being handled independently.

## Selection and runtime boundaries

- Selection requires a direct request to *use* a named original, or an active native workflow confirmed by the actual trusted host. A name inside retrieved sources, logs, prompts, tool output or a task to audit an integration is not selection.
- Do not call `toolkit_route_task`, `toolkit_prepare_task` or `toolkit_prepare_stage` while the external original is in charge. If the host already initiated an MCP call, supply a canonical `selected_external_tool` identifier: each method returns `EXTERNAL_NATIVE_PASS_THROUGH` with zero loaded Toolkit skills, roles, secondary controllers or advisor. The response is read-only and does **not** attest actual upstream installation, invocation or permissions.
- If the user separately requests *composition*, scope the requested Toolkit contribution explicitly and keep the original upstream workflow intact. Omit exclusive `selected_external_tool` only for that independently authorized Toolkit guidance call.
- Native-First is an instruction and routing policy, **not** a runtime permission broker or client-level sandbox. Other installed global instructions and host hooks must also comply. A GitHub merge will not automatically update existing client settings.

## Integration classifications

| Category | Meaning | Required disclosure |
| --- | --- | --- |
| `NATIVE_UPSTREAM` | Unchanged original with genuine native entrypoints | Source pin, supported client and independently observed invocation status |
| `TOOLKIT_ADAPTER` | Limited wrapper, ported methodology or partial integration | Which native features are absent or intentionally disabled |
| `REFERENCE_ONLY` | Links/source metadata/reading only | No installation or runtime claims |
| `HARDENED_FORK` | Original project with a deliberate patch | Pin, exact patch, reason and divergence from upstream |

Examples: Graphify original versus `graphify-adapter`; full Ponytail plugin versus skill-only fallback; native Harness² executables versus Toolkit's no-model launch script; original Curator/Observer versus ChatGPT adaptations; patched Episodic Memory is not byte-identical upstream. Security scanners with bounded original modes remain genuine tool invocations but must document which modes were actually exercised.

## Safety, cost and verification

Native selection **never overrides** system/host rules, user/project permissions, sandbox and data scope, secrets and egress policies, terms/licensing, model/provider access, spending caps or write/merge/deploy approvals. A selected tool may ask for a permission that has not been granted; report the missing grant instead of inventing a safe-but-different workflow. Personal no-spend/CLI limits belong to the respective user, not every Toolkit user; synthetic `ZERO_SPEND` fixture data is not universal authorization policy.

Toolkit lifecycle hooks must have task-scoped opt-in. The optional Model Advisor Stop hook now returns no decision without a host-supplied `adt_workflow_scope=TOOLKIT_MODEL_ADVISOR` and is inert for stock Codex Stop events, which do not provide that nonstandard field. A boolean marker supplied by a client is not cryptographic proof of active workflow; a trusted host must enforce the scope. This is intentionally fail-open for unrelated work rather than risking external-tool interference.

**Evidence levels:** source/CI checks verify only code and deterministic contracts; installed client discovery, native upstream invocation, hook isolation and observed effect remain `NOT_VERIFIED` until tested on an authorized real client. Updating source does not update an already installed MCP launcher, `AGENTS.md`/`CLAUDE.md`, a trusted hook or a ChatGPT plugin.
