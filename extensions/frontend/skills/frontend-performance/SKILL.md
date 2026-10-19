---
name: frontend-performance
description: "Use when diagnosing or improving frontend speed with repeatable baseline and candidate measurements."
---

# Frontend performance

**Use for:** measurable slow rendering, interaction, payload or network paths. **Do not use for:** speculative optimization without a scenario or feature delivery orchestration.

**Inputs:** exact interaction, representative content, device/viewport, build mode, network conditions, current metrics and permission to run safe benchmarks.

1. Reproduce one slow user journey. Capture baseline metric definitions, runs, cache state, build/environment, variance and measurement tools; without baseline, report a hypothesis, not an improvement.
2. Locate the cost with evidence (network, JavaScript, rendering, asset loading or third-party work), rather than assuming bundle size alone determines speed.
3. Choose the smallest change first. Consider correctness, freshness, accessibility and failure behavior when deferring or caching work.
4. Compare candidate against baseline using the same instrumentation and conditions, with enough repetitions to notice noise. Report all relevant trade-offs; avoid cherry-picking a run.
5. Recheck the targeted interaction and adjacent functionality. When comparable measurements cannot be collected, mark performance benefit NOT_MEASURED.

**Output:** baseline and candidate table (or explicit missing measurement), bottleneck evidence, environment, regressions and decision.

See [comparable measurement example](references/baseline-comparison.md). Do not run live load against third-party or production services without approval.
