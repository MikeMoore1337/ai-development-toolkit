# UX/UI Design Orchestra - specialist handoff and evidence

Toolkit coordinates existing skill work in one user-facing language and cannot replace the native workflows of external specialists.

## Shared brief for actual reviewers

Give each reviewer the user's design goal; target project/version if observed; existing brand rules; relevant reference images and prior user preference; action/flow and screen size; permitted tools; unknown facts; and the **no-target-write** rule before owner approval. Report findings as verified observations or labelled hypotheses. Real subagents need actual tool-call evidence, and sequential perspectives must be identified as `SEQUENTIAL`.

## Tool-native creative freedom

A user or original specialist may choose **any** appropriate design language: hero, storefront grid, editorial photography, cards, SaaS structures, unusual typography, gradients and other visual elements are not prohibited. Do not impose a fixed number of concepts, alternative wireframes, style risks or cross-domain swap experiments. Follow the actual tool-native workflow and present only alternatives actually explored. Good taste cannot be reduced to an "anti-template PASS".

## Preferred visual baseline and version lineage

When an earlier direction is preferred or accepted, record in the consumer project/chat (never Toolkit):
- baseline version/actual image references, whether user-preferred or explicitly approved, and strongest visual qualities;
- candidate version/actual images on comparable relevant viewports;
- actual side-by-side observations on composition, typography, subject photography, expression and task usability (mark uncertainty explicitly);
- distinct technical QA findings with source/viewport/interaction evidence;
- a recommendation to KEEP/REFINE the baseline, PROPOSE the candidate, or remain UNDECIDED, and the owner's **real** choice.

If the new design lacks demonstrated visual benefit, do not silently replace the previously preferred candidate just because technical checks pass. A reviewer can still show the candidate and ask the owner; do not claim an automatic aesthetic ranking.

## Final report

1. Scope, mode, baseline SHA/project design source, no-write statement and tools actually read/invoked.
2. Visuals actually produced: file/URL, version, viewport, provenance, observed status. No fake image references.
3. One or several candidate directions **as actually produced**, with reasons to keep or change them. If prior preferred version exists, preserve its refs/strengths and present a visual comparison before a replacement recommendation.
4. Technical checks: real viewport, overflow, keyboard/focus, errors and interaction states; explicit `NOT_VERIFIED` if not observed.
5. Artistic judgment: specific visual observations, competing advantages, uncertainty and owner preference. Clearly separate from technical PASS.
6. Human checkpoint: `AWAITING_VISUAL_APPROVAL` only when a useful visual package exists; otherwise `VISUAL_PACKAGE_MISSING`. Do not claim `OWNER_ACCEPTED` without user approval for a specific version. `implementation: NOT_STARTED` until a separately authorized follow-up.

The optional `scripts/validate_ux_ui_orchestra.py` checks declarations and linked evidence, **not pixels, attractiveness, actual client calls or owner approvals**.
