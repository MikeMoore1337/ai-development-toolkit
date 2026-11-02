# Normal Chat execution - connected apps first (#499)

This contract applies to the **ordinary ChatGPT conversation with the Toolkit plugin selected**. ChatGPT Work and Codex are **not prerequisites**. Toolkit is a task-scoped skill coordinator, not an executable host, filesystem bridge or autonomous daemon. Only host-exposed tools and connected apps that actually exist in the current turn can be called. This reference does not expand account limits, permissions or app availability.

## One user request -> one best feasible execution path

1. Understand the task and identify its authorized target (repository, supplied file or isolated project) and source-of-truth. Do not demand a developer prompt or an extra Work/Codex conversation. Respect user-imposed zero-additional-cost policies.
2. Check actual **current-turn** capabilities, not the plugin manifest alone: connected GitHub for repository work and CI; approved sandbox/remote agent (for example Hermes Agent) for local code and commands; host file/Python tools for analysis and artifacts; supported browser/image tools for visual output. Resolve target paths and active devices instead of assuming a private Windows filesystem is available.
3. Select the minimum task-specific Toolkit skill and inspect the original external skills required by the request or an observed standing user preference. For design, read packaged `USER_PREFERENCES.json` and [original selection and execution](../../toolkit-ui-review/references/ORIGINALS.md) before the final render. A saved `ALL_THREE` is already an opt-in; the current request need not name the tools. If an original is missing, perform the task-authorized setup after reviewing its source, license, immutable revision, files and required runtime; use a permitted isolated location and preserve existing files. Do not stop at "not installed" when a reviewed setup route is available, or ask again for already granted setup permission. A URL = `REFERENCE_ONLY`; a source read = `LOADED`; an actual tool invocation requires a verifiable tool result. Never claim an original engine executed because its SKILL.md was read. File presence alone does not establish native client discovery.
4. Execute permitted steps **in the same chat turn**, using available host actions. For GitHub: inspect issue/code, create a scoped branch/PR, run or examine exact-head CI and report verified outcomes. For a runner: inspect environment, use only authorized isolated workspaces, execute relevant tests/builds, read outputs and produce actual artifacts. For visual design: use original skill scripts if the executor is approved and ready; otherwise distinguish a native generated concept from an original skill result.
5. Confirm results and unresolved gates, including user visual acceptance before target UI changes, permissions before merge/deploy, security of third-party binaries/hooks and the absence of unexpected billing. Return a concrete artifact or a precise `BLOCKED` status, not a prompt to copy into Work.

## Host sandbox first - observed normal-chat browser pilot (#499)

