# Model Switching Adapters (Issue #357)

[Русский](ru/MODEL_SWITCHING_ADAPTERS.md) | [Portable advisor](ADAPTIVE_EXECUTION_ADVISOR.md)

The implementation in `scripts/model_switching_adapters.py` is a **host callback adapter**, not a new model provider, shell launcher, Codex CLI wrapper, online service or API integration. It is deliberately client-neutral. A client may supply actual capabilities and executable host callbacks, but unsupported clients remain single-model.

## Host integration contract

Supply the same exact `request` and explicit `consent` accepted by `adaptive_execution_advisor.authorize`, a user-approved target model, and a per-task state (`task_id`, `inventory_revision`, `calls_used`, `revoked`). The host itself is responsible for protecting that state against tampering and checking real account/model entitlements.

- `snapshot()`: returns current model inventory, revision, switching/delegation capabilities and verified zero-incremental-cost assertion. This is **checked again immediately before dispatch** against the original request.
- `invoke(model_id, context, method)`: uses the host's *existing authorized* model or subagent mechanism. `method` is `delegate` if verified, otherwise `switch` if supported. This callback is the only place an actual model could run.
- `restore(primary_model)`: required for a switching (non-delegation) host. Returning `True` is a host claim, not independently inspected model telemetry. A failed return emits `PRIMARY_RESTORE_NOT_VERIFIED`.
- Each call must be individually user-confirmed for `RECOMMEND_WITH_CONFIRMATION`. Automatic mode requires per-task opt-in, verified capability and zero incremental cost, an explicit model allowlist and `max_extra_calls` between 1 and 10.
- `context` is a minimal user-approved handoff, never logged by the adapter. In case of an exception the adapter reports `HOST_CALL_FAILED`, consumes the one attempt and **never automatically retries**.
- Execution provenance distinguishes requested and observed model. `EXECUTED_VERIFIED_BY_HOST` means only that the host callback supplied a matching verified receipt, **not independent third-party verification**.

## Client compatibility

| Host/client | Portable advisor | Model invocation by this repository | Runtime status |
| --- | --- | --- | --- |
| Codex | Yes | Host callback only; must be wired to an actually supported client API | NOT_TESTED |
| Claude Code | Yes | Host callback only; must verify actual local model/subagent support | NOT_TESTED |
| ChatGPT/Claude web | Text recommendation | No generic programmatic host switch exposed to Toolkit | UNSUPPORTED unless host adds a documented hook |
| DeepSeek/Qwen/other | Text recommendation | No assumed API/subscription access | UNKNOWN until client evidence |

Never infer a model catalog from published model names, paid provider APIs or screenshots. If an actual client's model inventory cannot be retrieved, report UNKNOWN and continue with the current model. Manual user input is not independently VERIFIED. Unknown quota remains UNKNOWN, not an estimated percentage.

## Verification

Run `python -m unittest tests.test_model_switching_adapters -v`. Tests use injected synthetic callbacks only. No real model use, paid APIs, secrets, client configuration changes or project writes occur.

**Acceptance boundary:** The core handoff/consent contract is implementable and testable offline. Real Codex/Claude Code installation, runtime model selection, quota measurements, telemetry, and client-specific UI are **NOT_VERIFIED** here. Do not close #357 as live complete until explicit allowed real-client trials produce exact versions, observed model receipts, fallback/restore proof and non-regression checks.


## Codex Desktop pilot (2026-10-25) and opt-in native bridge

A user explicitly approved **one** `multi_agent_v1__spawn_agent` with
`model=gpt-6.1-sol` on Windows. Codex returned agent
`01a1736e-e9f8-7132-82a7-23fc02ae6223` and a PostgreSQL answer.
This demonstrates **host-native delegated task completion**, **not backend
model identity**: no runtime `observed_model` attestation was returned.
The main UI model remained GPT-5.6 Luna Max. Plus usage moved from 27% to
30% (5-hour), 4% to 5% (weekly), with zero extra credits; not a billing receipt.

`scripts/codex_native_bridge.py` wires the existing `dispatch()` policy to
**trusted host-injected** `spawn_agent` and `wait_agent` callbacks. The host
must adapt its session-scoped tools to the normalized signatures:

- `spawn_agent(model=approved_model, message=minimal_context, fork_context=False)`
  returns `{"agent_id": "<canonical UUID>"}`
- `wait_agent(agent_id=id)` returns
  `{"agent_id": "<same UUID>", "status": "completed", "result": "<nonempty text>"}`

A completed native result yields `HOST_EXECUTED_MODEL_UNVERIFIED`,
`observed_model=UNKNOWN`, and a host-reported agent ID. Failure never retries.
There is no primary-model switch or restore for this delegate-only bridge.
Run `python -m unittest tests.test_codex_native_bridge -v` for offline mocks.

**Integration boundary:** A Toolkit MCP stdio process cannot directly invoke
Codex Desktop's session tools. This code does not register such tools or use
Codex CLI, an API key, provider network traffic, or paid services. A trusted
host must bind *real* callbacks for an end-to-end runtime check; that check is
still outstanding. With `zero_incremental_cost_verified=False`, policy
continues to deny automatic dispatch. An approved manual host trial does not
satisfy that zero-cost gate.
