---
name: product-discovery
description: "Turn a product idea or proposed feature into evidence-labelled hypotheses, an MVP scope, a concise PRD and measurable success criteria. Use for product discovery, MVP planning or PRD requests, not coding bugs or API implementation."
metadata:
  pack: "product"
  version: "1.0.0"
---

# Product Discovery: decide what to build before building it

**Positive triggers:** "Help turn my idea into an MVP"; "Write a PRD for a new product"; "Which product hypotheses should we test?"; "How can we tell whether this feature has value?"

**Negative triggers:** fix a Python/backend bug, add unit tests, implement an agreed feature, design an API contract or deploy software. Route these to existing engineering/QA skills. For ambiguous requests, determine whether the user wants a *product decision* or a *code change*; do not hijack coding tasks.

## Inputs and stop conditions

Read the idea or proposed change, current product/context, intended users, known limitations, available evidence, budget, privacy constraints and permissions. Do not require a methodology vocabulary or GitHub URL. Ask at most one or two **blocking** questions; otherwise proceed with visibly labelled assumptions. Stop a dependent recommendation when risk, missing consent, unavailable evidence or an unapproved irreversible decision would make it unjustified. Do not conduct interviews, collect private user data, invoke paid APIs, edit code or write files without explicit permission.

## Procedure

1. **Frame the problem:** describe the intended user segment, context, job to be done, present workaround, pain and smallest useful outcome. "Everyone" is not an actionable target segment; offer one initial segment marked `ASSUMPTION`.
2. **Mark evidence:** for significant statements record `USER_PROVIDED`, `SOURCE_BACKED` (with citation/date), `OBSERVED` (only actually measured), `ASSUMPTION` or `UNKNOWN`. Never synthesize market size, interviews, financial estimates or a baseline.
3. **Draft falsifiable hypotheses:** segment, problem, proposed change, expected observable outcome, metric, smallest ethical validation method and result that would refute it. Mark untested hypotheses `UNTESTED`.
4. **Cut the MVP:** one primary journey, essential features with inclusion rationale, excluded features, dependencies, risks and revision conditions. Use `must now / later / not needed` rather than fabricated RICE scores. Do not silently require payment, login, cloud, mobile apps or AI APIs.
5. **Write a compact PRD:** use [PRD contract](references/PRD_CONTRACT.json). Every required behavior has an observable acceptance criterion or an explicit unresolved reason. Do not claim PRD is implemented software.
6. **Choose decision metrics:** define formula/unit, observation event or available source, measurement period, baseline, proposed target, actual, data quality and owner if known. Defaults: `BASELINE = UNKNOWN`, `TARGET = PROPOSED`, `ACTUAL = NOT_MEASURED`. Avoid unnecessary personal-data tracking.
7. **Handoff:** pass product goal, MVP bounds, priorities, dependencies, user journeys, business rules, acceptance criteria, constraints and unresolved questions to project/delivery management (#54), business/system analysis (#55) and UX/UI (#56). Do not prematurely generate implementation schedules, complete API schemas or a UI kit.

For detailed decisions and recovery, read [workflow guidance](references/WORKFLOW.md); for a synthetic worked result, read [examples](references/EXAMPLES.md).

## Output contract

Return (a) beginner-friendly summary and next verifiable action, and (b) a structured PRD appropriate to the request: title, context/problem, users, jobs, evidence/assumptions, outcome, MVP inclusions/exclusions, functional requirements, material non-functional constraints, acceptance criteria, metrics, risks/dependencies/open questions, and next action. For a small idea keep it near one or two pages. Separate `IDEA`, `DISCOVERY`, `MVP`, `PRD`, `TECHNICAL DESIGN` and `WORKING SOFTWARE` statuses.

**Storage boundary:** Toolkit (including local copies) is read-only whenever used as guidance for another project. Put user-specific PRDs, research and reports **in chat by default**, in a user-authorized destination in their project only when requested, or in separately approved external storage. Never create `reports/`, `prd/`, `research/` or other user-output directories in Toolkit.

**Verification:** compare the result against [manual acceptance cases](references/MANUAL_ACCEPTANCE.md). Static checks and synthetic examples are not real research, real Codex/Claude skill activation or proof of product-market fit.
