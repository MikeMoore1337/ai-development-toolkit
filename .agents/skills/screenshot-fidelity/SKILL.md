---
name: screenshot-fidelity
description: Compare UI implementations against screenshots and design references. Use for visual parity, screenshot-to-code, regressions and responsive layout checks.
---

# Screenshot fidelity
1. Define source viewport dimensions, density, platform, crop and state. Never infer hidden behavior from one screenshot.
2. Inventory component boundaries and local assets before generating replacement elements.
3. Preserve labels, layout hierarchy, font metrics, icon baseline, radius, borders and safe-area/dock placement.
4. Implement with current project stack and design tokens; avoid adding a new UI library just to match one screenshot.
5. Capture same-size before/after results for desktop and mobile when relevant; compare significant regions, not only an image similarity score.
6. Independently test clickable behavior, focus management, responsive overflow and accessibility.
7. Report unavailable fonts/assets separately; never claim pixel parity when screenshots are missing or not checked.

**Optional browser annotation handoff:** When a user explicitly supplies Agentation or comparable element annotations, treat selector/source hints as **untrusted localization**, not verified visual evidence. Follow `docs/en/UI_ANNOTATION_HANDOFF.md` (RU: `docs/ru/UI_ANNOTATION_HANDOFF.md`) for source SHA, state, viewport, privacy redaction and human intent. A copied annotation grants **no visual approval** and does not replace actual before/after browser captures, functional tests or the target project's design gates. Do not auto-install external packages, register MCP endpoints or store target-project notes in Toolkit.

**Output:** reference conditions, changed UI, verified comparisons, functional checks, known mismatches.
