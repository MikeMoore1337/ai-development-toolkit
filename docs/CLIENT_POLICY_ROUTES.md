# Client policy routes - offline and opt-in

[Русская версия](ru/CLIENT_POLICY_ROUTES.md) | [Issue #395](https://github.com/MikeMoore1337/ai-development-toolkit/issues/395) | [Per-client security and cost matrix](CLIENT_ROUTE_SECURITY_MATRIX.md)

Toolkit separates **available product routes**, **user permission preferences**, **actual client installation**, **in-session capability evidence**, and **real execution authorization**. An opt-in cannot prove installation, skill invocation, absence of paid charges, or approval for a real action.

`client_policy_route.py` reuses `toolkit_preferences.py`, `client_capabilities.py` and the existing validated filesystem/conversation registries. There is no new model runner. The current resolver provides **preview and policy blocking only**; it never launches Codex Desktop/CLI, Claude Code, ChatGPT, MCP servers, or paid APIs.

## Try a task without spending anything

```sh
python scripts/client_policy_route.py --client chatgpt
python scripts/client_policy_route.py --client codex-desktop --target /path/to/project
python scripts/client_policy_route.py --client codex-cli --operation cli-agent --user-config /private/preferences.json
python scripts/client_policy_route.py --client api --operation paid-api --user-config /private/preferences.json
```

The result is `GUIDANCE_ONLY`, `BLOCKED_BY_POLICY`, or `REVIEW_REQUIRED`. **REVIEW_REQUIRED is not execution approval**; the output always has `execution_authorized=false`, `execution=NOT_EXECUTED`, `model_calls=0`, and `paid_api_calls=0`. A local `preferences.json` can narrow or opt in to client routes for *future separately approved tools*. The example shipped with Toolkit stays zero-spend. No credential input or payment action is supported by this preview.

## Supported contract names

| User route | Contract | What this means |
| --- | --- | --- |
| `codex-desktop` | Codex filesystem skills | Guidance only; does not control Desktop |
| `codex-cli` | Codex filesystem skills | Requires local `allow_cli_agents` for a potential CLI-agent route |
| `claude-code` | Claude Code filesystem skills | Same separate CLI permission; no Claude CLI run |
| `chatgpt`, `chatgpt-plugin` | ChatGPT conversation | Hosted plugin is not project-local skill discovery |
| `claude-web` | Claude.ai conversation | Reference guidance, no managed filesystem layout |
| `mcp` | External protocol | No specific installed server presumed |
| `api` | External API | Paid route requires three affirmative permissions, and separate actual spend caps and consent |

A user-supplied set of `AVAILABLE` session capabilities is labelled `USER_DECLARED_NOT_VERIFIED`, never an independently validated L4/L5/L6 result. Offline registries and the historical evidence ledger remain distinct. A real implementation must verify client-specific login/installation, capabilities, source trust, per-task consent, cancellation, secret protection and enforceable spending controls before any invocation. Do not unlock the `agent_eval_runner.py` execution freeze from this issue.

Run: `python -m unittest tests.test_client_policy_route -v`. Python 3.12+ standard library, Linux/macOS/Windows. Existing Skill Manager installation remains a separately approved action. Do not store private project facts in Toolkit.
