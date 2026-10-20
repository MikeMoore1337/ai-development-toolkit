---
name: accessibility-testing
description: "Evaluate web UI accessibility using applicable WCAG success criteria, keyboard/focus scenarios, assistive-technology protocols and evidence-backed findings. Use for accessibility audits and regression tests; not for ordinary styling, isolated Playwright scripting or feature delivery."
metadata:
  pack: "accessibility"
  version: "1.0.0"
---

# Accessibility QA

**Use for:** "Проверь доступность сайта", "Проверь WCAG 2.2 AA", "Подготовь keyboard/focus QA", "Проверь контраст и screen reader", "Accessibility test plan".

**Do not use for:** ordinary React fixes, attractive UI design (ux-design-process), screenshot comparison (screenshot-fidelity), motion-only tuning (motion-quality), generic Playwright automation (playwright-testing), API/load/security tests, releases or general feature delivery. Do not become another QA/workflow controller.

1. Inventory the real UI, platform, user goals, flows, pages, components, focus transitions, forms, responsive breakpoints, dynamic content and permissions. Preserve existing R-ID/AC-ID/UC-ID; unknown requirements remain unknown. For web, use [WCAG 2.2](https://www.w3.org/TR/WCAG22/) and select applicable criteria/levels/exceptions. If unspecified, propose AA as a target, not as a universal legal duty. Native applications require platform-specific requirements, not browser-only evidence.
2. Reuse UX handoff (ux-design-process), forms-validation, motion-quality, screenshot-fidelity, test-analysis-design, playwright-testing and quality-gate-assessment where relevant. Construct traceable test contracts and findings using [contracts and protocol](references/CONTRACTS.md). Require a user-observable oracle and explicit applicability, including exceptions.
3. Distinguish structural checks of known fixture markup, numeric sRGB-pair contrast, real browser keyboard/tab order, Shift+Tab, focus visibility and restoration, target-size geometry with exceptions, reflow/zoom, modal escape, keyboard alternatives to drag, role/name/state and dynamic status announcements. A static HTML or CSS declaration cannot prove keyboard operation, actual rendered colors, screen-reader announcements or real pointer geometry.
4. Plan combinations of browser, device, viewport and assistive technology. Use actual NVDA, VoiceOver, TalkBack or other available technology for named compatibility claims; JAWS is not mandatory. For a real test record OS, browser, AT/version, task, operator, observations, failures and limitations. Unavailable tools -> NOT_RUN or BLOCKED, never an automatic PASS.
5. Register potential versus confirmed findings, reproduction, affected task, observed impact, evidence, severity independent of WCAG level, minimal remediation and retest oracle. Blockers prevent the key task without an accessible alternative. Verify fixes by rerunning the same observable scenario, not by developer assurance.
6. Return results in chat by default. When using Toolkit in a target project, ALL Toolkit copies are read-only; never save user screenshots, DOM trees, logs, reports or fixtures to Toolkit. Respect the target's permission gates. No paid API, browser installation or external scan required.

Offline synthetic only: `python scripts/validate_accessibility.py` and `python -m unittest tests.test_accessibility -v`. These validate narrow example markup and data contracts, not real keyboard, browser, AT or WCAG conformance. English/Russian user guides: `docs/ACCESSIBILITY_QA.md` and `docs/ru/ACCESSIBILITY_QA.md`.

