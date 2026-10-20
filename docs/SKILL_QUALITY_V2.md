# Toolkit Skill Quality v2 (Issue #43)

[Русская версия](ru/SKILL_QUALITY_V2.md)

Toolkit Skill Quality v2 is an **internal quality standard**, not a revision of the official [Agent Skills specification](AGENT_SKILLS_SPEC.md). The pinned official reference validator remains authoritative for upstream format checking. This contract applies to **new or substantially revised skills**. Existing skills are valid without adding uniform new headings. Reuse the [offline metrics](SKILL_QUALITY_METRICS.md), [existing workflow exclusions](QUALITY_RULES.json), [client contracts](CLIENT_COMPATIBILITY.md), and [provenance rules](PROVENANCE_AUDIT.md) rather than creating competing validators or managers.

## Purpose, activation and boundaries

Every skill should describe a **specific repeated task**, positive triggers, negative triggers (when **not** to use it), related/composable skills and any conflicting top-level workflow. Avoid frontmatter descriptions that imply activation for every engineering request. The portable YAML description should be short and task-specific. Keep conditional details inside the body and references. Trigger quality requires semantic review or a real agent trial; a keyword-based scanner cannot prove correct skill selection.

Start from the [positive SKILL.md example](../templates/skill-quality-v2/example-skill/SKILL.md). When copying it, rename both the directory and the YAML name to the chosen skill ID. See also the [negative anti-pattern sample](SKILL_QUALITY_V2_ANTI_PATTERNS.md). These are authoring resources, not additional manifest skills and are not auto-installed.

## Quality contract and manual checklist

| Area | What reviewers must confirm | Acceptance evidence |
| --- | --- | --- |
| Scope | Clear problem, task boundary, positive and negative activation cases, distinction from neighboring skills | Example positive and negative requests |
| Inputs | Task goal, project context, constraints, existing artifacts, available permissions/tools, missing inputs and assumptions | One complete and one incomplete input case |
| Procedure | Reuse-first inspection, actionable steps, decisions, alternatives, recovery, stop conditions | Worked example and actual commands when available |
| Result | Concrete deliverable: code, tests, diagnosis, document or recommendation | Observable artifacts and objective acceptance oracle |
| Safety | Owner instructions, least privilege, secret handling, untrusted sources, no unapproved installs or production operations, approval for irreversible changes | Negative authorization scenario and manual security review |
| Portability | Explicit optional client/platform/tool assumptions rather than silent dependencies | Source compatibility contract; real trial where available |
| Context | Short SKILL.md, references loaded as needed, helper scripts only when justified | Reviewer checks that detail is conditional and not filler |
| Provenance | Reuse rights and citations to external origins where relevant | Existing provenance workflow, not an inferred license |

The agent must **not ask for information already present in context**. When information is insufficient, distinguish safe assumptions from blocking questions and stop before inventing authority. Do not report a proposed modification as completed, a local result as deployed, or an offline compatibility check as real client execution.

For beginners, explain the impact of decisions using plain language and one actionable next step. For experts, give relevant technical alternatives, trade-offs, commands and boundary conditions. Acceptance and safety requirements do **not** change based on skill level. Users should not be required to manually choose dozens of skills; use existing task profiles/recommendations without claiming that a static selector truly understands task intent.

Prefer progressive disclosure: concise SKILL.md, task-specific resources in references/, deterministic scripts/ only if needed. No arbitrary common file-size quota. Review redundant instructions that merely repeat basic model behavior, universal safety text, unrelated generic advice, or functionality already provided by another skill.

## Positive/negative activation worksheet

For each new or materially revised skill, write at least two positive task prompts, two negative nearby prompts, and an ambiguous edge case where relevant. For each case record: expected selected skill, exclusion rationale, available inputs, actual client/version if tested, observed activation if tested, and missed/spurious activation. Without a real client run, **observed activation = NOT_MEASURED** even if the source description appears correct.

## Evidence levels

The levels are **separate, staged observations**, not a numerical score or inferred guarantee. Record the source commit, client/environment when applicable, method and limitations. Supported statuses are PASS, FAIL, NOT_MEASURED and NOT_APPLICABLE. A missing test is **NOT_MEASURED**, not PASS; a failure must have an explanation; NOT_APPLICABLE requires a scoped reason.

| Level | Positive verification | What it cannot prove |
| --- | --- | --- |
| Source validated | Local Toolkit frontmatter, links, inventory and conflicts; independently pinned official skills-ref in CI | Packaging, installation or model behavior |
| Packaged | Verified reproducible archive with manifest and hashes | Installation |
| Installed | Actual copy/install into a specified versioned client environment | Client discovery |
| Discovered | Real client recognizes a registered skill (sanitized client log/UI) | Skill use |
| Activated | Real task trace shows the skill selected/read and applied | Correctness or effect |
| Effective | Independent acceptance oracle and baseline-vs-skill comparison including regressions and unsafe actions | Future success on every task |

