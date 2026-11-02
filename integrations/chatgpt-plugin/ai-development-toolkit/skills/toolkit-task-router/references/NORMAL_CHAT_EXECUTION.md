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
