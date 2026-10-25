# Adaptive Execution Advisor (Issue #356)

[Русский](ru/ADAPTIVE_EXECUTION_ADVISOR.md)

This is an **opt-in, offline-only policy helper**, not a model-switching engine. It builds on the existing toolkit task/skill router and orchestration decision policy, without introducing another agent runtime.

## User journey

1. Receive a task and classify it with existing Toolkit skills/profile routing. A host may additionally supply nonexclusive signals: `routine`, `architecture`, `security`, `design`, `ambiguous`, `repeated_failure`.
2. Ask the host for its **actual model inventory** and switching/delegation capabilities. If discovery is not supported, report UNKNOWN; never infer available models from provider names. An explicitly typed model list must not be marked VERIFIED unless the host confirms availability.
3. Present the three modes **with their benefits and risks**, and ask the user to choose **for this task**. No response means *no extra model calls*.
4. `SINGLE_MODEL` stays on the current model. `RECOMMEND_WITH_CONFIRMATION` suggests alternatives but **requires a separate confirmation before each use**. `AUTO_OPT_IN` permits only user-approved models within a strict per-task `max_extra_calls` cap. The default is never automatic.
5. If any authorization or capability is stale, revoked, inconsistent or unverified, keep the current model. The host must independently enforce consent again **at execution time**.

## Benefits and risks

| Mode | Benefit | Risk |
| --- | --- | --- |
| SINGLE_MODEL | Predictable limits and fewer context transfers | Complex cases may need more iterations |
| RECOMMEND_WITH_CONFIRMATION | Choose an appropriate, available model before each consultation | More interaction and additional token/time usage; quality is not guaranteed |
| AUTO_OPT_IN | Fewer manual steps for approved handoffs | Extra quota usage, latency and context transmission; quality is not guaranteed |

## API

`python scripts/adaptive_execution_advisor.py request.json [--consent consent.json]` returns read-only JSON. An input contains the exact fields:

```json
{
  "task_id": "demo-001",
  "locale": "en",
  "current_model": "client-model-A",
  "available_models": ["client-model-A", "client-model-B"],
  "inventory_status": "VERIFIED",
  "inventory_revision": "client-discovery-revision-1",
  "switching": "UNKNOWN",
  "delegation": "VERIFIED",
  "zero_incremental_cost_verified": true,
  "signals": ["architecture"]
}
```

Without consent the response has `user_selection_required=true`, `selected_mode=null`, `execution=NOT_RUN`, all three explained choices and blockers. This result is **not user approval**.

Example separate explicit user choice (not inferred from a prompt):

```json
{
  "task_id": "demo-001",
  "inventory_revision": "client-discovery-revision-1",
  "mode": "AUTO_OPT_IN",
  "approved_models": ["client-model-B"],
  "max_extra_calls": 2
}
```

This example does **not** activate any agent. `authorize` only checks policy and returns `execution=NOT_RUN`. Its output is not a reusable credential or durable permission. A host adapter must verify the live client and task consent separately at call time. User cancellation or changed limits invalidates consent.

Never interpret `zero_incremental_cost_verified=true` as automatically trustworthy: it is a caller declaration. Adapters must substantiate it before real calls. No paid API, remote server, secret, project mutation or telemetry is required by the policy.

## Testing and limitations

Run `python -m unittest tests.test_adaptive_execution_advisor` or the existing test discovery. The tests cover one-model clients, unknown inventories, unverified automatic execution, stale and cross-task consent, bounds, invalid schemas and both locales. These are **offline** tests, not live Codex/Claude/DeepSeek model activation, quota measurement or proof of improved outcomes.

Client-specific invocation, real model inventory, quota information, cancellation and runtime evidence belong to **Issue #357**. Until its implementation is verified, use this advisor for explanations and policy decisions only.
