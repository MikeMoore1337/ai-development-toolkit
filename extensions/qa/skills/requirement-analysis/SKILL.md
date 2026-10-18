---
name: requirement-analysis
description: "Translate product requests into testable outcomes and identify gaps. Use when specifications are ambiguous, incomplete, or high-risk."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Requirement Analysis

1. Gather the observable user or system outcome, relevant actors, entry conditions and non-goals. Separate sourced facts, interpretations and unresolved questions.
2. Express acceptance criteria as Given/When/Then or an equivalent observable contract. Include success, rejection and recovery outcomes.
3. For every rule, define who owns it, where it is enforced and how it can be observed. Do not substitute an implementation detail for a requirement.
4. Prioritize unknowns by reversibility and potential harm. Ask only for blocking decisions; proceed with documented assumptions otherwise.
5. Report a requirement-to-evidence map including items that remain untestable.

Output: `R-ID | expected behavior | evidence source | test idea | unknowns`. Avoid inventing business rules.
