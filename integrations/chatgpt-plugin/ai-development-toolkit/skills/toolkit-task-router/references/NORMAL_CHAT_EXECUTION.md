# Normal Chat execution - connected apps first (#499)

This contract applies to the **ordinary ChatGPT conversation with the Toolkit plugin selected**. ChatGPT Work and Codex are **not prerequisites**. Toolkit is a task-scoped skill coordinator, not an executable host, filesystem bridge or autonomous daemon. Only host-exposed tools and connected apps that actually exist in the current turn can be called. This reference does not expand account limits, permissions or app availability.

## One user request -> one best feasible execution path

1. Understand the task and identify its authorized target (repository, supplied file or isolated project) and source-of-truth. Do not demand a developer prompt or an extra Work/Codex conversation. Respect user-imposed zero-additional-cost policies.
2. Check actual **current-turn** capabilities, not the plugin manifest alone: connected GitHub for repository work and CI; approved sandbox/remote agent (for example Hermes Agent) for local code and commands; host file/Python tools for analysis and artifacts; supported browser/image tools for visual output. Resolve target paths and active devices instead of assuming a private Windows filesystem is available.
3. Select the minimum task-specific Toolkit skill and only the original external skills that are genuinely installed/available. A URL = `REFERENCE_ONLY`; a source read = `LOADED`; an actual tool invocation requires a verifiable tool result. Never claim an original engine executed because its SKILL.md was read.
4. Execute permitted steps **in the same chat turn**, using available host actions. For GitHub: inspect issue/code, create a scoped branch/PR, run or examine exact-head CI and report verified outcomes. For a runner: inspect environment, use only authorized isolated workspaces, execute relevant tests/builds, read outputs and produce actual artifacts. For visual design: use original skill scripts if the executor is approved and ready; otherwise distinguish a native generated concept from an original skill result.
5. Confirm results and unresolved gates, including user visual acceptance before target UI changes, permissions before merge/deploy, security of third-party binaries/hooks and the absence of unexpected billing. Return a concrete artifact or a precise `BLOCKED` status, not a prompt to copy into Work.

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
