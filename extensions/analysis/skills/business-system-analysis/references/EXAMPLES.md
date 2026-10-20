# Synthetic worked example: household expenses

[Machine-checkable example](EXAMPLE_EXPENSES.json) | [Contract](SYSTEM_SPEC_CONTRACT.json)

This fictional example reuses Product Discovery #53 and Delivery Management #54 source identifiers **unchanged**:

| Product source | System refinement | Rule / scenario | Acceptance | QA status |
| --- | --- | --- | --- | --- |
| R1: add expense | SR1 | BR1, UC1 | AC1: record/totals; AC2: reject invalid | NOT_WRITTEN |
| R2: totals | SR2 | BR2, UC2 | AC3: totals equal displayed entries | NOT_WRITTEN |
| R3: edit/delete | SR3 (delete path only) | UC3 | AC4: deletion updates totals | NOT_WRITTEN |

SR3's edit behavior remains a gap for a full specification; this example does not invent an AC for edits. Detailed tests are not implemented, CI for an actual app is NOT_RUN and AI-client activation is NOT_MEASURED. No real personal data or observed performance is used.

Stakeholder: a hypothetical household expense keeper (ASSUMPTION); no fabricated interview.

Process (plain text, **not BPMN 2.0**):

    START (user opens add form)
      -> enter amount -> validate?
      -> accepted: create entry -> update list and totals -> END
      -> rejected: show invalid amount; persist nothing -> END
      -> cancelled: persist nothing -> END

Domain: Expense record; an optional ReportingPeriod is merely a PROPOSED entity, not an approved database table. Performance has status UNKNOWN without invented latency; no external integration is required by the MVP.

Decision D1 about refunds/negative values is UNRESOLVED. PRD and Delivery Plan contradictions must preserve both source references; no invented business logic is accepted. Backend decides actual storage/API using architecture-decisions/api-design. Frontend receives states and rules. UX/UI (#56) receives journeys and errors. QA receives original R/AC and proposed mappings, with no fake PASS.
