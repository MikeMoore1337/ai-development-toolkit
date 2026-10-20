# Accessibility QA - test and finding contracts

These records are portable, not a WCAG certification. Source: [WCAG 2.2 W3C Recommendation](https://www.w3.org/TR/WCAG22/), [informative criterion explanations](https://www.w3.org/WAI/WCAG22/Understanding/), [W3C evaluation methodology](https://www.w3.org/WAI/test-evaluate/). The W3C Recommendation dated 12 December 2024 is the checked edition. The explanations are informative, not additional normative criteria.

## Applicability and reuse matrix

| Area | Reuse | Specialized gap |
| --- | --- | --- |
| UX planning, focus, user flows | ux-design-process | Audit realized interaction and evidence |
| Forms, instructions, errors | forms-validation | Label/error oracles and regression |
| Keyboard, semantic locators, browser | playwright-testing | Apply SC, manual/AT verification |
| Visual state and focus | screenshot-fidelity | Screen-reader and focus management separate |
| Motion/reduced motion | motion-quality | Apply 2.2.2, 2.3.1 and context conditions |
| Acceptance, findings, severity | test-analysis-design, quality-gate-assessment | Trace WCAG criteria and evaluate remediation |

Do not spawn individual mini-skills for keyboard, contrast, ARIA, forms or screen readers. Don't install all QA skills.

## Portable test contract

Required keys of validate_test: test_id, source_requirement, user_goal, target_interface, interaction, guideline, criterion, level, preconditions, input, expected, oracle, method, environment, technology, evidence, status, severity, remediation, retest, limitations. Preserve R/AC/UC IDs, record applicability/exception in limitations if relevant. User goal and observable oracle are mandatory; an assertion in source code is not observed behavior.

Allowed statuses: PASS, FAIL, NOT_RUN, BLOCKED, NOT_APPLICABLE (reason required), NEEDS_MANUAL_REVIEW, INCONCLUSIVE. A PASS needs executed observation and matching verification method. For browser, keyboard, manual or assistive-technology methods, record operator and actual environment. For AT checks, identify technology and version if known. A synthetic static PASS cannot promote the corresponding runtime check. A self-declared evidence record still needs actual corroboration.

Evidence kinds are independent: STATIC_CHECKED, CONTRACT_CHECKED, BROWSER_TESTED, KEYBOARD_TESTED, ASSISTIVE_TECH_TESTED, MANUAL_REVIEWED and CONFORMANCE_ASSESSED. Do not promote one into another. Report BROWSER_ACCESSIBILITY=NOT_TESTED and ASSISTIVE_TECHNOLOGY=NOT_TESTED without runtime proof. Offline validate_report intentionally permits only WCAG conformance status NOT_ASSESSED; formal scope-wide assessment requires separate W3C WCAG-EM procedure and review.

A coverage report lists applicable required_criteria and tests. Missing criteria fail the offline contract. Don't silently omit SCs not automatable: add NOT_RUN/NEEDS_MANUAL_REVIEW or justified NOT_APPLICABLE as appropriate.

## Selected web WCAG 2.2 criteria

| SC | Level | Typical investigation |
| --- | --- | --- |
| 1.3.1 | A | Structural relationships |
| 1.4.1 | A | Color is not sole information carrier |
| 1.4.3 | AA | 4.5:1 normal text, 3:1 large text, with exceptions |
| 1.4.4 | AA | Resize Text |
| 1.4.10 | AA | Reflow and specified two-dimensional exceptions |
| 1.4.11 | AA | 3:1 applicable non-text UI/graphics, exceptions |
| 2.1.1, 2.1.2 | A | Keyboard operation and traps |
| 2.2.2, 2.3.1 | A | Pausable movement, flashes |
| 2.4.3 | A | Focus Order |
| 2.4.7, 2.4.11 | AA | Focus Visible and Not Obscured Minimum |
| 2.4.12 | AAA | Focus Not Obscured Enhanced (not AA requirement) |
| 2.5.7, 2.5.8 | AA | Drag alternatives; 24x24 CSS px target, spacing and other exceptions |
| 3.3.1, 3.3.2 | A | Error identification, labels/instructions |
| 4.1.2 | A | Name, Role, Value |
| 4.1.3 | AA | Status Messages |

Other applicable success criteria remain in scope for real assessments. A short registry is not an exhaustive WCAG evaluator. Distinguish standards from desirable interaction recommendations. WCAG 2.2 AA is a reasonable starting goal for web content if the target is unspecified, not universal legal advice. Native app evaluations need platform norms.

## Keyboard, focus, responsive and AT protocol

1. Record actual browser/OS and, when used, screen reader/version, input mode and task. Test Tab and reverse Shift+Tab, role-dependent Enter/Space/arrows, open/close dialog, Escape where expected, focus restoration after dialog removal, deleted element, route changes and validation.
2. Verify focus order, visibility under sticky overlays, navigation completion without pointer and expected accessible names/states using actual runtime. When appropriate check zoom 200%, reflow at 320 CSS px equivalent, text scaling, localized long strings, mobile keyboard, fixed panels and safe areas. This guidance is not blanket numeric success for every layout or exception.
3. For target size use rendered rectangles and applicable 2.5.8 spacing/equivalent-target/inline/user-agent/essential exceptions; do not label all targets smaller than 24x24 nonconformant.
4. Inspect dialogs, loading, errors and save announcements with real assistive technology; an aria-live attribute does not demonstrate actual announcement. For NVDA/VoiceOver/TalkBack record task, result, operator, environment and failure; paid JAWS not required.
5. For significant animation use applicable WCAG 2.2 criteria and product reduced-motion settings; reduced-motion is not a blanket AA mandate for every animation. Ensure state is not conveyed only by motion.
6. Hand a finding to engineering with expected versus observed behavior, SC and applicability, impact, reproduction, severity, minimal change and retest oracle. Rerun the same scenario after correction.

## Finding contract and severity

Fields: finding_id, component, user_flow, source_requirement, criterion, applicability, expected, actual, evidence, method, severity, impact, steps, remediation, retest_oracle, status, limitations. Statuses: POTENTIAL, CONFIRMED, FIX_PROPOSED, FIX_IMPLEMENTED, RETEST_PASS, RETEST_FAIL, NOT_TESTED. A static warning may remain POTENTIAL. CONFIRMED requires observation, and RETEST_PASS requires executed retest evidence; developer claims aren't sufficient.

Severity is separate from SC level. BLOCKER = core task inaccessible without an accessible alternative. HIGH = important or frequently used task impaired. MEDIUM and LOW depend on impact, frequency, alternatives, reach and actual evidence. Do not infer number of affected users.

## Offline oracle limitations

The narrow stdlib HTMLParser inspects synthetic IDs, explicit labels, known buttons, error references and main landmark. It is NOT an accessibility tree or general ARIA checker. The contrast oracle accepts only two known opaque final sRGB hex colors and uses relative linear luminance (channels <=0.04045: c/12.92; otherwise ((c+0.055)/1.055)^2.4). Ratio = (lighter+0.05)/(darker+0.05). Compare full precision before rounding; unknown alpha, backgrounds, gradients and unresolved CSS tokens must be rejected, not passed. Do not infer rendered contrast from declared CSS alone.

Offline command: `python scripts/validate_accessibility.py`. Reference and intentionally broken HTML live under `fixtures/accessibility` and contain fictional values only. No browser, paid tool, app deployment, external API or real AT was used.

