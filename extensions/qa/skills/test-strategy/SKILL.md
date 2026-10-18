---
name: test-strategy
description: "Choose a risk-based mix of unit, contract, API, integration, E2E and exploratory tests. Use when planning or revising project test architecture."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Test Strategy

Inventory architecture, critical user journeys, integration points, release cadence, failure cost and testing constraints. Choose layers by feedback speed, observability, fault localization and cost; avoid a rigid universal testing pyramid. State which scenarios need deterministic fakes versus production-like integrations and who maintains fixtures. Define measurable goals: failure detection, meaningful test oracles, stability and execution cost, not just code coverage. Revisit strategy after production incidents and architectural changes.
