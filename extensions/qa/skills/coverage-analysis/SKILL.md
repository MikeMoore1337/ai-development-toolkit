---
name: coverage-analysis
description: "Assess test coverage of requirements and risks instead of relying only on line percentage. Use for release gaps and strategy reviews."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Coverage Analysis

1. Collect requirements, critical flows, known incidents and actual execution evidence.
2. Map every risk to tests or controls, distinguish planned versus executed checks, and flag ambiguous coverage.
3. Use branch/line coverage as supporting evidence only; high coverage does not guarantee oracle quality.
4. Highlight duplicate low-value tests and single points of failure in the verification strategy.
5. Prioritize gaps by impact, likelihood and detectability; identify a targeted next test rather than demanding arbitrary percentages.

Output `risk | test/evidence | uncovered behavior | priority | next action`. Do not extrapolate from sampled tests to full confidence.
