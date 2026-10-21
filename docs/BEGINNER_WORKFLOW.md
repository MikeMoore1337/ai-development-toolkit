# From an idea to a first verified result

[Русская версия](ru/BEGINNER_WORKFLOW.md)

**Start here if you do not code.** Describe what you want in ordinary language. You do not need to choose Python, a database, a frontend, a skill name or a role first. The AI client can explain and plan; changing files, running commands and publishing depend on the client's actual tools and your permissions.

This is one **conversation contract**, not an installer, autonomous agent, extra skill, CLI or guarantee of execution. Existing [task-scoping](../.agents/skills/task-scoping/SKILL.md), [feature-delivery](../.agents/skills/feature-delivery/SKILL.md), [minimal-safe-change](../.agents/skills/minimal-safe-change/SKILL.md), [implementation](../.agents/skills/implementation/SKILL.md), and [QA strategy](../.agents/skills/qa-strategy/SKILL.md) remain the engineering sources. Select one feature controller if needed; never stack `feature-delivery` and `make-feature` by default.

## Three people this route serves

| Person | Goal and starting point | Minimal input | Typical confusion or mistake | Safe finish condition |
| --- | --- | --- | --- | --- |
| A. Idea owner | Has an idea, no programming knowledge; wants a useful first version | One user, one problem, one desired outcome | Asking for login, cloud, payment or microservices before a local prototype | One basic action works and its actual verification is recorded, or an honest plan if execution is unavailable |
| B. Existing app owner | Reports a broken Save button without knowing the code | Expected vs observed result, access to app or relevant files/logs | Guessing a root cause or rewriting unrelated code | Reproduced cause and narrow regression-checked fix, or a clearly blocked diagnosis |
| C. Toolkit adopter | Has a project and Codex but does not understand profiles or skills | Client name, target folder, permission to inspect the project | Equating copied skill files with live activation, or overwriting unmanaged files | Preview reviewed, permitted installation status checked, activation still separately unmeasured |

## Agent instructions: the seven-stage route

1. **Understand.** Identify the user's goal from existing context. Ask **one blocking question only** when the next safe action genuinely cannot proceed (for a defect, missing project/artifact may be blocking). Otherwise state a small, reversible assumption.
2. **Scope.** For a new app identify user, primary action, data, smallest demonstrable feature, exclusions, and acceptance criteria. For a bug record expected/actual behavior, reproduction and boundary. For adoption identify client, project, layout and potential conflicts.
3. **Explain.** In plain language, say what the first result will do and why this is the least complex reasonable option. Do not force the user to choose a programming language, database, API or profile. For expert users also give significant alternatives, interfaces and trade-offs when material. Keep the **same** security, verification and approval gates.
4. **Act within actual capability.** Distinguish: (a) authorized read/write/command tools available, (b) files can only be prepared, (c) a change or external effect awaits approval, (d) the client cannot perform the action. Do not claim a feature exists when only a draft or steps exist. Inspect existing project instructions and other people's work before modifying anything.
5. **Verify.** Use the strongest feasible check for the changed behavior: syntax, unit, contract/API, integration, UI, manual or end-user scenario. Report each **PASS** only with an executed check and reproducible evidence; use **FAIL**, **NOT_RUN**, **BLOCKED** or **NOT_APPLICABLE** accurately. Static file validation is **not** proof of runtime behavior; one's own review is **not** independent acceptance.
6. **Report.** State in this order: outcome, where to open it, what actually changed, check name/status/evidence, what could not be checked, significant risks and the single useful next action. For an expert append diff/commit, commands and acceptance evidence when available.
7. **Next.** Request explicit approval before publishing, deployments, purchases, deletion, overwriting others' files, or actions restricted by repository policies. If blocked, preserve progress and give one safe, actionable next step.

