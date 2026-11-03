# Enables one-time proactive model-advice guidance in Codex Desktop.
# Never invokes Codex CLI, model APIs, native agents, or Toolkit MCP.
# The user must opt in explicitly; merely installing Personal MCP leaves it off.
[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [switch]$Disable,
    [switch]$Check,
    [string]$InstructionsPath = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($Disable -and $Check) {
    throw '-Check and -Disable are mutually exclusive.'
}
# Codex reads global instructions from CODEX_HOME, when set, rather than ~/.codex.
$codexHome = if (-not [string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
    [IO.Path]::GetFullPath($env:CODEX_HOME)
} else {
    Join-Path $HOME '.codex'
}
$defaultPath = Join-Path $codexHome 'AGENTS.md'
$path = if ($InstructionsPath) { [IO.Path]::GetFullPath($InstructionsPath) } else { $defaultPath }
$path = [IO.Path]::GetFullPath($path)
$dir = Split-Path -Parent $path
$overridePath = Join-Path $dir 'AGENTS.override.md'

# A linked user instruction file (or parent) could modify unrelated content.
foreach ($candidate in @($path, $dir, $overridePath)) {
    if (Test-Path -LiteralPath $candidate) {
        $item = Get-Item -LiteralPath $candidate -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Linked instruction path refused: $candidate"
        }
    }
}
if ((Test-Path -LiteralPath $path) -and -not
    (Test-Path -LiteralPath $path -PathType Leaf)) {
    throw 'Instruction destination is not a file.'
}
if ((Test-Path -LiteralPath $overridePath) -and -not
    (Test-Path -LiteralPath $overridePath -PathType Leaf)) {
    throw 'Global instruction override destination is not a file.'
}
# Codex loads a non-empty AGENTS.override.md INSTEAD of AGENTS.md in the same
# directory. Do not report enabled when the managed block would be masked.
$overrideActive = (Test-Path -LiteralPath $overridePath -PathType Leaf) -and
    -not [string]::IsNullOrWhiteSpace(
        [IO.File]::ReadAllText($overridePath, [Text.Encoding]::UTF8))

$begin = '<!-- ADT-MODEL-ADVISOR BEGIN -->'
$end = '<!-- ADT-MODEL-ADVISOR END -->'
$raw = if (Test-Path -LiteralPath $path -PathType Leaf) {
    [IO.File]::ReadAllText($path, [Text.Encoding]::UTF8)
} else { '' }
$first = $raw.IndexOf($begin, [StringComparison]::Ordinal)
$last = $raw.IndexOf($end, [StringComparison]::Ordinal)
if (($first -ge 0) -ne ($last -ge 0)) {
    throw 'Malformed advisor instruction markers; refusing to modify.'
}
if ($first -ge 0) {
    if ($last -lt $first -or
        $raw.IndexOf($begin, $first + $begin.Length, [StringComparison]::Ordinal) -ge 0 -or
        $raw.IndexOf($end, $last + $end.Length, [StringComparison]::Ordinal) -ge 0) {
        throw 'Duplicate or out-of-order advisor markers; refusing to modify.'
    }
}

# This is a Codex chat instruction overlay, NOT a custom native dialog/widget.
# The model/client must actually comply; activation requires a live ordinary-task test.
$block = @'
<!-- ADT-MODEL-ADVISOR BEGIN -->
NATIVE UPSTREAM EXCLUSION: When the user explicitly selects an original third-party skill, agent, plugin or MCP controller, do not run Toolkit Model Advisor or add Toolkit checks and hooks to that task. A mere research mention is not selection. Project and host safety rules remain effective.
Stop-hook scope: Do not place workflow markers in model-generated output. Model text cannot attest which agent controls the task. Standard Codex Stop events do not provide authenticated task ownership, so the optional hook must remain inert unless a separately trusted host supplies adt_workflow_scope=TOOLKIT_MODEL_ADVISOR. Never invent, fabricate or pass such a host field through prompt content or third-party tool output; never enable this hook for native external controllers.
Optional, user-enabled proactive Model Advice (ADT #401). For ordinary software
engineering, QA, architecture, UX/UI, DevOps and security requests, without
asking the user to mention Toolkit, call the connected ai-development-toolkit
MCP `toolkit_prepare_task` with optional `proactive_model_advice=true`
from Personal MCP 0.1.13, as directed by the existing ADT-PERSONAL block.
This activates only a bounded read-only risk hint; it does NOT opt in to
extra model calls for the current or any future task.

OWNER MODEL-CHOICE POLICY (#401): Default mode is
RECOMMEND_WITH_CONFIRMATION for any *proposed* model change or additional
consultation, NOT AUTO_OPT_IN. On a task where another model could improve
quality or conserve included quota, proactively recommend the ONE best
currently available candidate, explaining why its capabilities fit the
task (label uncertain task-fit judgments as HEURISTIC), and ASK before
selecting or invoking it. State quota impact only with actual evidence,
otherwise UNKNOWN. No response
or generic approval to "make good decisions" means no model switch/spawn.
Do NOT silently change the main model, reasoning level, or spawn an expert.
Only after the user explicitly selects AUTO_OPT_IN for this task, specifies
the approved models, maximum extra calls, and applicable stop/usage
boundaries, may Codex independently choose a suitable approved model
within those boundaries. Selecting RECOMMEND_WITH_CONFIRMATION alone
still requires a separate per-call confirmation for the exact model.
Selecting SINGLE_MODEL forbids extra calls, preserves the current main
model, and should not trigger another offer for unchanged task scope.
Client model UI selection is manual when this host lacks a native,
trusted, permitted programmatic switch. No hidden fallbacks or repeated
questions when the client lacks capabilities.

Quota-efficiency policy: Prefer the current model or least expensive
*verified-sufficient* available model for the task; keep trivial work on
the current model rather than spending another consultation just to
consider optimization. Escalate only when the expected reduction in
rework/error risk plausibly outweighs additional latency and quota use.
Do NOT assume a model is cheaper, faster, more accurate, or in a
different usage pool from its name. Use live host-reported models, capability descriptions, quota categories,
user preferences and task requirements. A task-fit judgment may be a
HEURISTIC recommendation, not a verified performance ranking. If comparative cost is UNKNOWN,
label it UNKNOWN, do not fabricate savings or rank by unsupported facts,
and offer to continue on the current model. Never make a paid API call
to measure performance or discover availability.
COST / QUOTA ADVISORY BOUNDARY (#401): Failure to obtain an exact per-call
quota or cost receipt must NEVER suppress a useful MODEL RECOMMENDATION or
the user-choice question. A verified live model inventory and genuine task
fit may justify suggesting one model even while subscription quota usage
is UNKNOWN. UNKNOWN is NOT proof of free execution, but also NOT proof
that every consultation costs extra money. Distinguish:
- ADVICE: read-only, no billing attestation or extra-model call required.
- PRIMARY-MODEL CHANGE: usually user selects model in Codex UI; suggesting
  such a switch adds NO subagent call and may be more quota-efficient.
- SUBAGENT CALL: requires exact per-call consent (unless separately
  bounded AUTO_OPT_IN), trustworthy native tools, one-shot lease, and
  applicable included-usage billing guard. Do not replace this with a
  general statement that cost cannot be verified.
If billing or quota cannot be measured by the host, offer the user a
CHOICE and state the missing evidence. Do not invent remaining percentage,
per-call price, or zero-cost guarantee. Do not poll for a billing tool
which Codex Desktop does not expose. Continue implementing with the current
model when the user declines or does not answer.

Use its task profiles and source guidance plus the actual task to assess,
once per task and at genuine new risk boundaries, whether independent model
review may materially improve correctness. If toolkit_route_task has already
returned a compatible primary profile, pass it as the optional `profile` to
toolkit_prepare_task so the second routing does not silently change priorities.
The actual user task and discovered risks, NOT the chosen skill profile alone,
govern the review decision. This assessment is ADVISORY, not proof of
semantic/model inference. Do not call external models for assessment.

Immediately after toolkit_prepare_task returns and BEFORE substantive edits,
inspect its `model_advisor` metadata when present. The MCP may return a
`REVIEW_CANDIDATE` based only on bounded task-risk terms, not a model's
independent reasoning or host capabilities. Use the actual task and
`model_advisor.reason_code` to make a bounded advisor decision:
PROPOSE_REVIEW if independent review could materially help;
SINGLE_MODEL_SUFFICIENT if not; or CAPABILITY_UNAVAILABLE when the
host cannot verify live model availability/delegation/cost.
On `REVIEW_CANDIDATE` for a real security/concurrency/integrity risk,
surface a concise opt-in chat choice BEFORE implementing high-risk edits
unless live model delegation and manual UI selection are both confirmed
unavailable. Unknown per-call quota telemetry is NOT a reason to suppress
the choice; it can block execution until owner confirmation. No request for models,
consent or execution is implied by the MCP hint itself.
If `model_advisor` is absent from the tool response, treat this as a
stale Personal MCP adapter: do not claim the new advisory gate ran, and
continue safely on the primary model. Do NOT invent a host model list.
On the discovery of MATERIAL NEW RISK from actual source/diff inspection
(e.g. OS-lock, git hook bypass, Windows junction, rollback journal),
reassess once at that risk boundary via read-only MCP
`toolkit_model_review_checkpoint` with the original plain-language task,
a short list of concrete findings, stage=NEW_RISK, and
proactive_model_advice=true. This is optional guidance for opted-in users,
not a permission to delegate. Call it at most once per material new
risk boundary and avoid duplicate prompts. If the risk was already assessed
or the user rejected review, only reconsider after a materially NEW scope.
Use PRE_CHANGE or PRE_PR only where a newly observed critical risk
justifies reconsideration. Never poll or call this checkpoint in a loop.
This checkpoint reads only supplied task/finding text, does not inspect
files independently, attest a model inventory, or execute a model.
For security-sensitive changes involving concurrency, Git trust boundaries,
state recovery or major migration risk, independently consider a pre-change
review rather than waiting for the final summary. Do not quietly skip the
decision merely because skill routing succeeded or the profile is qa-core.
This is an in-session decision, NOT a guarantee of improved model quality.
Avoid creating files, logs or external telemetry just to record this decision.

For simple, routine or self-contained changes, do the work silently using
the current primary model. Do NOT present the advisor choice on every turn.
When choosing SINGLE_MODEL_SUFFICIENT, do not interrupt the user or publish
an artificial advisory audit log.
Consider proactively proposing an expert for architectural trade-offs, unclear
data migrations or concurrency, high-impact security, repeated debugging
failures, complex cross-system changes, or independent verification of an
important result. Briefly explain the concrete reason, expected benefit,
possible latency, extra context transfer and possible included-usage impact.
Quality improvement is not guaranteed.

When a different model or independent consultation is materially worth
proposing and no applicable user permission exists, show a short TEXT
recommendation within the current Codex chat, in the user's language:
  "Recommended: <ONE verified available model, or UNKNOWN>.
   Task fit: <one concrete reason grounded in observed capabilities>.
   Quota impact: <observed comparative impact, or UNKNOWN>.
   1. Keep current model and do not delegate (SINGLE_MODEL).
   2. Recommend suitable model, then ask me to approve the exact
      model and each consultation/switch (RECOMMEND_WITH_CONFIRMATION).
   3. Choose automatically only among models and call/usage caps that
      I explicitly approve for THIS task (AUTO_OPT_IN).
   Potential extra time/quota and quality uncertainty: <short explanation>.
   Which mode do you choose?"
For unknown native inventory, do NOT name or rank a model. For a main
model switch, explain whether the user must change it in Codex UI.
Never call the user's selection of mode 2 permission to use a model:
wait for separate, specific authorization. Do not select mode 3 on
the user's behalf.
No separate template prompt, manual Toolkit invocation, or GitHub URL from
the user is needed. This is a CHAT text fallback; do not claim a native
Codex Desktop modal/overlay exists.

Only suggest named models when the active Codex client's CURRENT native
model inventory provides them. Never invent entitlement, model availability,
quota, billing provenance or backend model identity. A known model catalog
with UNKNOWN per-call quota cost still permits recommending a suitable
model and asking first. If native inventory
is UNKNOWN but a new material risk is REVIEW_CANDIDATE, do NOT silently
discard the advisory. Show at most one concise honest suggestion that a
second opinion might help, with risk reason, and explicitly say model
availability is NOT VERIFIED. Offer SINGLE_MODEL (continue now), or
RECOMMEND_WITH_CONFIRMATION (first verify native expert availability,
then request separate consent); AUTO_OPT_IN is DISABLED until a verified
native inventory, host execution capability, zero-extra-cost permission
and scoped consent exist. When AUTO is disabled for unavailable billing
evidence, RECOMMEND_WITH_CONFIRMATION remains a valid ADVICE mode; do
not conflate a blocked extra call with a blocked recommendation. Do not suggest actual model names or pretend
there is a usable choice before host verification. Never block safe task
progress solely due to missing inventory, or run unknown models.
If the host explicitly confirms delegation is UNAVAILABLE, only note
that independent review cannot currently run; stay on the primary model.
Do not loop or ask the user repeatedly about unavailable capabilities.

No reply means NO permission. Honor a user's refusal for the current task;
do not ask again unless its material scope changes. An explicit approval
must be tied to the current task and bounded by selected model(s), call cap,
client account/session policy and optional revocation. Do not interpret a
general preference as unlimited approval. A chosen AUTO_OPT_IN mode requires
a separate, explicit scoped agreement, NOT an automatic persistent default.
Never call subagents simply because this instruction block was installed.

When the user has selected RECOMMEND_WITH_CONFIRMATION for a task and
approved one exact consultation, select only that live, approved model.
For AUTO_OPT_IN, after one explicit task-scoped consent listing allowlisted
models and call cap, choose the most relevant currently available model
yourself without asking again within the approved scope. If several are
equivalent, prefer lower included-quota impact. The main model remains
the only writer. Do not claim that model ranking is measured or known when
the current host does not provide evidence. A recommendation is not a
completed consultation.

For an approved extra consultation, do not stop after recommending a model
merely because the MCP does not run native tools. The trusted Codex Desktop
HOST (not MCP) may perform the following sequence using its own native
tools and local Python interpreter, but never Codex CLI:
1. Check the tools exposed in THIS session. V1 requires
   multi_agent_v1__spawn_agent plus multi_agent_v1__wait_agent. V2 requires
   spawn_agent with task_name, model, fork_turns and list_agents with
   agent_status; model override must actually be offered in the tool schema.
   No matching tools or insufficient model override -> SINGLE_MODEL fallback.
2. Verify the current native model inventory, native ChatGPT-account route,
   task-scoped consent, chosen model and inventory revision; UNKNOWN is not
   VERIFIED. Do NOT require the client to expose an exact per-call quota
   meter before ASKING which model the user prefers. For execution:
   a) If real zero-incremental-cost evidence exists, use the original
      zero_incremental_cost_verified=true contract, honestly sourced.
   b) Otherwise, ONLY for one RECOMMEND_WITH_CONFIRMATION consultation,
      after explicit owner confirmation of THIS model and call, request
      confirmation of all current facts: ChatGPT subscription login,
      no paid API route, credit balance observed ZERO, automatic credit
      top-up observed OFF, included allowance observed REMAINING, and
      consent to unmetered (UNKNOWN) per-call quota consumption.
      Set zero_incremental_cost_verified=false (do not forge true).
      Pass subscription_guard with exact task_id, inventory_revision,
      requested_model, route=CODEX_CHATGPT_SUBSCRIPTION, and booleans
      owner_confirmed_this_call=true, paid_api_route_disabled=true,
      credit_balance_zero_observed=true,
      automatic_topup_disabled_observed=true,
      included_allowance_remaining_observed=true,
      unknown_per_call_usage_acknowledged=true.
      These are OWNER DECLARATIONS, NOT independent billing proof.
      Never invent/assume them or reuse old confirmations.
      If any are unknown, skip native spawn and recommend manual Codex UI
      model selection instead. Never use a paid API, credit balance, or
      automatic top-up to complete this optional review.
   c) AUTO_OPT_IN without verified zero-incremental-cost evidence remains
      BLOCKED. A manual included-allowance attestation never enables AUTO.
   For V2 set client_snapshot.native_runtime=V2 and
   client_snapshot.native_model_override=VERIFIED ONLY after checking the
   actual exposed native tool schema. Never trust a model's assertion alone.
3. Request read-only toolkit_codex_prepare_delegation with the approved
   task/request/consent/state/snapshot/minimal context and native_runtime
   V1 or V2; include exact subscription_guard only for user-approved
   manual included-allowance mode. A preflight plan/fingerprint is NOT
   a reservation.
4. Use the trusted local Toolkit source's
   scripts/codex_host_one_shot.py via local Python (NOT Codex CLI).
   Call init --root on a host-approved private, absolute user ledger path,
   preferably inside CODEX_HOME or ~/.codex, only after consent. On Windows,
   the host must verify its filesystem ACL separately. Send claim --root required
   bounded JSON exclusively by stdin (including subscription_guard when
   applicable); do not persist user prompts, print
   raw context in logs, or substitute an untrusted script. The claim must
   return HOST_ONE_SHOT_RESERVED for this exact plan before native spawn.
   This is a trusted host-owned one-shot claim, without retry or bypass.
   If script, private ledger, execution permission or the lease is missing,
   refuse to spawn; explain the specific preflight blocker once.
5. Invoke the ONE approved native spawn with exact arguments from the
   preflight plan. For V1 perform one matching wait_agent and review its
   final status. For V2, wait for mailbox only if actually blocked, then
   use list_agents to get the target task's completed agent_status; V2
   wait_agent alone does NOT contain a final result. Never use fork_context
   in V2; use fork_turns=none with the selected model override.
6. Call toolkit_codex_review_delegation, then record outcome once with
   the ledger script using only the bounded native responses; redact
   substantive output from durable receipts. Reconcile actual usage as
   host-reported, never fabricate backend model verification. No retry,
   alternative model, unapproved additional spawn or silent primary switch.

Respect real cost gates, project AGENTS.md, security/network/visual/release
approval rules, and the user's restrictions. Never use paid APIs or Codex
CLI to work around missing native capabilities. If any gate cannot be
verified, continue the primary-model task without a repeated prompt.

Uninstalling this opt-in block restores ordinary Toolkit skill routing.
<!-- ADT-MODEL-ADVISOR END -->
'@
$nl = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
$block = $block.Replace("`r`n", "`n").Replace("`n", $nl)
# Static source attestation, not proof that the Desktop client ingested it.
# An old managed block must not be reported as a current installation.
if ($Check) {
    if ($overrideActive) {
        Write-Host 'Model advisor check: MASKED_BY_GLOBAL_OVERRIDE'
    } elseif ($first -lt 0) {
        Write-Host 'Model advisor check: NOT_INSTALLED'
    } else {
        $installedBlock = $raw.Substring($first, $last + $end.Length - $first)
        if ([string]::Equals($installedBlock, $block, [StringComparison]::Ordinal)) {
            Write-Host 'Model advisor check: SOURCE_PRESENT_CLIENT_UNVERIFIED'
        } else {
            Write-Host 'Model advisor check: BLOCK_STALE_UPDATE_REQUIRED'
        }
    }
    return
}
if (-not $Disable -and $overrideActive) {
    throw 'AGENTS.override.md takes precedence over AGENTS.md. No changes; resolve the override before enabling.'
}
if ($Disable) {
    if ($first -lt 0) {
        Write-Host 'Model advisor already disabled; no changes.'
        return
    }
    $updated = $raw.Substring(0, $first) + $raw.Substring($last + $end.Length)
} elseif ($first -ge 0) {
    $updated = $raw.Substring(0, $first) + $block + $raw.Substring($last + $end.Length)
} else {
    $prefix = if ($raw.Length -eq 0) { '' } elseif ($raw.EndsWith($nl)) { $nl } else { $nl + $nl }
    $updated = $raw + $prefix + $block + $nl
}
if ([string]::Equals($raw, $updated, [StringComparison]::Ordinal)) {
    Write-Host 'Model advisor instructions already up to date; no changes.'
    return
}
$verb = if ($Disable) { 'Disable proactive model advisor' } else { 'Enable proactive model advisor' }
if (-not $PSCmdlet.ShouldProcess($path, $verb)) { return }
if (-not (Test-Path -LiteralPath $dir -PathType Container)) {
    [void](New-Item -ItemType Directory -Force -Path $dir)
}
if (Test-Path -LiteralPath $path -PathType Leaf) {
    $backup = $path + '.adt-model-advisor-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fffffff')
    Copy-Item -LiteralPath $path -Destination $backup -ErrorAction Stop
    Write-Host "Backup: $backup"
}
[IO.File]::WriteAllText($path, $updated, [Text.UTF8Encoding]::new($false))
Write-Host "Model advisor: $(if ($Disable) { 'DISABLED' } else { 'ENABLED' })"
Write-Host 'Restart Codex Desktop and test a normal task without mentioning Toolkit.'
