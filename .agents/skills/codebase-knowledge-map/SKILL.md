---
name: codebase-knowledge-map
description: Map large repositories, dependency flows and component boundaries when ordinary code search is insufficient. Use for change impact analysis and architecture discovery.
---

# Codebase knowledge map
1. Begin with targeted code search, tests and dependency files. Create a graph only when cross-module relationships materially affect the decision.
2. Gather deterministic edges (imports, calls, definitions) and label heuristically inferred edges separately.
3. Identify entry points, state owners, external IO, tests and changed call paths.
4. Check whether graph tooling has locally available parsers and an acceptable data flow; keep private code local unless explicitly authorized.
5. Validate suspicious relationships against original source code. A graph is a navigation aid, not ground truth.
6. Avoid leaving generated full-repo reports in commits unless needed; timestamp graph output and invalidate it after relevant changes.

**Output:** affected nodes, evidence-backed relationships, uncertain edges, recommended focused tests.
