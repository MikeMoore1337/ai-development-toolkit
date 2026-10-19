# Fullstack design and delivery handoff

**Design-only example:** "Design authentication for a web application." Deliver an actor map, login/session lifecycle, backend permission enforcement boundary, storage/schema requirements, UI loading/error/unauthorized states, migration constraints and a testable acceptance map. Status = DESIGN ONLY; no controller, code change or deployment presumed.

**Implementation example:** "Add authentication to my application." First inspect the installed workflow/profile and repository instructions. Use the user's already selected feature-delivery or make-feature for orchestration. If neither exists, explain that a controller may be selected through the existing profile/skill manager or continue only within explicitly authorized narrow work. Never combine both controllers; never treat this design skill as a controller.

| Acceptance criterion | Required evidence | Current synthetic example status |
| --- | --- | --- |
| Signed-in user loads own profile | backend response + UI update | NOT_MEASURED |
| Anonymous request cannot read profile | 401 and no data returned | NOT_MEASURED |
| Other user's/tenant's record cannot be accessed | 403/404 plus no data side effect | NOT_MEASURED |
| Expired session returns to safe state | server enforcement + UI recovery | NOT_MEASURED |
| Existing client remains compatible | old/new contract fixtures | NOT_MEASURED |
| Failed write does not show saved state | rollback/conflict reproduction | NOT_MEASURED |

**Negative cases:** design-only should never force installation or run a controller; implementation must not select both; unavailable implementation authority means a design/handoff can still be delivered, not a false implementation PASS.

**Limits:** Acceptance rows are scenario specifications, not executed agent trials; use actual project contracts, not assumed authentication mechanisms.
