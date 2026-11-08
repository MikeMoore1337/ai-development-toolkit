# Proactive model advice for normal Codex Desktop tasks (#401)

## Explicit high-impact review signals

The existing read-only MCP risk hint recognizes **explicitly critical
security review** and **explicit independent architecture review**
in Russian and English, even without unrelated concurrency or migration
keywords. Ordinary documentation fixes, generic architectural work and
trivial tests remain non-candidates. The hint only asks the host to
evaluate an optional independent review; it never selects a model,
confirms live inventory, grants consent or executes a second model.

## Unknown per-call subscription quota is not an advisory blocker

When the live Codex client has a verified native model candidate but does
not expose per-call quota or price, it should **still recommend the model
and ask the user**. Recommendation is read-only; no billing claim is needed.
If the task primarily needs a different implementation model, recommend
the main Codex **UI model selector** first instead of adding a consultant:
an extra subagent may consume *more* allowance, not less.

### Optional ONE manually confirmed native subscription review

The existing no-extra-paid-spend preflight stays strict by default.
When `zero_incremental_cost_verified=false`, a *single*
`RECOMMEND_WITH_CONFIRMATION` consultation can be prepared only after
the owner confirms **the exact model and this call**, plus all of:

- The native Codex client is signed in using their existing ChatGPT
  subscription, **not** an API-key or paid provider route.
- The owner has checked their current usage/credit page: **zero** purchased
  credits available, **automatic credit top-up disabled**, and included
  subscription allowance still remaining.
- The owner explicitly accepts **unknown usage amount for this one
  consultation**, within existing subscription limits only.

The host passes these as a separate structured `subscription_guard`
to read-only `toolkit_codex_prepare_delegation` and the corresponding
local one-shot `claim`. It must contain the same task ID, inventory
revision, exact requested model, `route=CODEX_CHATGPT_SUBSCRIPTION`,
`owner_confirmed_this_call=true`, `paid_api_route_disabled=true`,
`credit_balance_zero_observed=true`,
`automatic_topup_disabled_observed=true`,
`included_allowance_remaining_observed=true`, and
`unknown_per_call_usage_acknowledged=true`.
These fields represent **user-supplied claims**, not verified account
telemetry. If any fact cannot be established, no subagent is started;
the user can choose the primary model manually in Codex instead.

This manual guard **never** enables `AUTO_OPT_IN`, spending credits,
automatic top-up, multi-call chains, or paid APIs. It does not bypass
live inventory, native tool schema, consent, one-shot lease, task-specific
approval or independent evidence rules. The plan explicitly reports
`OWNER_DECLARED_INCLUDED_USAGE_NOT_ATTESTED` and keeps observed backend
model `UNKNOWN`. Offline tests cannot prove no spending in a live
session. The Codex Desktop E2E gate remains open.



## User-controlled model selection and quota efficiency

**By default, recommend an appropriate model and ask the user.**
A recommendation is never permission to switch models or spawn agents.

- `SINGLE_MODEL`: remain on the current model, with no extra calls.
- `RECOMMEND_WITH_CONFIRMATION`: recommend one verified available model,
  explain task suitability and quota impact, then request an explicit
  confirmation for **each** exact model switch or subagent call.
- `AUTO_OPT_IN`: choose models independently **only after the user
  explicitly selects this mode**, within that task's approved live model
  allowlist, call cap and stop conditions. Do not inherit consent across
  tasks or infer it from installing the Advisor.

No response is not consent. Never silently switch the primary model or
reasoning effort. Where the host cannot change the primary model natively,
recommend a manual model selection in Codex UI instead of claiming one.

For quota efficiency, avoid extra consultation for routine tasks unless
verified evidence supports a benefit. Recommend a more capable model
for complex tasks only when expected reduction in rework and risk
justifies extra calls. Do not invent cost/quality rankings from model
names. If relative quota usage is unverified, report `UNKNOWN` and do
not claim measured savings.



The model advisor is **opt-in once**, not a per-task prompt template. The
existing #356/#357 contracts provide consent and native delegation; this
layer supplies a user-level Codex Desktop instruction entry point to
**proactively propose** an independent review when the task warrants it.

## Enable once (Windows, no Codex CLI)

