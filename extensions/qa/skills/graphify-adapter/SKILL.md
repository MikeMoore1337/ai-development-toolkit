---
name: graphify-adapter
description: "Optionally use a code graph to investigate callers, dependencies and change impact. Use only when an approved graph tool is available."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Graphify Adapter

Discover whether Graphify or another code graph exists in this project and whether running it is authorized. Prefer read-only queries. Compare graph edges with code references and tests; graphs can be stale or incomplete. If unavailable, fall back to language-aware search, source inspection and repository metadata and report reduced confidence. Do not install software, upload source code, run a remote indexer or make Graphify mandatory by default. Output a small path-based dependency map and unresolved edges.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
