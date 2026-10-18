---
name: design-system-consistency
description: Audit or implement interfaces without breaking an existing design system. Use for dashboards, mobile web, PWA, screens and design-to-code tasks.
---

# Design system consistency
Use a restrained combination of established UI review patterns. Generic 'premium' aesthetics must never override local product decisions.

1. Inspect existing tokens, fonts, icon family, radii, borders, spacing, responsive breakpoints and accessible states.
2. Reuse existing patterns; do not blindly apply a taste-skill preset, UI UX Pro Max palette or another project's branding.
3. Compare before/after at representative viewports; for screenshot tasks preserve target geometry, visual hierarchy and spacing.
4. Review flows: discovery, empty/loading/error/success states, keyboard focus, readable labels, reduced motion, high zoom and safe-area insets.
5. Prevent new excessive borders, repeated card nesting, unexplained shadows, random radius changes and multiple icon families.
6. Prefer semantic CSS tokens and minimal component diff. Respect any user-approved screenshots and release gates.
7. Visual aesthetics remain a product judgment; objective checks prove interaction, not beauty.

**Output:** design constraints, exact divergences, before/after evidence, accessibility and regression notes.
