---
name: example-skill
description: Use to verify draft release-note claims against existing merged changes; do not use to deploy or publish releases.
---

# Release-note verification example

## Activation

- Positive: "Check whether each release note matches a merged change."
- Positive: "Find missing user-visible fixes in this draft release note."
- Negative: "Deploy this release." Delegate to the authorized release workflow.
- Negative: "Build a new product feature." Use the feature implementation workflow.
- Can combine with documentation-maintenance. Never combine two top-level release controllers.

## Inputs and authority

Read the available draft, project changes/changelog, version, constraints, test records and project rules. Reuse existing tooling. Do not ask for files already in context. If merged history is unavailable, mark unverified claims without guessing. Never install tools or publish without separate authorization.

## Procedure

1. Identify exact release scope, version and source revision from supplied project artifacts.
2. Compare every draft claim against merged changes; identify omissions and unsupported statements.
3. Explain mismatches with links to existing evidence, clearly distinguishing facts and assumptions.
4. If key evidence is inaccessible, stop verification of that claim and request only the missing necessary data.
5. Do not modify or publish release materials without the owner's task-specific approval.

## Output and acceptance

Produce a traceable report with verified entries, omissions, unsupported claims and unknowns. Every verified claim must point to real source evidence. Do not claim unexecuted tests or deployment. Present beginner-friendly explanations or advanced diagnostics as appropriate without weakening the verification criteria.

For larger releases, consult the [conditional review checklist](references/review-checklist.md).