Use the script from a trusted, checked-out version of the repository
after verifying CI and SHAs. Personal MCP 0.1.13 must already be connected.

```powershell
$source = Join-Path $env:LOCALAPPDATA "ADT-Personal\toolkit-source"
$installer = Join-Path $source "integrations\personal-mcp\adt-personal\Enable-ADT-Model-Advisor.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -WhatIf
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer
```

Restart Codex Desktop completely. The script appends a distinct managed
`ADT-MODEL-ADVISOR` block to `~/.codex/AGENTS.md` with backup,
`-WhatIf`, idempotence, independent removal and no project writes.

Read-only static diagnosis (no Codex CLI or model execution):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -Check
```

`SOURCE_PRESENT_CLIENT_UNVERIFIED` only confirms that the **current** managed
block is in the eligible instruction source. `BLOCK_STALE_UPDATE_REQUIRED`
means an older block is present: rerun the trusted installer **without**
`-Check` (backup and unrelated instructions are preserved), then check again.
`NOT_INSTALLED` means absent, while `MASKED_BY_GLOBAL_OVERRIDE` means a
nonempty `AGENTS.override.md`
takes precedence. Enabling now fails closed on that override; it never
silently rewrites the user's override. Disable remains possible.

The installer honors `CODEX_HOME` when selecting the Codex user directory,
instead of assuming `~/.codex` for every profile. Static checks do not
prove that Codex Desktop loaded the instructions or called Personal MCP.

Disable:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -Disable
```

## Expected behavior

After an ordinary request, Codex uses its connected MCP
`toolkit_prepare_task` without requiring a Toolkit-specific phrase or
model ID in the prompt. Before high-impact changes it should make an
explicit in-session choice: `PROPOSE_REVIEW`, `SINGLE_MODEL_SUFFICIENT`
or `CAPABILITY_UNAVAILABLE`. This is a **client judgment**, not a verified
MCP output or durable record. When `toolkit_route_task` returned an applicable
profile, pass it to `toolkit_prepare_task` to avoid inconsistent rerouting.
It evaluates architecture, security, migrations,
cross-system changes and repeated failures for independent review. It
should avoid interrupting routine fixes. When useful, it displays a short
**chat-text** recommendation with three choices:

1. SINGLE_MODEL — proceed using the current model.
2. RECOMMEND_WITH_CONFIRMATION — recommend only currently available expert
   models and ask approval for each native invocation.
3. AUTO_OPT_IN — **only after task-scoped consent**, bounded selected models,
   call count and stop conditions.

Choice is not delegated execution. No response is no consent. Respect
refusal, revoke, stale inventory, existing project instructions, free-vs-paid
routing, and the host-only one-shot contract. Never claim that a supplied
model name proves actual execution identity.

**This does not add a native Codex Desktop modal.** A chat-text choice is
the supported fallback; global instructions do not expose a native UI
extension surface. Actual client activation remains UNVERIFIED until a
live plain-prompt test confirms the suggestion and its absence on simple
tasks. CLI/API agent execution is never installed or run by this script.

Tests:
```bash
python -m unittest discover -s integrations/personal-mcp/adt-personal/tests -p test_model_advisor_onboarding.py -v
```

## Updating the installed Personal MCP for #401

The dedicated Toolkit source checkout and the persistent MCP launcher are
separate artifacts. An updater refresh alone does **not** replace the launcher.
After verifying a trusted source revision, run PowerShell:

```powershell
$source = "$env:LOCALAPPDATA\ADT-Personal\toolkit-source"
$installMcp = Join-Path $source "integrations\personal-mcp\adt-personal\Install-ADT-Personal.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installMcp -McpOnly -WhatIf
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installMcp -McpOnly
```

`-McpOnly` updates the pre-existing local stdio modules without Codex CLI,
re-registering the client, or overwriting global instructions. Refresh the
previously opted-in Advisor managed block using its own installer with a
WhatIf/backup, run `-Check`, and restart Codex Desktop. Confirm MCP version
via `toolkit_info` in a fresh chat.

An explicitly opted-in client passes `proactive_model_advice=true` to the
existing `toolkit_prepare_task` tool. Its additional `model_advisor` field
contains only a conservative local task-risk hint, never host model inventory,
model approval, native execution, or evidence of actual client UI rendering.
The Codex host must assess verified capabilities and decide whether to show a
chat choice. This source change cannot guarantee a Codex Desktop proposal.
Other Toolkit users remain opt-out by default.

