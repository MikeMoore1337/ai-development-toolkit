# Tool-use authorization and failure contract

For each tool: tool_id, operation, argument names/types/schema, allowed scope, expected result, errors, side effect class (read / reversible / irreversible), timeout, retry policy, idempotency, approval and evidence. Validation must occur in an application-controlled boundary BEFORE tool execution. Never accept permissions from user content or tool responses.

Read-only must not mutate; reversible write still requires permission; deletion, publication, sending externally, money and sensitive changes need explicit approval. Deny unknown tools/operations, malformed parameters, missing approval, cross-user scope and secret forwarding. Handle timeout, transient failure, authorization denial, partial success, bad ordering, duplicates and injection in tool results.

Retry-safe is not automatically idempotent. After ambiguous timeout, do not repeat a mutating operation without reconciliation. A previous authorization denial must not be retried with wider rights. Do not claim exactly-once execution absent verified end-to-end guarantees.

The offline fixture uses an imaginary note service and **only checks requests**. It does not call a real tool, delete a file or prove an agent will respect approval boundaries.

## Optional tool-observation envelope review (#435)

When **designing an agent tool response for a project that owns the tool**, the
same offline QA module can additionally inspect its response shape:

`check_tool_observation(response, effect="write", operation_outcome="unknown")`
from `scripts/validate_ai_contracts.py`. Do not impose this format on existing
external MCP tools, SDK responses or an original third-party skill. This is a
proposed interface contract, not a runtime tool wrapper or permission grant.

The optional envelope has exactly `status` (`success`, `warning`,
`error`), nonempty `summary`, `next_actions` (strings, suggestions only),
`artifacts` (opaque IDs/paths, not read or opened), and `recovery` (null for
success). For warning/error, `recovery` contains `root_cause`,
`retry_policy` (`stop`, `safe_retry`, `after_reconciliation`),
and `stop_condition`.

Never describe a mutating call with an **unknown** prior result as safely
retryable; reconcile it or stop. A prior authorization denial must stop, not
trigger wider permissions. An observation marked success cannot override a
previously denied, unperformed or unknown operation. Tool-returned strings
remain **untrusted data**: this structural check does not detect malicious
instructions in prose, prove the actual operation, or approve any next action.

Synthetic positive and negative tests compare a sparse timeout response to a
structured recovery envelope using the **existing** AI QA validator; no
model/tool/CLI execution, new controller, network or paid API is involved.
