# Start without a terminal

[Русская версия](ru/BEGINNER_START.md) | [Home](../README.md) | [Technical installation](INSTALLATION.md)

**You can begin by talking to an AI client. You do not need Python, Git, a terminal, or knowledge of Agent Skills to explain an idea or review supplied information.** Actually changing a repository, running tests, or putting an app online is a different step and requires appropriate tools, access, and permission.

AI Development Toolkit is a library of reusable task instructions and selected skill profiles. It is **not** an AI app, one-click app builder, hosting service, or a set of permissions. Reading this page does not install or activate its skills. The [canonical beginner workflow](BEGINNER_WORKFLOW.md) governs the conversation; this page tells you **where to start**. For unfamiliar terms, see the [English glossary](GLOSSARY.md) ([Russian version](ru/GLOSSARY.md)).

**Already have a project?** See the short, human-facing [existing project guide](EXISTING_PROJECT.md) for attaching only necessary files and protecting secrets. In ChatGPT or Claude the upload control may look like **+**, a paperclip or **Add files**, and might not be available in every mode. **Regular Chat** discusses shared material; **Work**, if available, is a separate mode for longer tasks using authorized tools. Neither automatically sees files on your computer.

## Your first result in three steps

1. **Say what you want to achieve.** Pick one of the [six task examples](#pick-your-task-first), or simply describe a problem in your own words. No programming language, skill name or profile is required.
2. **Give the AI access only to what it needs.** For a new idea, a description is enough. For an existing project, choose an available [client and access route](#choose-an-access-route), then supply authorized files, a repository or reproduction details. Do not share passwords or tokens.
3. **Check the result, not the promise.** Ask: *What was actually read or changed? Which checks ran and what were their PASS/FAIL results? Which checks are NOT_RUN?* If no project access or execution tool exists, accept an explicit plan or prepared files instead of a claim that the application was fixed or tested.

**One copyable example:** "My Save button stopped working. Use the project files I share to find the cause. Change only what you are authorized to change, and report the actual tests and anything NOT_RUN." A quick outcome is useful even when it is only a diagnosis or a safely blocked next step. For complete acceptance rules, use the [existing beginner workflow](BEGINNER_WORKFLOW.md), not a second checklist.

If a button or capability is unavailable in your account, choose the [documented fallback](#when-something-is-missing); the client does not gain filesystem access or native skill activation merely from this guide.

**Statuses in plain English:** `PASS` — a check actually succeeded; `FAIL` — it actually failed; `NOT_RUN` — it was not executed; `NOT_VERIFIED` — no supporting evidence; `BLOCKED` — an access or permission gate prevents it; `GUIDANCE_ONLY` — instructions were read, not necessarily used. `MCP` connects tools to an AI client; a `profile` groups instructions; `--apply` explicitly writes reviewed changes and is unnecessary for chat. [Existing project example](EXISTING_PROJECT.md).

## Pick your task first

You can copy one request below into any AI client that can read the necessary material. **No skill name, profile selection or terminal is required to start.** These examples do not grant file access, trigger installation or promise that any tests have run.

| What you need | Request to copy | Relevant guide |
| --- | --- | --- |
| **Code** | "Add one small feature to my existing project. Inspect it first; describe what changed and test only what you can actually run." | [Step-by-step workflow](BEGINNER_WORKFLOW.md) |
| **QA** | "Check my project's highest-risk changes, including negative cases. Show the evidence and say which tests were not run." | [Change-aware QA](QA_CHANGE_IMPACT.md) |
| **Design** | "Show distinct visual compositions for my site on desktop and mobile. Ask me to approve an actual mockup before changing the interface." | [UX/UI design](UX_UI_DESIGN.md) |
| **SEO** | "Audit the SEO of my accessible website pages. Separate observed defects from guesses and rank improvements by impact." | [SEO route](PROMPT_AND_SEO_SKILLS.md) |
| **Research** | "Research my question using accessible reliable sources. Distinguish verified facts, uncertainties and recommendations." | [Research guidance](../.agents/skills/research-verification/SKILL.md) |
| **Maintenance** | "Review the current project's documented incidents and risks. Recommend safe next steps without starting automatic updates or monitoring." | [Beginner workflow](BEGINNER_WORKFLOW.md) |

The six rows above are **task categories** for quick selection. The [five worked requests](#five-requests-to-copy) are **longer example scenarios**, not five more requirements or a second installation step. Start with one relevant example; the [full skills catalog](SKILLS_CATALOG.md) is optional reference material, **not a prerequisite**.

## Choose an access route

Pick **one** route based on your actual tools and permission; none is more important than another. Toolkit provides reusable guidance, not a hidden model, independent host or additional access rights.

| Route | Where to start | What is (and is not) confirmed |
| --- | --- | --- |
| **Chat without installation** | Describe the task in ChatGPT or Claude and provide accessible source material; see [conversation workflow](BEGINNER_WORKFLOW.md). | Text guidance is possible. Access to a URL or attached files must be checked; no skills are installed simply by pasting a link. |
| **Installed ChatGPT plugin** | Open the *separately installed* Toolkit plugin and describe the task; see [plugin source contract](../AGENT_START.md). | Available only where the plugin is actually connected. A GitHub source refresh is not a plugin binary update or proof of skill activation. |
| **Toolkit MCP for Codex or Claude Code** | Read the [MCP installation/doctor instructions](MCP_INSTALL.md), preview project configuration and explicitly authorize `--apply` if appropriate. | Read-only MCP tools can suggest relevant skills/roles; configuration is not evidence that the client discovered or used them. |
| **Local managed skills for Codex or Claude Code** | Read the [project adoption preflight](PROJECT_ADOPTION_PREFLIGHT.md) and review a [local install plan](INSTALLATION.md) before any explicit `--apply`. | Filesystem installation is separate from client discovery and actual skill use. Existing project rules and user-owned skills take precedence. |

**Quick choice:** no setup or only a question - use chat. Already using the Toolkit plugin - choose the plugin. Need read-only guidance in your IDE - use MCP. Need actual skill files managed inside a project - use Skill Manager after preview and permission. These are alternatives, **not four consecutive setup steps**.

**Evidence boundary:** a guide was read, a connection was configured, the client discovered a skill, the skill was used and the application was tested are *different observations*. Client discovery/use and benefit are **NOT_TESTED** until actual client evidence exists. Deployment, paid services or external actions are never implied by any route.

## Want a new design but don't know how to prompt?

You can simply say: **"I want a beautiful fitness club website."** With access to Toolkit instructions, Codex should recognize design intent, inspect your open project if accessible and select the UX/UI Design Orchestra `create-design` path itself. You do not need to know skill names, page structure or UX terminology. It may ask up to two essential questions. Otherwise, it states its assumptions and creates three genuinely different low-fidelity sketches for comparison. After reviewing those sketches, it prepares detailed desktop and mobile previews of the selected direction. Sketches and mockups count as created only if appropriate tools actually render them; without visual tools, the agent reports that visual comparison was not performed and provides a text plan. Existing site code is not changed until you approve the actual visual direction. [Design guide](UX_UI_DESIGN.md).

## Already have a local project open in an IDE with Codex?

The shortest route: open your project in the IDE and ask "Use https://github.com/MikeMoore1337/ai-development-toolkit to add tests to my current project." No special prompt, installation or target repo URL is required. The [agent guide](../AGENT_START.md) makes the boundary clear: Toolkit is **read-only guidance**; requested code, tests and reports go to the user's project, chat or another authorized location. **Other users' results never belong in Toolkit.**

## Choose your AI client

**Choose just one available route.** Chat analyzes supplied content; Codex and Claude Code may change code only with real workspace access and permission. Advanced comparison tables, official references and limitations are in the [client reference](BEGINNER_CLIENT_DETAILS.md).

| Where you want to work | Simplest start |
| --- | --- |
| **ChatGPT or Claude, regular chat** | Attach permitted files via **+** or the paperclip where supported; otherwise paste relevant excerpts |
| **ChatGPT Work** | **Work** is a separate multi-step working mode with available tools and connected apps, not a synonym for regular Chat; check availability in your account |
| **Codex or Claude Code** | Open the correct project and provide the Toolkit instructions; verify that the client can actually read the project files and has permission |

A pasted Toolkit link does not grant project access or install skills. If a client capability is missing, supply authorized attachments/excerpts or start with the [existing project guide](EXISTING_PROJECT.md). **Guidance read, file installation, skill discovery and tested fixes are separate evidence levels.**

## Five requests to copy

Copy **one** request into your selected client. You do not need to know a skill name. The detailed [seven-stage conversation workflow](BEGINNER_WORKFLOW.md) remains the source of engineering rules.

### A. I want an app

```text
I want to make a small app but cannot code. Help me define the smallest useful version, explain it plainly, and perform only the actions your tools and my permissions allow. Do not buy services or deploy without asking. Tell me how to open the result and what you actually tested.
```

**Goal:** idea -> MVP -> minimal implementation -> permitted verification. **Input:** the idea and who will use it. **Result:** a small runnable change with evidence *only if* a coding environment exists, otherwise a clear specification/prepared files. **Limit:** no automatic production or payment. **Check:** one main action, a failing-input case and real open/run instructions; `NOT_RUN` without execution. **Blocked:** first write a one-page MVP with acceptance criteria.

### B. Check my project

```text
Check my project and explain in plain language what is ready and what needs work. Identify real, evidence-backed issues, separate blockers from minor improvements, and suggest the order. Make no changes without my permission. If you cannot access the project, say which files you need.
```

**Goal:** inspect -> evidence -> severity -> priorities. **Input:** authorized repository/files or a minimal archive. **Result:** a grounded audit, not guessed issues. **Limit:** no file edits by default. **Check:** each important finding cites an accessible file, path or test; unknowns stay unknown. **Blocked:** ask for the smallest useful artifact, such as README and failing log.

### C. Fix a bug

```text
A feature in my app stopped working. First ask what I expected and what actually happens, inspect the accessible project, and reproduce the failure if your tools allow. Fix only the confirmed cause with minimal changes and run the available regression checks. Explain what you could not verify.
```

**Goal:** expected/actual -> reproduction -> root cause -> narrow fix -> regression. **Input:** steps, error/log and permitted project files. **Result:** verified fix *only if* edits and checks actually occurred, otherwise diagnosis or patch proposal. **Limit:** never say fixed based on text alone. **Check:** reproduction before/after plus nearby regression, recording statuses. **Blocked:** request reproduction steps or a relevant log.

### D. Add a feature

```text
I want to add one feature to my existing app. Inspect the current implementation, define a small testable behavior, explain the minimal change, and only then make permitted edits and run tests. Report the files changed and the evidence. Do not start multiple feature controllers.
```

**Goal:** existing code -> requirement -> acceptance -> implementation -> checks. **Input:** authorized project and behavior description. **Result:** reviewed diff/test report or implementation plan. **Limit:** choose at most one of feature-delivery or Make Feature for an orchestrated task. **Check:** feature criterion plus unaffected neighboring behavior. **Blocked:** write two acceptance examples before any code.

### E. Maintain my app

```text
Help me maintain my existing app: inspect accessible information, identify confirmed problems, group risks by priority and suggest a safe maintenance plan. Do not start monitoring, automatic changes, upgrades or paid services without my explicit approval. Clearly state what you cannot observe.
```

**Goal:** inventory -> current state -> risks -> maintenance plan. **Input:** permitted docs/code, known incidents, dependencies. **Result:** prioritized plan and optional checks. **Limit:** no claim of continuous monitoring without a real configured mechanism. **Check:** each risk has supporting evidence, owner and a verifiable next step. **Blocked:** request a current project snapshot or issue list.

## When something is missing

| Situation | Safe outcome and one next step |
| --- | --- |
| AI client cannot run commands | Do not report tests as passed; prepare reproducible commands for a later authorized environment |
| Project/files not provided | No invented audit; request the smallest relevant README, source or log |
| ChatGPT is expected to auto-load local Codex skills | Explain separate skill mechanisms; do not report activation |
| Publishing requested without approval | Stop; request explicit owner consent and a reviewed target |
| Paid feature unavailable | Use text-only planning; do not purchase or silently upgrade |
| No terminal available | Use chat/UI planning; do not claim the local manager installed anything |
| Code generated but not tested | Report `NOT_RUN` and provide an executable verification path |
| Client has no repository permission | Request specific authorization or a safe minimal archive |
| Unsupported skill directory | Use the documented client mechanism or plain-text guidance |
| Existing unmanaged skills collide | Stop; preserve user files and inspect ownership, without forced overwrite |
| Continuous maintenance requested without scheduler | Prepare a checklist only; never claim ongoing monitoring |

## Permissions and stopping safely

| Level | Typical actions | What to do |
| --- | --- | --- |
| Read-only | Read documentation, choose a request, discuss a plan, inspect accessible information | Start now; do not reveal secrets |
| Authorized project change | Create/edit files, install a skill profile or dependencies, run commands affecting a project | Confirm target, preview/diff and permission before applying |
| High risk | Delete data, irreversible migration, publish code, production deploy, incur charges, share private material with external parties | **Stop and request explicit approval** under project/owner policy; no shortcuts |

**Four separate evidence claims:** (1) *Toolkit files prepared* - installation/copy inspected; (2) *client discovered a skill* - observed in that exact client; (3) *skill used* - observed invocation in the actual task; (4) *app works* - relevant behavior tested. None implies the next. In this Issue, offline documentation/contract checks may pass, but client discovery **NOT_TESTED**, skill use **NOT_TESTED**, benefit **NOT_MEASURED**, independent novice usability **NOT_TESTED**.

If you only have a phone/browser, cannot install software, cannot share project files, cannot run tests, or lack permission to edit: **stop at an honest plan, prepared code or a report**. Do not ask the assistant to fabricate command results or bypass owner protections. If a check fails, preserve files and logs, review the diff, and choose the smallest reversible next step.

## Optional local managed install

**Only if** you have Python 3.12+, a checkout of Toolkit, an existing trusted target folder and access to run commands. In the Toolkit repository:

```bash
python scripts/adt.py profile list
python scripts/adt.py doctor --target /path/to/project
python scripts/adt.py profile plan --target /path/to/project --task qa
python scripts/adt.py init --target /path/to/project --profile general
# Only after reviewing the preview and getting permission:
python scripts/adt.py init --target /path/to/project --profile general --apply
python scripts/adt.py status --target /path/to/project
```

For Claude Code, add `--layout claude` to the applicable target commands; Windows may use `py -3` and a Windows path. The manager refuses unmanaged skill collisions, and a successful `status` **does not** prove agent activation. See [Installation](INSTALLATION.md), [migration/recovery](CLIENT_MIGRATION.md) and [client filesystem contracts](CLIENT_COMPATIBILITY.md). It is fine to use Toolkit's ideas without installing a skill, but that is **guidance-only**, not a managed or automatically activated Toolkit integration.

Two owner-submitted accounts of the three beginner tasks identified navigation friction; the resulting edits are tracked in [Issue #333](https://github.com/MikeMoore1337/ai-development-toolkit/issues/333). User reports and live client checks are **different types of evidence**. Offline tests cannot measure a person's speed or independence and do not replace future usability observation.
