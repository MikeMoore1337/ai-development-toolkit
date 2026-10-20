---
name: playwright-testing
description: "Use Playwright to build stable UI assertions, network waits and traces. Use only in Playwright-enabled web projects."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Playwright Testing

1. Prefer semantic locators (`getByRole`, `getByLabel`, stable test IDs) to fragile CSS chains.
2. Assert visible user state; mock network only if a test is expressly a UI-isolated test.
3. Wait on observable conditions and bounded expect assertions; avoid `waitForTimeout` as a general synchronization strategy.
4. Isolate authentication, storage, fixtures and parallel worker data; attach traces or screenshots on failure.
5. Test responsive layout, focus/keyboard and offline/error states when applicable.

Inspect the project's Playwright version and conventions before suggesting API calls. Do not require Playwright in non-browser repos.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
