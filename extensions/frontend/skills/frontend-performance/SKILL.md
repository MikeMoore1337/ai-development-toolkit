---
name: frontend-performance
description: "Use when measuring or improving frontend responsiveness, rendering work, assets or network cost."
---

# frontend performance

Inspect the actual frontend stack and project conventions before choosing tools or patterns. Follow repository rules and approval gates.

1. Reproduce the slow scenario with representative data, device, viewport and network; record baseline metrics.
2. Identify measured costs: requests, payloads, rendering churn, long tasks, bundles, assets or third-party scripts.
3. Remove unnecessary work before suggesting caches, global stores, preloading or extra infrastructure.
4. Review freshness, accessibility and correctness trade-offs of deferral, memoization and loading changes.
5. Re-measure under comparable conditions and recheck adjacent interactions; mark unmeasured claims as hypotheses.

**Output:** Baseline, observed outcome or missing measurement, bottleneck and trade-offs.
