# Accessibility QA - web interfaces (Issue #62)

[Русская версия](ru/ACCESSIBILITY_QA.md) | [Skills catalog](SKILLS_CATALOG.md)

The optional accessibility-qa profile combines one specialist skill (accessibility-testing) with existing test-analysis-design, playwright-testing and quality-gate-assessment. This is an accessibility verification process, not a second UX/UI workflow controller, browser engine, axe-core replacement or WCAG certificate. No paid API, browser or external service is required for the offline example.

## First check, without terminal

Ask your AI assistant:

> Check whether users can use my website with a keyboard, enlarged text and a screen reader. Identify the key flows and available source materials, use the free Toolkit, do not change my app without permission, and clearly separate checks you ran from checks still needed.

Accessibility means people can perceive and use an interface with different input and presentation technologies. WCAG (Web Content Accessibility Guidelines) are W3C standards for web content. Level A lists fundamental criteria; AA adds requirements commonly targeted by web projects; AAA is more stringent and not automatically part of AA. In absence of a specified web target, propose WCAG 2.2 AA, but check jurisdiction before calling it a legal requirement.

Keyboard checks cover Tab and Shift+Tab order, activation, escape from dialogs and returning focus. Focus order should follow the user's task, and visible focus must not be hidden under fixed bars. Each field needs an accessible label and understandable, linked errors. Visible text is not always an accessible name read by a screen reader.

Contrast problems arise when foreground and actual background colors are too similar. Typical AA thresholds are 4.5:1 for normal text, 3:1 for large text and applicable non-text UI, with criterion-specific exceptions. For target size, SC 2.5.8 is not a blanket rule that every button must be 24x24; spacing and other exceptions matter. For responsive content evaluate real zoom, reflow, long localized text, overlays and keyboard conditions.

Automatic tools inspect only part of accessibility. A successful screenshot is not a keyboard test, visible status text is not proof of screen-reader announcement, and a static HTML inspection is not a rendered-browser result. Run manual keyboard tasks and appropriate NVDA/VoiceOver/TalkBack checks for applicable flows. Log browser/OS/AT, observed result and limitations; do not fabricate outcomes.

## Specialist test plan

> Prepare a WCAG 2.2 AA accessibility plan for a multi-screen web app with forms, dialogs, asynchronous status updates, keyboard-only operation and mobile reflow. Include SC mapping, exceptions, R/AC links, positive and negative test cases, independent observable oracles, actual browser/AT combinations, findings, severity, remediation and retest conditions. Mark anything unexecuted NOT_RUN and conformance NOT_ASSESSED.

Process: requirement -> applicable success criterion -> user task -> observable oracle -> performed check -> evidence -> potential/confirmed finding -> focused fix -> observed retest. Severity reflects blocked user goals, frequency and alternatives; it is not the WCAG A/AA/AAA level.

[Skill and complete contracts](../extensions/accessibility/skills/accessibility-testing/references/CONTRACTS.md) include mapping for keyboard, focus, semantics, labels, forms, contrast, motion, pointer targets, resize, dynamic announcements and AT. [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) is normative; [Understanding WCAG](https://www.w3.org/WAI/WCAG22/Understanding/) is informative. See [W3C Evaluation](https://www.w3.org/WAI/test-evaluate/) and [choosing tools](https://www.w3.org/WAI/test-evaluate/tools/selecting/).

## Reproducible zero-cost example

Two fabricated interfaces reside in `fixtures/accessibility/accessible.html` and `inaccessible.html`. The offline standard-library script checks only narrow structure, known ID references and declared opaque sRGB color pairs. It deliberately does not verify actual rendered CSS, keyboard, focus, assistive technology or WCAG conformance.

```bash
python scripts/validate_accessibility.py
python -m unittest tests.test_accessibility -v
```

To prevent regressions, retain requirement IDs, tie failures to reproducible scenarios, keep failing fixtures as negative tests and rerun verified browser/AT checks after fixes. The Toolkit source is read-only when used in another project. Return results in chat unless storage elsewhere is expressly authorized. No customer screenshots, logs, accessibility trees or project artifacts may be stored in Toolkit.

