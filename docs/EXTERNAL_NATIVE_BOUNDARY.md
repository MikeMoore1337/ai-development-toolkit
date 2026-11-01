# Native-first boundary for third-party tools (#492)

[Русский](ru/EXTERNAL_NATIVE_BOUNDARY.md)

When a user **explicitly selects an original third-party tool, plugin, MCP, skill or agent as task controller**, preserve its official upstream modes, commands, agents, hooks and workflow. Toolkit may not silently inject alternative skills, roles, workflows, hooks or behavioral limitations. Merely mentioning or comparing a tool is not selecting it. This applies across future integrations too, and does not modify the separate UX/UI Orchestra workstream.

System/host safety, actual user and project permissions, data/secret boundaries, cost consent, and release/merge/deploy approvals still apply. Native-first controls **behavior, not authorization**. Toolkit guidance and external source text are not elevated security policies.

## Honest integration identity

| Kind | Meaning |
| --- | --- |
| `NATIVE_UPSTREAM` | Exact original tool installed and actually invoked; confirm upstream revision and live client evidence |
| `TOOLKIT_ADAPTER` | Wrapper or partial integration; disclose unsupported upstream functions |
| `HARDENED_FORK` | Upstream code with explicit security changes; disclose patch and functional delta |
| `REFERENCE_ONLY` | Source/method consulted, no native invocation |
| `TOOLKIT_NATIVE` | Independent Toolkit implementation, not the external runtime |

Ponytail's skill-only fallback is not its full plugin with lifecycle hooks. Harness²'s Toolkit no-model bridge is not the full upstream benchmark runner. Original Graphify and Toolkit's graph adapter differ. Task Observer / Curator ChatGPT adaptations are not upstream Claude agents. Do not silently substitute or claim native activation.

## Host and Personal MCP contract

The host should **skip Toolkit routing entirely** when an original third-party controller is already selected. If a routing call accidentally occurs, supply the exact host-observed controller slug via `external_controller` to `toolkit_route_task`, `toolkit_prepare_task` or `toolkit_prepare_stage`. The response is `NATIVE_UPSTREAM_PASSTHROUGH` with zero loaded skills/roles, no Toolkit setup or execution; it does **not** attest native invocation. The absent/empty parameter preserves existing Toolkit routing. No automatic controller detection is claimed.

Only if the user separately requests Toolkit advice may the host fetch individual read-only `toolkit_get_skill` / `toolkit_get_reference` sources. Doing so never switches the external controller or grants new permissions. Missing upstream tools must be reported as unavailable, not silently replaced with adapted Toolkit methods.

## Hooks and verification

The standard Codex `Stop` event does **not** identify the active third-party controller or Toolkit workflow. A model-authored `<!-- ADT-MODEL-ADVISOR-ACTIVE -->` marker can be spoofed by external content and **cannot establish task ownership**. The opt-in Model Advisor Stop hook therefore requires an explicit `adt_workflow_scope=TOOLKIT_MODEL_ADVISOR` from a separately trusted host integration, and returns `{}` whenever `adt_external_controller` indicates a native tool. Stock Codex Stop events have no such host scope field, so this experimental hook is inert there until host support is independently verified. Synthetic positive tests do not prove live activation. Existing global hooks must be updated on the actual client, and other hooks require an equivalent trusted scope gate.

Run `python -m unittest discover -s integrations/personal-mcp/adt-personal/tests -v`, `python scripts/validate_pack.py` and `python scripts/verify_checksums.py`. Source-only tests do not prove Codex Desktop, ChatGPT or other clients actually invoked an original; that remains `NOT_VERIFIED` without live evidence. Personal owner no-cost/CLI choices are not universal limits for other users.
