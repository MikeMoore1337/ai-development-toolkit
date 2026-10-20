# Manual acceptance and negative cases

These are prompts for a real model test, **not** claims that the model passed.

1. Plain idea without PRD -> compact draft with source ASSUMPTION or UNKNOWN; no mandatory repository URL.
2. PRD R1-R3 / AC1-AC4 -> preserve all IDs, show SR links, no invented accounts or external APIs.
3. PRD versus Delivery Plan conflict -> show both sources and UNRESOLVED_CONFLICT; no undocumented precedence.
4. "Can delete" versus "must never delete" on the same object -> conflict log, no arbitrary override.
5. Payment integration without endpoint/auth information -> CONTRACT_PENDING, no synthetic API contract.
6. Claims a provider has a free API but no evidence -> UNVERIFIED_DEPENDENCY.
7. "App must be fast" -> UNKNOWN metric or PROPOSED measurable target, never confirmed SLA.
8. User asks only for bug fix/unit tests/UI mockup/deployment -> do not activate this skill as controller.
9. User's private project or uploaded archive -> outputs in chat; Toolkit copies never modified.
10. A spec labels an unexecuted test PASS or a proposed decision APPROVED -> structural validator rejects missing evidence.
11. A Mermaid text flowchart -> no declaration of BPMN 2.0 conformance or deployed process.
12. Real client trials are NOT_MEASURED unless separately performed and evidenced.
