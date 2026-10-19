# Reverse-order search responses

**Context:** User types query A, then query B. Server responses may arrive in any order; the screen must show the latest query.

| Event | Current query/version | Response | Allowed visible result |
| --- | --- | --- | --- |
| Start A | A / 1 | pending | loading A |
| Start B | B / 2 | pending | loading B |
| Finish B | B / 2 | data B | show B |
| Finish A | B / 2 | data A | ignore A; retain B |

**Rule:** on starting a request, increment the screen-scoped request version; on completion, commit only when response.version equals the current version AND the active query still matches. Cancellation can reduce waste but must not be the only correctness guard. In a cache, older A data may be stored under key A without changing the B view.

**Negative path:** A finishes last after B's success; an unconditional assignment would incorrectly show A. When B fails, show B's error and a B retry, not a late A success. If an optimistic write fails, roll back only that write's version to avoid undoing a newer update.

**Checks:** force B-before-A in a deterministic network stub, assert visible query and result both equal B; repeat with B error, navigation/unmount and a B retry. Verify no state update is made to an unmounted view. Separate client evidence from server conflict guarantees.

**Limits:** The version guard protects one UI owner. Multi-user concurrent writes need a server-side version, compare-and-swap or equivalent conflict policy. Pseudocode is framework independent.