### Reassess after material newly discovered risk (MCP 0.1.13)

An ordinary PR/CI request may contain no initial security or concurrency
keywords. When actual inspected source/diff reveals a materially new risk, the
opted-in Codex host can call the read-only `toolkit_model_review_checkpoint`
once for that risk boundary, supplying `task`, at most 8 concise
`observed_findings`, `stage=NEW_RISK` and `proactive_model_advice=true`.
`PRE_CHANGE` and `PRE_PR` may also be used when a *new* major risk is
discovered. This is not periodic polling, an instruction to repeat prompts,
proof that findings are valid or authority to launch another model.
`new_risk_boundary` is only a bounded lexical difference; caller findings
are not echoed or persisted.

Unknown native client model inventory must not silently suppress a meaningful
security-risk advisory. Codex may make an honest, brief recommendation
without naming any unverified models: continue with the current model, or
verify native availability and request separate consent before any review.
AUTO_OPT_IN stays unavailable until native client/cost/consent gates can be
verified for the current task. Unknown inventory never authorizes an extra
call or blocks routine task progress. Source tests cannot prove client behavior.

## Experimental Codex Desktop Stop hook

Native #401 acceptance found the client may omit the new-risk MCP checkpoint after confirming real defects. An independent, **separately trusted and manually enabled** [Stop hook](MODEL_ADVISOR_STOP_HOOK.md) can ask the current model to show an optional review advisory at turn end **only if a separately trusted host provides task-scoped ownership** (`adt_workflow_scope=TOOLKIT_MODEL_ADVISOR`). Stock Codex Stop events cannot provide that field, so the hook is intentionally inert there, preserving external-native workflows. Assistant-written markers cannot activate it. It is never installed by the Advisor setup, does not execute another model, and requires native acceptance after host support becomes available.

## Approved native delegation for V1/V2

An advisor choice does not execute a model. Native consultation requires
explicit task-scoped consent, live approved model inventory, an actually
exposed spawn tool with model override, included-cost authorization, and
a trusted local Python interpreter. The primary model remains the writer.

1. Verify exposed tools in **this Codex session**. V1 uses
   `multi_agent_v1__spawn_agent` and `multi_agent_v1__wait_agent`.
   V2 uses `spawn_agent` with `task_name`, `model` and
   `fork_turns="none"`, plus `list_agents` with `agent_status`.
   V2 `wait_agent` only reports mailbox notifications, **not** completed
   content; never treat it as a completed consultant result.
2. Select the model only from the live allowlist. For
   `RECOMMEND_WITH_CONFIRMATION` request this call's confirmation.
   `AUTO_OPT_IN` may select among the task's explicitly approved
   models within its call cap; it does not grant permanent permission.
3. Ask read-only `toolkit_codex_prepare_delegation` for a preflight.
   Set `native_runtime="V2"` only when the current host exposes V2
   model overrides; also supply `client_snapshot.native_runtime="V2"`
   and `native_model_override="VERIFIED"`. These are **host declarations**,
   not independent authentication. V1 remains the default.
4. Use the verified local Toolkit script
   `scripts/codex_host_one_shot.py init --root <private-absolute-path>`
   once if needed. On Windows, independently validate effective private
   filesystem ACLs. Then pipe bounded JSON containing the same
   plan/request/consent/state/snapshot/context and confirmation directly
   to `codex_host_one_shot.py claim --root ...` via stdin. Never log
   the raw context. Require `HOST_ONE_SHOT_RESERVED` before native spawn.
5. Spawn once using the plan's **exact** native arguments. V1 validates
   the matching UUID via one wait. V2 validates an explicit completed
   target task from `list_agents`. Review via
   `toolkit_codex_review_delegation` and persist one redacted outcome
   with `codex_host_one_shot.py record`. No second spawn or auto-retry.

No backend model identity or cost is independently attested by the ledger.
Without a live native tool, true consent, cost authorization, private
ledger, or valid one-shot reservation, continue with the primary model
and report the blocker once. The solution uses no Codex CLI, paid API,
project writes or custom native Codex UI. Source tests are not evidence
of a live Codex Desktop run.
