---
name: end-to-end-feature-design
description: "Use when designing a user-visible vertical feature across interface, API and data without assuming implementation."
---

# End-to-end feature design

**Use for:** "Design authentication for an app", a feature blueprint or acceptance planning. **Do not use for:** debugging an existing defect, a single isolated API change or replacing an implementation workflow controller.

**Inputs:** user outcome, actors/permissions, current project architecture, known contracts, constraints, exclusions and desired deliverable. Inspect the actual project and approval gates.

1. Define the user goal, scope, roles, edge cases and success/negative acceptance examples; state assumptions that need confirmation.
2. Draw a minimal vertical slice: UI -> API -> backend logic -> persisted data -> response/event -> UI, naming responsibility and data at each seam.
3. Specify contract shape, source of truth, loading/empty/error/unauthorized/conflict/recovery states, compatibility and release dependencies.
4. Link each acceptance criterion to an observable test or review artifact; separate evidence already collected from proposed verification.
5. **Design-only request:** deliver the blueprint and handoff directly. Do not start or require a delivery controller and do not claim code was implemented.
6. **Implementation request:** use the implementation controller already chosen by the project/user, either feature-delivery OR make-feature, never both (WF001 in docs/QUALITY_RULES.json). If none is present, explain the optional choice and existing tool/profile route before implementation. Do not auto-install a controller or create another orchestrator.

**Output:** component/ownership map, cross-layer contract table, error/recovery paths, acceptance-to-evidence matrix, decisions and implementation handoff; clearly label DESIGN ONLY vs IMPLEMENTATION results.

See [design handoff and acceptance scenarios](references/design-handoff.md). Execution, merge, deploy and third-party operations remain subject to owner approval.
