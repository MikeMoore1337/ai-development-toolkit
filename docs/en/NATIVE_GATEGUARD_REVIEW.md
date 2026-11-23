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

## Static reviewer hardening (#438, 2026-11-01)

This remains **advisory only**, with no installed hook, executed action or granted permission. Duplicate JSON keys, `NaN`/`Infinity`, malformed encoding, unsupported control characters, excessive nesting and oversized input are rejected. A `RecursionError` produces bounded `BLOCK_RECOMMENDED` JSON without a traceback or original command.

Recognition now covers directly visible `git -C ... reset --hard`, `git clean --force`, `git push -f`, `git worktree remove`, PowerShell `ri`/`Remove-Item` and command chains. Inert text such as `echo "rm -rf file"` is no longer falsely treated as a confirmed destructive operation. Unknown syntax, escaping and nested interpreters always require review rather than an allow recommendation.

**ECC capability -> Toolkit -> verified gap -> decision -> test:**

| ECC capability | Existing Toolkit | Gap | Decision | Test |
| --- | --- | --- | --- | --- |
| Claude `PreToolUse` execution denial | Explicit input reviewer | No verified Codex Desktop pre-execution callback | Do not register hooks; keep enforcement unverified | Result contract; client E2E NOT_RUN |
| Shell/Git/PowerShell scrutiny | Bounded lexical classifier | Known variant misses and inert-quote false positives | Harden direct-operation checks; unknowns require review | `test_pretool_gate_hardening.py` |
| Transcript evidence and session state | Intentionally absent | Not needed for source-only analysis | Do not port, log or collect | Idempotency/side-effect tests |
| Input validation and trust | JSON with size limit | Duplicate keys and deep recursion | Reject ambiguous payloads; catch `RecursionError` | Negative CLI tests |
| ECC Node bootstrap and SessionStart | Not integrated | No proven Codex `PreToolUse` GateGuard | Do not install or copy | Pinned upstream inspection |

**Provenance.** Consulted `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b` (MIT, Affaan Mustafa) and independently `zunoworks/gateguard` (MIT, Hirokazu Seto / ZUNO WORKS K.K.). No original third-party hook or dependencies have been copied. The ECC root license is not, by itself, evidence of third-party file provenance.

Submit one synthetic JSON event to the documented Python script's stdin to use the optional reviewer. `ALLOW_CANDIDATE` is not permission to run; `BLOCK_RECOMMENDED` is not a host-enforced denial. Regex patterns and exact allowlists are not a shell parser or proof against obfuscation. User/project/client/sandbox permissions retain precedence. To disable, stop invoking the optional script; rollback source changes through an ordinary PR, since client configurations were never changed.

**Unverified boundaries:** `HOST_ENFORCEMENT=NOT_VERIFIED`, `CODEX_DESKTOP_E2E=NOT_RUN`, `WINDOWS_HOOK_TRUST=NOT_VERIFIED`, `RELEASE=NOT_PUBLISHED`. GitHub CI only tests the source-level contract. Keep #438 OPEN until an authorized host demonstrably delivers a trusted callback before execution and refuses a harmless synthetic test operation.

## Additional static path and quoted-string review (#438)

- Explicit `Read` paths and `Glob` filesystem patterns referencing `.env` (except public templates `.env.example`, `.env.sample`, `.env.template`, `.env.dist`), `.ssh`, `.aws`, key files or `..` path components now return `REVIEW_REQUIRED` with the fixed code `SENSITIVE_OR_OUT_OF_SCOPE_PATH`. No file is read and no source path is echoed. This is conservative advice, not proof that a path lies outside the project.
- `Grep.pattern` denotes a content-search expression, not a target path; mentioning `.env` there is not automatically a sensitive-file read.
- Quotes and shell metacharacters may represent either inert prose or executable substitution. Ambiguous commands return `REVIEW_REQUIRED`, while directly identifiable risk without such ambiguity returns `BLOCK_RECOMMENDED`. No user or host permission is granted, and no full shell parser has been introduced.

