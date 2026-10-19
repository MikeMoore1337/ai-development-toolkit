---
name: component-architecture
description: "Use when designing frontend component boundaries, composition, reusable UI parts and their contracts."
---

# component architecture

Inspect the actual frontend stack and project conventions before choosing tools or patterns. Follow repository rules and approval gates.

1. Inspect the current UI architecture, user flows, ownership, design conventions and existing reusable components.
2. Keep rendering, interaction state and data access separate only where responsibilities differ; prefer existing primitives to speculative abstractions.
3. Specify component inputs, emitted events, state owner and loading/empty/error behavior. Avoid side effects during rendering.
4. Check lifecycle, coupling, responsive behavior and compatibility with existing consumers.
5. Implement a representative change, test its main interactions and adjacent reuse, and remove abstractions that do not help.

**Output:** Component map, public contracts, verified changes and remaining coupling.
