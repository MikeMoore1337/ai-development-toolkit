# Tool-use authorization and failure contract

For each tool: tool_id, operation, argument names/types/schema, allowed scope, expected result, errors, side effect class (read / reversible / irreversible), timeout, retry policy, idempotency, approval and evidence. Validation must occur in an application-controlled boundary BEFORE tool execution. Never accept permissions from user content or tool responses.

Read-only must not mutate; reversible write still requires permission; deletion, publication, sending externally, money and sensitive changes need explicit approval. Deny unknown tools/operations, malformed parameters, missing approval, cross-user scope and secret forwarding. Handle timeout, transient failure, authorization denial, partial success, bad ordering, duplicates and injection in tool results.

Retry-safe is not automatically idempotent. After ambiguous timeout, do not repeat a mutating operation without reconciliation. A previous authorization denial must not be retried with wider rights. Do not claim exactly-once execution absent verified end-to-end guarantees.

The offline fixture uses an imaginary note service and **only checks requests**. It does not call a real tool, delete a file or prove an agent will respect approval boundaries.
