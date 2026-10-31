# Optional Model Advisor Stop hook (separately trusted, experimental)

## Scope

A real Codex Desktop session loaded Personal MCP 0.1.13 and opted-in advice
but omitted the new-risk checkpoint after independently discovering release
blockers. An MCP server cannot force a host to invoke another tool after the
host reads code. The **Codex lifecycle Stop hook** provides a distinct,
host-driven reminder path. This source artifact is disabled by default.

**Native-First / task-scoped activation (#494):** the hook returns `{}` unless a trusted host integration supplies `adt_workflow_scope=TOOLKIT_MODEL_ADVISOR` in the Stop event and `adt_external_tool_active` is not `true`. These fields are **not standard Codex Stop-event fields**: normal Codex Desktop events cannot activate this hook. It never infers ownership from a model-generated message. Do not inject or fake a scope marker into an unrelated workflow. Source-only tests of synthetic scoped events do not prove host support, actual invocation or effectiveness.
Hook docs: https://developers.openai.com/de-DE/docs/hooks.

The portable, stdlib-only script
`integrations/personal-mcp/adt-personal/hooks/model_advisor_stop_hook.py`
reads a bounded Stop-event JSON from stdin and tests the **last assistant
message** for a conservative combination of confirmed high-risk defects.
If triggered, it returns one bounded `decision=block` continuation reason
to ask the *same primary model* to offer optional independent review.
It neither inspects files nor verifies the truth of a finding. It cannot
attest that Codex Desktop will honor or display the suggestion.

## Safety and opt-in

No default installation, client configuration edit, file writes, external
network access, model API, Codex/Claude CLI, transcript reads, persistent
telemetry or delegated model call. Original assistant content is never
reflected in the hook output. Input is limited to 64 KiB, and malformed
events fail open as `{}`.

A Stop continuation uses the **same** model and may consume more included
subscription quota. `stop_hook_active` prevents recurrence within that
Stop continuation; separate threads may still trigger a recommendation.
Lexical false positives/negatives remain possible. Never assume trusted
hook installation, available model inventory or user permission.

## Manual installation example (Windows)

**Known Windows Desktop blocker:** [openai/codex #47283](https://github.com/openai/codex/issues/47283)
reports that the app may list a hook as enabled without successfully
trusting or running it; its trust confirmation worked only in interactive
Codex terminal. In environments where Codex CLI is prohibited, **do not
enable this hook or bypass trust** until native Desktop review/trust is
independently verified as fixed. Green source CI does not remove this gate.

After owner review of exact committed source and green CI, the user may
**separately** opt in to a global `hooks.Stop` entry under
`%CODEX_HOME%\hooks.json` or `%USERPROFILE%\.codex\hooks.json`.
Do not overwrite existing hooks. Example of a standalone file to merge:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /absolute/trusted/path/model_advisor_stop_hook.py",
            "commandWindows": "py -3 \"C:\\Users\\YOUR_USER\\AppData\\Local\\ADT-Personal\\toolkit-source\\integrations\\personal-mcp\\adt-personal\\hooks\\model_advisor_stop_hook.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Review/trust the exact definition in the supported **native Codex Desktop**
interface. If hook trust UI is unavailable there, do not enable it.
Never bypass trust to make an acceptance test pass. Updating the script
may require re-trusting it.

Remove only the added Stop hook entry to disable; an `AGENTS.md` advisor
disable alone does not disable a separately installed hook. No automatic
installation script is provided intentionally.

Live acceptance requires a positive complex-task case, a simple negative
control and no delegated model execution. Offline unit tests prove none of
these native client capabilities.
