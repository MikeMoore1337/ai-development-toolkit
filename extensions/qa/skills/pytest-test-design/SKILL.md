---
name: pytest-test-design
description: "Structure deterministic Python tests with pytest fixtures and parametrization. Use only when pytest is present."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Pytest Test Design

1. Discover project fixture conventions, plugins, Python version, and test execution commands.
2. Keep fixtures scoped to shared state lifetimes; parametrize meaningful cases rather than duplicating bodies.
3. Express explicit assertions with diagnostic failure messages when needed; verify persistent changes through reliable polling.
4. Avoid ordering dependencies, mutable global fixture state, hidden test skips and blanket retry plugins.
5. Keep focused tests fast; mark integration/external-resource tests according to the repository's test organization.

Use project-supported plugins only; do not install or introduce dependencies without explaining their value.

## Worked example and failure checks

Use the [task-specific field guide](references/FIELD_GUIDE.md) when the case involves multiple states, boundaries, missing evidence or an independent handoff. Its scenarios are synthetic, not proof of executed tests. For a simple case, apply the procedure above and do not load extra material.
