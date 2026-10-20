# UX/UI manual acceptance (synthetic examples, not completed trials)

Use the actual user's product requirements, screenshots and rendered implementation when available. Record reviewer, date, viewport, platform, scenario, evidence path and result for **each** check; otherwise status NOT_TESTED.

| Check | Verification and expected result |
| --- | --- |
| Sources | Source R/AC/SR/UC/BR identifiers unchanged; assumptions and gaps visible |
| Flows | Main and alternative/error branches end in reachable states, recovery is possible |
| IA | Every required action reachable in navigation for its user role |
| Wireframes | Hierarchy, control labels, forms, empty/loading/error states described |
| Prototype | Click real controls, compare from/to/error states, keyboard and destination |
| Visual | Compare rendered output to approved baseline at matched viewport and UI state |
| Tokens | Reuse actual brand typography, spacing, colors, icons and modes |
| Responsive | Render desktop/mobile and tablet if relevant; zoom, long strings, safe-area, overflow |
| Accessibility | Check applicable WCAG 2.2 criteria: keyboard, focus, labels, contrast, error recovery, target size and reduced motion; separate auto/manual/assistive-tech results |
| Handoff | Developer can locate contract, state machine, tokens, assets, decisions and AC checks |
| QA | Visual comparison plus main interactions, not pixel similarity alone |
| Owner approval | Only OWNER_ACCEPTED after explicit review and proof |

Do not infer visual tests, WCAG compliance, browser interaction, 60 FPS or real AI-client skill activation from this checklist.