**Action vocabulary:** `EXPLAIN` (discussion only), `PREPARE` (draft without modifying target), `READ` (authorized inspection), `CHANGE` (authorized file edits), `EXECUTE` (permitted command/test), `EXTERNAL` (publish, deploy, paid service or third-party changes, explicit gate). Never treat a previous discussion or copied file as blanket authorization for an `EXTERNAL` action.

## A. Create a tiny home-tasks application

> I have never programmed. Please help me make a simple list of household tasks. Explain the smallest useful version in plain language and only perform actions for which you actually have tools and permission. Run the checks you can, and say clearly which ones were not run.

**Example scope:** One person can add a task, see it and mark it complete; tasks persist locally after reopening. No account, server, payments, cloud sync or paid service in version one. Ask about persistence only if a decision blocks an available implementation; a simple local browser application is a *candidate*, not a mandatory stack.

**Acceptance:** A1 - adding “Buy milk” makes it appear once in the list. A2 - marking it complete changes its state and remains correct after reopening. A3 - an empty task cannot be saved. A4 - the agent supplies run/open steps and the exact verification results. If there is no writable coding environment, provide a small implementation plan or preparable files; label A1-A3 **NOT_RUN**, not PASS.

**Agent routing:** `task-scoping` -> `feature-delivery` (only if implementation is possible and appropriate) -> `implementation` / `qa-strategy`. Prefer existing application conventions over introducing a new framework. A working local file is not a deployed product.

## B. Repair a broken Save button

> After the last update, Save no longer works. Inspect the available project and try to reproduce the problem before editing. Fix only the verified cause, test the saving scenario and explain what remains uncertain.

**Example scope:** Determine which screen, what ought to be saved, actual error and reproducible steps; check logs and code only where access was granted. If files or a running app are missing, ask for the smallest blocking artifact, not for guessed technology details.

**Acceptance:** B1 - document expected/observed behavior and reproduction evidence. B2 - where verified, change the smallest cause rather than unrelated modules. B3 - the Save scenario and one neighboring regression have recorded outcomes. Without diagnostic access, cause is **UNCONFIRMED**, fix **NOT_DONE**, tests **BLOCKED**; never invent a successful reproduction or fix.

**Agent routing:** `task-scoping` -> `minimal-safe-change` -> `implementation` and `qa-strategy` as appropriate. If the problem risks data loss, ask before destructive experiments or migrations.

## C. Connect Toolkit to an existing Codex project

> I have a project and Codex. Help me choose a minimal Toolkit profile. Before changing anything, check the installation method and show me a preview. Do not overwrite unmanaged skills, and separately explain how to verify that Codex actually used a skill.

**Example scope:** Identify the *real* client and selected target directory. For a generic first pass, the existing `general` profile is an option, not a command to automatically install. Check the target's `AGENTS.md`, installed skills and permissions; follow the [installation guide](INSTALLATION.md) and [Russian first-run walkthrough](ru/GETTING_STARTED.md). The latter uses a disposable folder, not the user's project.

**Acceptance:** C1 - the proposed profile is explained in ordinary words and references real existing skills. C2 - the existing `skill_manager.py install` preview is reviewed **before** any `--apply`. C3 - collisions, ownership and rollback are respected. C4 - post-apply `status` and copied files are reported separately from **NOT_TESTED** live client discovery or **NOT_MEASURED** effectiveness. If no filesystem/terminal is accessible, provide instructions without saying installation occurred.

**Safe command shape (example; review target first):**
```bash
python scripts/skill_manager.py catalog
python scripts/skill_manager.py install --target /path/to/disposable-project --profile general
# Only after reviewing the preview and receiving permission:
python scripts/skill_manager.py install --target /path/to/disposable-project --profile general --apply
python scripts/skill_manager.py status --target /path/to/disposable-project
```
For Claude Code use the documented `--layout claude`. Hermes has source-contract documentation but **no supported Toolkit manager integration**; do not silently install into it.

## Capability and evidence boundaries

