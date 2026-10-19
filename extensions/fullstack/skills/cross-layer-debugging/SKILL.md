---
name: cross-layer-debugging
description: "Use when debugging a defect spanning user interface, API, worker, database or runtime environment."
---

# cross layer debugging

Inspect the existing project boundaries, technology and deployment constraints before proposing a change. Follow project approval gates.

1. Reproduce expected and observed behavior, including environment and timestamps, without recording secrets.
2. Trace the operation through network, backend and persistence using correlation IDs or available logs.
3. Identify the first layer diverging from an actual contract; separate product, cache, deployment and test harness issues.
4. Form a falsifiable cause hypothesis and check confirming and contradicting evidence before editing.
5. Fix the owning boundary minimally and repeat both failing and neighboring scenarios; label unsupported conclusions.

**Output:** Evidence chain, proven or provisional root cause, change and regression checks.
