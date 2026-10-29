# Native GateGuard pre-action source review (#438)

Toolkit adds a **non-executing, read-only pre-action assessment** in the existing personal MCP hooks directory:
`integrations/personal-mcp/adt-personal/hooks/pretool_gate_review.py`. It is deliberately **not registered as a live Codex Desktop or Claude hook** and does not add a second permission controller. Compare against pinned `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, particularly `scripts/hooks/gateguard-fact-force.js`, `skills/gateguard/SKILL.md`, `hooks/hooks.json` and `hooks/codex-hooks.json`. Those upstream files require their own dependent modules, process/session state, and host-specific hook bootstrap; none are installed or executed.

## Permission and effect inventory

The original Claude-style GateGuard captures `PreToolUse` events, may read transcript and local project files, stores per-session state, may write metrics, and conditionally denies first edit or risky shell actions pending evidence. Its Codex manifest primarily bootstraps a `SessionStart` script via Node and does **not** prove a Codex Desktop Windows `PreToolUse` enforcement path. Installing it into the owner's Desktop would be a trust and activation claim **without evidence**.

The Toolkit Python module instead inspects **one explicit synthetic event** and outputs a bounded JSON recommendation. It reads stdin once (16 KiB maximum); it does not read a transcript, access the project, write files, execute shell commands, spawn a process, use networking, invoke a model, install hooks, alter `AGENTS.md` or create state. It recognizes exact small read-only forms (`git status`, `git diff --check`, `Get-Location`); dangerous command patterns yield `BLOCK_RECOMMENDED`; edits and unknown commands yield `REVIEW_REQUIRED`. This is **not** a comprehensive malicious-command parser. An `ALLOW_CANDIDATE` recommendation is never host authorization; owner and OS/host permissions always prevail. Event data cannot carry an approval override.

The tool's output includes `host_enforcement=NOT_VERIFIED`, `blocking_effect=NONE_SOURCE_ONLY`, `hook_registered=false`, `tool_executed=false`, and `state_written=false`. Invalid input fails closed. Use only sanitized synthetic examples:

```text
{"schema_version":1,"tool_name":"Bash","tool_input":{"command":"git status --short"}}
```

```sh
python integrations/personal-mcp/adt-personal/hooks/pretool_gate_review.py
```

Pass JSON via stdin; no command is executed. The tool is not automatically invoked by any AI client. Native Codex Desktop activation remains **NOT_VERIFIED**; a real pre-execution host callback with verified semantics, explicit owner permission, no duplicate hook and observed denial of a synthetic destructive action are required before describing it as a protective hook.

## Verification and rollback

Offline unit tests cover benign reads, Windows PowerShell, destructive Git/shell commands, SQL, unknown commands, compound and nested shell forms, bad schema, duplicate event idempotence and no secret echo. No paid API, Codex CLI, Claude CLI, external ECC runtime or telemetry. Undo is removal of these optional source files/docs/tests through an ordinary reviewed PR; host settings are untouched. A separate versioned Toolkit release and interactive Windows acceptance still require their own gates.