| Client/environment | Talk and scope | Read/change files and execute tests | Skills discovery |
| --- | --- | --- | --- |
| Chat-only conversation | Yes | **Not assumed**; only if explicitly connected tools actually permit it | **NOT_TESTED** |
| Codex, Claude Code | Yes | Conditional on installed client, runtime, trust, permissions and project context; managed layouts have offline filesystem tests | Actual discovery **NOT_TESTED**, activation **NOT_TESTED** |
| Hermes Agent | Yes when agent available | Runtime/trust/configuration dependent; Toolkit manager integration **UNSUPPORTED** | Actual discovery **NOT_TESTED** |

Detailed, evidence-scoped [client matrix](CLIENT_COMPATIBILITY.md) and [registry](../compatibility/clients.json) take precedence over generic marketing promises. Official documentation, offline filesystem checks, actual activation and human usability are different kinds of evidence. Do not claim an unsupported client action was performed.

## When something goes wrong

| Condition | Honest explanation and next step | Must not claim |
| --- | --- | --- |
| No project or required bug artifact | Ask for a link/file or reproduction detail that is actually blocking | Diagnosis or file fix |
| No filesystem or terminal | Offer a draft or manually executable next step | Code was written or tests were run |
| Unsupported client/layout | Cite supported layouts; show manual guidance without installing | Compatibility or activation |
| Vague goal | Propose one reversible MVP assumption; ask only if safety depends on answer | A certain specification |
| Unmanaged skill collision or ownership lock | Stop; inspect owner and backup options; never overwrite by force | Successful installation |
| No test environment or failing tests | Mark BLOCKED/FAIL and preserve observations; give a concrete retry | PASS |
| No independent reviewer | Mark independent acceptance NOT_TESTED | Independent review |
| Publish or pay without approval | Stop and request action-specific consent; zero-spend by default | Published, charged or deployed |

## Example of an honest handoff (illustrative, NOT actual test evidence)

**Outcome:** A small task-list implementation was *prepared as a draft only*. **Where:** draft files (not deployed). **Applied changes:** none. **Checks:** syntax NOT_RUN; main user scenario NOT_RUN; independent review NOT_TESTED. **Next action:** open the draft in an authorized coding runtime, then test add/complete/reopen. A text plan is not working software.

The machine-readable [acceptance and negative cases](../fixtures/beginner_journeys.json) are deterministic documentation contracts. Their offline test verifies **schema, references, state constraints and forbidden claim combinations**. It cannot establish model adherence, actual app behavior, client skill activation or user comprehension.

## Scope and follow-up

- **#49:** this conversation contract, personas, acceptance examples, honest outcomes, deterministic offline regressions.
- **#50:** CLI init/doctor/profile plan - not implemented here.
- **#51:** start without terminal and OS-specific onboarding - not implemented here.
- **#52:** real novice usability sessions with pre-defined tasks, observable success/failure, time/effort and misunderstanding notes - **NOT_TESTED** here.
- **#11:** independently gated live AI-client activation/effectiveness - **NOT_MEASURED** here.

**Expert content review checklist:** scope and exclusions clear; jargon not required; real client capability conditional; action/approval boundary explicit; negative cases stop unsafe claims; no paid dependency; acceptance outcome tied to evidence. This checklist permits expert review but is *not* evidence that an independent human performed it.

## End-to-end delivery

For a continuous idea-to-support contract, resumable handoffs and honest evidence levels, see [End-to-end workflow](END_TO_END_WORKFLOW.md). This does not add a new controller or require a terminal.

## Use Toolkit in ChatGPT or Claude.ai without installation

Open a chat and say: "Use https://github.com/MikeMoore1337/ai-development-toolkit for this task." If you have a project ZIP, attach **the project ZIP** separately and describe the goal; no GitHub URL for your own project is needed. The client must first establish whether it can actually read the Toolkit and the attachment. If not, ask for only the necessary source files or give a clearly labeled draft. Nothing is installed merely by sharing the URL; generated reports stay in chat by default. Native hosted Skills, where available, are optional and independent from this no-install workflow. See [the client guide](CLIENT_CAPABILITIES.md).
