---
name: e2e-testing
description: "Select high-value end-to-end scenarios and collect visible evidence. Use for critical user journeys spanning UI and backend."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# E2E Testing

1. Pick a small set of business-critical journeys with clear success and failure outcomes. Avoid duplicating every API unit test at UI level.
2. Verify user-visible result **and** underlying state when relevant; include navigation, permissions, errors and recovery.
3. Stabilize test setup, use accessible selectors and explicit async readiness; capture traces/screenshots on failures without secrets.
4. Exercise supported viewport/browser combinations and keyboard interaction when those are project requirements.
5. Separate a real browser run from generated test code or a manual visual inspection.

Include environment, build/commit, browser/version and evidence links in the handoff.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