For required design executables, follow [host preparation before invoking the original](../../toolkit-ui-review/references/ORIGINALS.md#prepare-the-host-before-invoking-the-original), including the host's actual network permissions and the original's failure disclosure.

When the ordinary ChatGPT host actually exposes a sandboxed Python/container environment, inspect its toolchain *there* before deciding that a remote Hermes Agent or Work is needed. A host may already provide Python, Node.js, Git, Playwright and Chromium. Use only tools that were genuinely discovered in the current turn; no assumption that every ChatGPT account or session has them.

### Original-skill executor failover when the preferred sandbox cannot prepare originals

`ORIGINAL_EXECUTOR_FAILOVER` is a routing check inside the existing Orchestra, not a new controller or an executable exposed by the plugin. An available Python/browser sandbox does not imply that it can resolve GitHub or download a pinned engine. Before marking a required original `NOT_RUN` or `BLOCKED`, distinguish runtime availability from **source acquisition, installed skill, native invocation, and its later stage results**.

1. Probe the preferred, authorized host's **task-relevant prerequisites**, including a read-only network/source check for immutable upstream revisions, executable discovery, and the required browser automation path. Do not use `git ls-remote` alone as proof of installation or browser success. Record a concrete DNS/proxy/filesystem/launcher outcome when observable, without claiming a cause solely from an opaque launcher error.
2. On a confirmed source-access or executable blocker, discover whether **another currently connected and authorized executor** can do the missing step (for example, a connected desktop device). Check actual device status, allowed operations, network, runtime and isolation before invoking it. A connected tool is not automatically an approved place for arbitrary binaries. Within the task's existing permission, fetch immutable reviewed sources into a fresh isolated workspace, preserve checksums/licences, avoid source hooks and global installation, and use the original unchanged launchers. Never write to the owner's existing dirty checkout, install on a production host, or tunnel around an explicit network/permission refusal.
3. Execute selected original commands and downstream applicable stages from the **same synthetic brief**; keep separate receipts (`source revision`, `command`, `exit code`, `output`) for Impeccable, Taste Skill and UI UX Pro Max. If a native browser inspector fails, mark `ORIGINAL_INSPECT_FAILED` and preserve its real error. Independent Playwright/Chromium QA may still pass, but must not be relabeled as a successful original inspector or a full original process. Preserve the original's documented launcher-failure disclosure and fallback.
4. When no alternative is available/authorized, report `BLOCKED_ORIGINAL_EXECUTOR` with the specific missing prerequisite, complete other safe work, and never fake a specialist invocation. An artifact saved only on a remote device is **not a downloadable chat artifact** unless the host actually transfers or exposes its verified path. Neither `ALL_THREE`, overall E2E, owner approval, nor production delivery is implied by individual command exit 0 results.

This failover uses only authorized host/connected-tool capabilities, never Work/Codex by default, paid APIs, privileged host installation, or a second design coordinator.

- Prefer host-provided, authorized execution for standalone prototypes, local data processing and focused QA. Project files and customer secrets are **not** automatically present in the sandbox.
- For a browser-visible design, use a real browser to capture the specified viewport(s), exercise a representative primary interaction and check JavaScript exceptions, horizontal overflow and network activity. Preserve the screenshot and a concise measurement receipt in the current chat or the explicitly permitted target project. Never put user design files in Toolkit's public repository.
- Built-in browser evidence is a distinct execution claim from an original skill invocation. An actual local Chromium screenshot can be `BROWSER_EXECUTED` even when Impeccable, Taste Skill and UI UX Pro Max are `NOT_RUN`. Claim a script or engine invocation only after running that original unmodified component with a verifiable result. Follow an original's own documented fallback when its launcher fails; preserve its required disclosure and remaining workflow instead of adding a Toolkit-wide stop. Report playbook use separately from an engine that remains `NOT_RUN` or `BLOCKED`. A fallback does not satisfy an explicit requirement for that engine to run.
- Do not auto-download engine binaries or install required runtime packages without the task's existing authorization and source review; use the host's own approval mechanism when it requires additional execution permission.
- Keep hook activation and production actions within their existing task permissions; never bypass browser isolation.

An observed **synthetic** pilot on 2026-11-01 ran in ordinary ChatGPT without Work/Codex: Python 3.13, Node.js 22, Git, Chromium and Playwright were present; a no-network illustrative HTML page was captured at 1440×900 and 390×844. Both viewports had 0 horizontal overflow, 0 JavaScript exceptions, 0 external requests, and the selection/add-to-cart interaction passed. This is a **single-session observation**, not a universal environment entitlement, a live e-commerce test, or original-skill L5 proof.

## Capability-based adapters

| Current host adapter | Useful observed actions | Absent capability to avoid inventing |
| --- | --- | --- |
| Connected GitHub app | Repository source reads/writes, PRs, comments, CI and exact SHA | Host browser rendering or installation on Windows |
| Connected sandbox/remote execution app | Read/process/write in explicitly allowed sandbox, tests, pinned skills if installed | Offline/paused device, nonexistent runtimes or outside mounts |
| ChatGPT host Python/files/image tools | File analysis, generated artifacts and images when supported | Uninstalled external executable skill invocation |
| Bundled skill and verified Toolkit GitHub guidance | Routing and original instructions actually read | Automatic background job, unlimited messages, private API grants |

If the required tool is unavailable, continue with useful work that genuinely fits the available scope and report the specific blocker: e.g. `RUNTIME_MISSING_PYTHON`, `DEVICE_OFFLINE`, `NO_AUTHORIZED_WRITE_APP` or `BROWSER_NOT_VERIFIED`. Do not claim a source-only smoke test proves native client activation.

## No Work and zero-cost boundary

Do not recommend Work as a default workaround for a normal ChatGPT task or exhausted Codex limits. Do not silently invoke paid APIs/CLI or install new services on the owner's VPS. An ordinary ChatGPT session still has account-specific message/tool limits. Full custom MCP with write actions is plan/workspace dependent; reuse existing authorized connected apps instead of assuming arbitrary write-MCP access. Do not promise background execution unless an actual scheduled task was created.

## Task receipt

For each material action report only actual evidence: the target and immutable revision, adapter and command/action performed, output status, tests or screenshot artifacts, and outstanding owner/CI/runtime gates. Use `EXECUTED / NOT_RUN / BLOCKED / FAILED`, and distinguish human design judgment from technical PASS. Retain no private project data in the shared Toolkit repository.
