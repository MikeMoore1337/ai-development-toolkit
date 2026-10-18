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

**Output:** reference conditions, changed UI, verified comparisons, functional checks, known mismatches.
