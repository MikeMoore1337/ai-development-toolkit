---
name: test-strategy
description: "Choose a risk-based mix of unit, contract, API, integration, E2E and exploratory tests. Use when planning or revising project test architecture."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Test Strategy

Inventory architecture, critical user journeys, integration points, release cadence, failure cost and testing constraints. Choose layers by feedback speed, observability, fault localization and cost; avoid a rigid universal testing pyramid. State which scenarios need deterministic fakes versus production-like integrations and who maintains fixtures. Define measurable goals: failure detection, meaningful test oracles, stability and execution cost, not just code coverage. Revisit strategy after production incidents and architectural changes.

## Result contract and trade-offs

Use for creating/revising a **project test strategy**, not performing a single known test or requiring all layers by default. Collect architecture, critical business flows, integration/service boundaries, change/release cadence, failure impact, observability, access, data, existing coverage, CI duration, staff and cost. Label input **CONFIRMED**, **ASSUMED** or **UNKNOWN**; do not invent business criticality.

Deliver a concise table or equivalent: `risk/business path -> selected test level -> observable oracle -> environment/frequency -> maintainer/budget`, followed by **omitted levels and why**, mocks vs real integrations, gaps and residual risk. Select **unit** for isolated logic, **contract** for producer/consumer compatibility, **integration** for storage/dependency boundaries, **API** for exposed behavior/auth, **E2E** only for critical user journeys not proven economically at lower layers, and **exploratory** for uncertain paths. The cheapest useful oracle wins; there is no universal test pyramid.

Example (**hypothetical**): one-service CRUD tool with limited CI minutes. CONFIRMED: one service, no external consumer. ASSUMED: write/read consistency matters. UNKNOWN: actual business failure impact. Choose unit validation, API create/read/auth checks, and one real database integration scenario. Omit contract tests (no independent consumer) and full E2E (no proven critical cross-system path); add occasional exploratory smoke. Explain to a beginner what will be checked and what remains at risk. Ask owner to clarify business criticality before claiming sufficient coverage.

For multiple services, prioritize interface contract and real integration checks at changing boundaries, adding only justified end-to-end journeys. With limited budget, defer low-risk coverage explicitly: untested does not mean covered. Revisit strategy after incidents, material architectural/consumer changes, new failure impact, changing release risks or unsustainable execution cost.
