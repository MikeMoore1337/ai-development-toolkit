# Proactive model advice for normal Codex Desktop tasks (#401)

The model advisor is **opt-in once**, not a per-task prompt template. The
existing #356/#357 contracts provide consent and native delegation; this
layer supplies a user-level Codex Desktop instruction entry point to
**proactively propose** an independent review when the task warrants it.

## Enable once (Windows, no Codex CLI)

Use the script from a trusted, checked-out version of the repository
after verifying CI and SHAs. Personal MCP 0.1.11 must already be connected.

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

`SOURCE_PRESENT_CLIENT_UNVERIFIED` only confirms the managed block is in
the eligible instruction source. `NOT_INSTALLED` means absent, while
`MASKED_BY_GLOBAL_OVERRIDE` means a nonempty `AGENTS.override.md`
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
model ID in the prompt. It evaluates architecture, security, migrations,
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