Offline skill_quality_metrics.py reports PASS or FAIL for *local* source validation and leaves the separately executed official skills-ref result as NOT_MEASURED **inside its own report**. It leaves Packaged, Installed, Discovered, Activated and Effective as NOT_MEASURED. Deterministic repetition of static metrics does not change these values. A passing simulated installation or source client compatibility contract must not be promoted to client discovery. Live trials remain gated by [Issue #11 evaluation policy](SKILL_EVALS.md).

## Optional machine-readable evidence declarations

No evidence declaration is required for existing skills. After owner-reviewed trials, optionally add a sanitized record in quality/evidence/ named exactly after the skill ID with a .json extension. The [example](SKILL_QUALITY_V2_EXAMPLE.json) explicitly declares all levels NOT_MEASURED and uses a synthetic revision; it **does not** attest any real test.

The evidence record must contain schema_version (1), skill_id matching the manifest and filename, a full 40-hex source_revision, and an exact six-key levels mapping. PASS requires a method, at least one existing repository-relative SHA256-pinned artifact and PASS at each preceding level. Runtime PASS requires environment, reviewed_by and UTC observed_at. Discovery and higher require a known client_id from compatibility/clients.json. Effective requires a comparison object describing baseline vs candidate. FAIL needs reason. NOT_APPLICABLE is reserved for runtime levels and requires reason. NOT_MEASURED accepts only status.

The existing validate_quality.py checks records and artifact integrity as **EVIDENCE001**, rejects unknown clients, hash mismatches, unsafe paths, missing evidence and fake stage promotion. It does **not** validate the authenticity of logs or reviewer independence. An invented text file matching its hash cannot establish a real test. Real client and model assessments must be independently reviewed, using de-identified evidence with no credentials, secrets or private transcripts. Evidence declarations and static per-skill metrics remain separate to preserve the source metrics schema and baseline comparability.

## Migration, CI and next tasks

1. New skills use the template, positive/negative worksheet, output oracle, reuse-first checks and approval boundaries.
2. Existing local validator and pinned official skills-ref check format; the quality gate checks links and optional declarations; source metrics report static-only values.
3. Review semantic trigger boundaries, capability overlap, permission risks and actual output criteria manually; do not infer semantics by searching for headings/phrases.
4. Existing catalog semantic inventory belongs to #44, Core/QA refactoring to #45, Frontend/Backend/Fullstack to #46, documentation/versioning to #47 and expanded CI to #48. Do not mass-update old or protected QA/Make Feature materials here.

The existing CI matrix covers Ubuntu Python 3.12/3.13 and Windows Python 3.14, including checksum/provenance checks and the pinned upstream CLI where configured. No new dependency or live agent/API call is introduced. Without real trials, empirical quality, actual model token cost and agent effectiveness remain NOT_MEASURED.

## Issue #45 - manual semantic acceptance cases

These are **expected behaviors** for future client testing, not proof of actual Codex/Claude activation. Real agent discovery, selection and effectiveness remain **NOT_MEASURED**. Corresponding static checks are in `tests/test_skill_quality_v2.py`.

| Skill | Positive scenarios - expected activation | Negative scenarios - expected exclusion | Required evidence |
| --- | --- | --- | --- |
| API Testing | HTTP success + read-back; documented negative HTTP 404/403; asynchronous event only when present | UI styling; mark unobserved event PASS | Actual response, state and optional event outcomes separated; no hidden skipped check |
| Test Strategy | Small service without full E2E; multi-service boundaries; limited test budget | Run one known test; invent business-critical flows from no inputs | Selected/omitted layers, assumptions vs confirmed data, untested risk and revisit point |
| Make Feature | Independent review available; delegation unavailable; local tests without review | Self-review presented as independent PASS; high-risk change without required review; delegation limit reset | Client capabilities, real reviewer identity when available, incomplete C*, budgets and stopped high-risk steps |
| Clear Voice | Edit user prose; write UI microcopy | Fix Python; validate SQL; edit structured JSON | Original writing modes intact, no false technical trigger; legal-document edits don't certify legal correctness |

A missing review agent may still allow reversible work with explicit `DONE_WITHOUT_INDEPENDENT_REVIEW` only when independent review is not mandatory; required review remains `INDEPENDENT_REVIEW_PENDING`. Tests of code/document strings are not behavioral AI-client evaluations. Do not claim model activation PASS from these fixtures.
