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
Stop-hook scope: Only after actually using Toolkit Model Advisor for this task, and only when a bounded Stop reminder remains wanted, prefix the final answer with the HTML comment <!-- ADT-MODEL-ADVISOR-ACTIVE -->. Do not emit it for external controllers, general risk reports or unverified advisor execution.
Optional, user-enabled proactive Model Advice (ADT #401). For ordinary software
engineering, QA, architecture, UX/UI, DevOps and security requests, without
asking the user to mention Toolkit, call the connected ai-development-toolkit
MCP `toolkit_prepare_task` with optional `proactive_model_advice=true`
from Personal MCP 0.1.13, as directed by the existing ADT-PERSONAL block.
This activates only a bounded read-only risk hint; it does NOT opt in to
extra model calls for the current or any future task.
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
unless live capability is verified unavailable. No request for models,
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

When worth proposing and no applicable user permission exists, show a small
TEXT recommendation within the current Codex chat, in the user's language:
  "A second opinion could help: <one specific reason>.
   1. Continue on current model (SINGLE_MODEL).
   2. Ask an available expert once, with my confirmation
      (RECOMMEND_WITH_CONFIRMATION).
   3. Allow selected experts automatically within a task-specific call cap
      (AUTO_OPT_IN), only after explicit opt-in.
   Extra consultation may use more time and subscription quota.
   Choose 1/2/3."
No separate template prompt, manual Toolkit invocation, or GitHub URL from
the user is needed. This is a CHAT text fallback; do not claim a native
Codex Desktop modal/overlay exists.

Only suggest named models when the active Codex client's CURRENT native
model inventory provides them. Never invent entitlement, model availability,
quota, billing provenance or backend model identity. If native inventory
is UNKNOWN but a new material risk is REVIEW_CANDIDATE, do NOT silently
discard the advisory. Show at most one concise honest suggestion that a
second opinion might help, with risk reason, and explicitly say model
availability is NOT VERIFIED. Offer SINGLE_MODEL (continue now), or
RECOMMEND_WITH_CONFIRMATION (first verify native expert availability,
then request separate consent); AUTO_OPT_IN is DISABLED until a verified
native inventory, host execution capability, zero-extra-cost permission
and scoped consent exist. Do not suggest actual model names or pretend
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

If and only if a permissible delegated execution is approved, use the
existing ADT #357 read-only `toolkit_codex_prepare_delegation`, trusted
host-owned one-shot claim, native spawn/wait and
`toolkit_codex_review_delegation`, without retry or silent fallback.
Respect real cost gates, project AGENTS.md, security/network/visual/release
approval rules, and the user's restrictions. Never use paid APIs or CLI
unless an individual user explicitly permits those routes.

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
