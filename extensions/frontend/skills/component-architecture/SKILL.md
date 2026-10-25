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

**External component selection gate:** For concrete proposals involving shadcn/ui, Magic UI, Tailwind, Radix/Base UI, Motion or similar component registries, first apply `docs/en/UI_COMPONENT_SELECTION.md` (RU: `docs/ru/UI_COMPONENT_SELECTION.md`). Evaluate existing primitives and exact upstream provenance/license before considering a dependency. A proposal is not implementation approval; do not add packages, copy components, change product visuals or bypass the target owner's visual gate merely because a registry includes the pattern. The optional source-only packet validator cannot prove browser correctness.

**Output:** Component map, public contracts, verified changes and remaining coupling.