**Host enforcement blockers as of 2026-11-01:** open Codex issues [#47283](https://github.com/openai/codex/issues/47283) (Windows Desktop trust) and [#21639](https://github.com/openai/codex/issues/21639) (post-update hook dispatch regression). [#41979](https://github.com/openai/codex/issues/41979) documents fail-open behavior for invalid/failed PreToolUse hook runs: rejecting JSON locally cannot prove the host actually denies the operation. The connected Desktop Commander device is Linux-only; Windows Codex Desktop E2E remains **NOT_RUN**. No hooks are installed or client trust settings modified.

## Optional Codex PreToolUse adapter (#575)

`integrations/personal-mcp/adt-personal/hooks/codex_pretool_gate.py` is an optional, non-installed protocol projection around the existing `review_event`. It does not register a hook. It returns an empty object for an `ALLOW_CANDIDATE`, leaving all Codex, sandbox, OS and owner permissions in force. `REVIEW_REQUIRED`, `BLOCK_RECOMMENDED`, malformed data, unknown tools and unsupported metadata result in documented JSON `deny`. It does not execute the tool, alter `updatedInput`, read transcripts, log input or write state. It is not a general shell parser or a security boundary.

**Directory constraint:** The documented `cwd` identifies the session. Source for Codex `rust-v0.171.0-alpha.13` substitutes the resolved execution directory for a local `exec_command`, but falls back to the session directory for remote execution. The event does not establish which case applies. By default the adapter denies Bash, including read-only calls. The owner may opt in to `--assume-local-exec-cwd` only for an independently verified local-only trial on the matching build; this is an assumption, not host attestation. Resolved paths, including symlinks and Windows junctions, must be inside the configured root. This check cannot prevent later filesystem changes or establish isolation.

**Opt-in and rollback:** do not activate this adapter until its exact client build, trust, effective-directory event shape, deny, benign read, failure modes and rollback have been tested in an isolated project. For an explicitly approved trial, configure one project-local `PreToolUse` command in the normal Codex hook format, with the absolute Python interpreter and adapter paths and `--project-root` set to that project's absolute directory. On Windows PowerShell the command must use the call operator, e.g. `& 'C:\path\python.exe' 'C:\path\codex_pretool_gate.py' --project-root 'C:\path\project'`; escape it correctly for the chosen JSON/TOML file. Review and trust the exact hook in the official UI. Preserve the previous configuration and do not duplicate existing handlers. Disable it in the UI and restore only the trial configuration afterwards; verify that unrelated hooks and trust state were not changed. Merely removing the source file is not a verified rollback.

A Windows Desktop `26.1117.41037` test on 2026-11-23 verified one **separate test callback** delivered a Bash event, returned `deny`, and prevented a unique marker; a separate `pwd` succeeded. The actual adapter above was not used in that test. Callback failures, unhooked tool paths and multiple hooks remain separate questions. Hook failures can permit dispatch, so local input rejection must never be described as guaranteed host fail-closed behavior.

On 2026-11-23, a separate trusted test callback in a fresh local Windows Desktop session received three marker calls and intentionally crashed, returned malformed JSON, or exceeded its two-second timeout. Each marker was created; no hook warning was reported. For these measured cases, `HOST_FAIL_CLOSED=NOT_SUPPORTED`. This does not establish behavior for other tool paths, callback launch failures, or hook conflicts.

Redacted local receipt (UTC): test callback `gate575-canary-v2` denied `exec-9e434187-201d-44e9-972e-9e230fc61302` at 08:23:16 on 2026-11-23; the independent marker check found no file. The safe read `exec-f40ecd78-6669-4570-b17c-5cfca60a7246` succeeded. Failure callback `gate575-failure-v3` received crash `exec-1a3c28d6-ca96-4f89-a132-fb3c19dad089`, invalid `exec-8111a0d9-ec74-4c44-aced-fff72198120e`, and timeout `exec-c4dd1a6f-0d21-44dc-a650-ffa5a07ca931` at 08:49:56, 08:50:00, and 08:50:04 respectively; the three harmless marker files were present. These observations are for the separate test callbacks, not this adapter.
