# Native GateGuard pre-action source review (#438)

Toolkit adds a **non-executing, read-only pre-action assessment** in the existing personal MCP hooks directory:
`integrations/personal-mcp/adt-personal/hooks/pretool_gate_review.py`. It is deliberately **not registered as a live Codex Desktop or Claude hook** and does not add a second permission controller. Compare against pinned `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, particularly `scripts/hooks/gateguard-fact-force.js`, `skills/gateguard/SKILL.md`, `hooks/hooks.json` and `hooks/codex-hooks.json`. Those upstream files require their own dependent modules, process/session state, and host-specific hook bootstrap; none are installed or executed.

## Permission and effect inventory

The original Claude-style GateGuard captures `PreToolUse` events, may read transcript and local project files, stores per-session state, may write metrics, and conditionally denies first edit or risky shell actions pending evidence. Its Codex manifest primarily bootstraps a `SessionStart` script via Node and does **not** prove a Codex Desktop Windows `PreToolUse` enforcement path. Installing it into the owner's Desktop would be a trust and activation claim **without evidence**.

The Toolkit Python module instead inspects **one explicit synthetic event** and outputs a bounded JSON recommendation. It reads stdin once (16 KiB maximum); it does not read a transcript, access the project, write files, execute shell commands, spawn a process, use networking, invoke a model, install hooks, alter `AGENTS.md` or create state. It recognizes exact small read-only forms (`git status`, `git diff --check`, `Get-Location`); dangerous command patterns yield `BLOCK_RECOMMENDED`; edits and unknown commands yield `REVIEW_REQUIRED`. This is **not** a comprehensive malicious-command parser. An `ALLOW_CANDIDATE` recommendation is never host authorization; owner and OS/host permissions always prevail. Event data cannot carry an approval override.

The tool's output includes `host_enforcement=NOT_VERIFIED`, `blocking_effect=NONE_SOURCE_ONLY`, `hook_registered=false`, `tool_executed=false`, and `state_written=false`. Invalid input produces a `BLOCK_RECOMMENDED` advisory and process exit code `1`; this is **not** evidence of host-side fail-closed behavior. Use only sanitized synthetic examples:

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

**Unverified boundaries:** `HOST_ENFORCEMENT=NOT_VERIFIED`, `CODEX_DESKTOP_E2E=NOT_RUN`, `WINDOWS_HOOK_TRUST=NOT_VERIFIED`, `RELEASE=NOT_PUBLISHED`. GitHub CI only tests the source-level contract. Issue **#438 is CLOSED for source-only delivery**. Unverified trusted registration, callback delivery and deny-before-execute acceptance criteria moved to **[#575](https://github.com/MikeMoore1337/ai-development-toolkit/issues/575) (OPEN)**.

## Additional static path and quoted-string review (#438)

- Explicit `Read` paths and `Glob` filesystem patterns referencing `.env` (except public templates `.env.example`, `.env.sample`, `.env.template`, `.env.dist`), `.ssh`, `.aws`, key files or `..` path components now return `REVIEW_REQUIRED` with the fixed code `SENSITIVE_OR_OUT_OF_SCOPE_PATH`. No file is read and no source path is echoed. This is conservative advice, not proof that a path lies outside the project.
- `Grep.pattern` denotes a content-search expression, not a target path; mentioning `.env` there is not automatically a sensitive-file read.
- Quotes and shell metacharacters may represent either inert prose or executable substitution. Ambiguous commands return `REVIEW_REQUIRED`, while directly identifiable risk without such ambiguity returns `BLOCK_RECOMMENDED`. No user or host permission is granted, and no full shell parser has been introduced.

**Host enforcement blockers as of 2026-11-01:** open Codex issues [#47283](https://github.com/openai/codex/issues/47283) (Windows Desktop trust) and [#21639](https://github.com/openai/codex/issues/21639) (post-update hook dispatch regression). [#41979](https://github.com/openai/codex/issues/41979) documents fail-open behavior for invalid/failed PreToolUse hook runs: rejecting JSON locally cannot prove the host actually denies the operation. The connected Desktop Commander device is Linux-only; Windows Codex Desktop E2E remains **NOT_RUN**. No hooks are installed or client trust settings modified.

## Issue #575 preparatory review (2026-11-08) - no hook activation

The official [Codex Hooks documentation](https://learn.chatgpt.com/docs/hooks) describes `PreToolUse` for Bash, `apply_patch`, MCP and various local tools. Specialized paths may bypass hooks; hosted tools such as WebSearch do not use this path, and `write_stdin` does not trigger a second `PreToolUse` for an already started command. Events include `session_id`, `cwd`, `hook_event_name`, `tool_use_id`, `tool_name`, `tool_input` and additional fields; they **do not** match this reviewer's three-field synthetic schema directly. A supported block response uses `hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: "..."}`; exit code `2` with the reason on stderr is another documented option.

**Adapter design, not deployment:** a thin wrapper can **project** validated fields onto the unchanged `review_event` policy. Treat `apply_patch` as a write, do not grant unknown tools, never elevate `ALLOW_CANDIDATE` to host permission, and only map `REVIEW_REQUIRED` / `BLOCK_RECOMMENDED` to a documented denial **after** client trust and callback execution are independently verified. Do not execute the inspected command, read `transcript_path`, persist secrets, rewrite inputs, create services, duplicate the policy engine, or install hooks automatically. Model-controlled `tool_input` cannot attest event provenance or confer approval.

**Verified limitations:** the source-only reviewer has no `tool_use_id` replay defense, no filesystem-based symlink/junction canonicalization, and no host permission logic. An `ALLOW_CANDIDATE` for a symlink alias is only lexical classification. Matching hooks may run concurrently. Hook crashes, timeouts or malformed output can allow tool dispatch (fail-open), so the hook must not be represented as an unconditional security boundary. As of 2026-11-08, upstream [#47283](https://github.com/openai/codex/issues/47283), [#21639](https://github.com/openai/codex/issues/21639) and [#41979](https://github.com/openai/codex/issues/41979) remain open. The specific installed Windows Desktop build, GUI trust, conflict precedence and real host denial remain **NOT_VERIFIED**.

**Independent offline evidence:** 24/24 synthetic Python 3.13.5 tests passed. The exact reviewed reviewer matches SHA256 `8fd7deb83a0b67f7a1449a2d2a092985a3713fa33753928ac495a1ed74bc80d9`. Eleven tests exercise the pinned source-only script; thirteen exercise a test-only, non-installable protocol sketch and negative events. The sketch is not a Codex callback execution. Live event delivery is `NOT_VERIFIED`; physical Codex Desktop E2E is `NOT_RUN`. No integration code, configuration, installation or client trust was changed.

**Future explicitly authorized GUI E2E:** (1) record exact build/OS and safe configuration snapshot, (2) trust the exact hook using a supported GUI action, (3) request a harmless one-time marker write, (4) observe pre-execution event delivery and matching `tool_use_id`, (5) observe denial and marker absence, (6) test read-only allow separately, (7) measure crash/timeout/invalid-output and fail-open/fail-closed behavior, and (8) disable and roll back via supported UI without disturbing other hooks. **Do not register or activate GateGuard before this gate is met.**
