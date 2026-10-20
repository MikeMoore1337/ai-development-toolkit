# Start without a terminal

[Русская версия](ru/BEGINNER_START.md) | [Home](../README.md) | [Technical installation](INSTALLATION.md)

**You can begin by talking to an AI client. You do not need Python, Git, a terminal, or knowledge of Agent Skills to explain an idea or review supplied information.** Actually changing a repository, running tests, or putting an app online is a different step and requires appropriate tools, access, and permission.

AI Development Toolkit is a library of reusable task instructions and selected skill profiles. It is **not** an AI app, one-click app builder, hosting service, or a set of permissions. Reading this page does not install or activate its skills. The [canonical beginner workflow](BEGINNER_WORKFLOW.md) governs the conversation; this page tells you **where to start**. For terminology see the [Russian glossary](ru/GLOSSARY.md).

## Already have a local project open in an IDE with Codex?

This is the shortest route for an **existing project**: open its folder in your IDE, give the agent `https://github.com/MikeMoore1337/ai-development-toolkit`, and describe your task. The [agent entry guide](../AGENT_START.md) describes **using guidance without installing Toolkit files into the project**. Analysis and reports default to chat; a requested file needs an external destination. Before source edits, the agent discloses planned paths. No target GitHub URL or terminal commands are needed. Reading guidance does not prove skill activation.

## First four actions

1. **Choose where you want to work** in the [client table](#choose-your-ai-client). If unsure, use ChatGPT or Claude in the browser to discuss your goal first.
2. **Choose one task** among the [five copy-ready requests](#five-requests-to-copy). You do not have to choose a programming language, skill or profile.
3. **Attach only the information needed**: an idea needs a description; an existing app needs accessible files, a repository or a reproducible problem report. Never paste secrets.
4. **Check the actual result**. Ask what was read, changed and tested. A plan or code pasted into chat is not an installed, tested or published application.

If a button or capability described below is not available on your account, **stop at planning** and use the fallback. Do not assume every AI client has identical UI or Agent Skills support.

## Choose your AI client

| Client / mode | Easiest supported start | Can change your app? | Can run tests? | Toolkit skills | Terminal for that route |
| --- | --- | --- | --- | --- | --- |
| [OpenAI Codex](#openai-codex), cloud environment | Open Codex Cloud and select a connected, prepared GitHub project | Yes, in the authorized cloud checkout; local Desktop tasks can work in selected folders | Yes, when tools/dependencies and permission exist | Repository `.agents/skills` is documented for Codex; you must actually provide the skills in that repository/environment | **Not required** for the cloud UI path after environment setup; local managed Toolkit install requires CLI |
| [ChatGPT](#chatgpt), Chat / Work | Start a chat or a permitted Work task, then attach relevant files | Chat can prepare text/files; Work can modify supported accessible sources with connected tools and permissions, not arbitrary local files from web/mobile | Only in an execution-capable mode with tools, not guaranteed in ordinary Chat | Workspace/plugin skills are **not** the same as local Toolkit `SKILL.md`; automatic discovery from this repo is **not established** | **Not required** to discuss or upload; code execution/repository writes depend on tools |
| [Claude Code](#claude-code), Desktop Code / cloud | Open the Code tab, select an existing local project or available cloud session | Yes, within the authorized project/session | Yes, with execution tools and dependencies | Project `.claude/skills` supported; local manager preview/apply is a separate CLI step | **Not required** for a configured Desktop GUI session; installing dependencies/setup may still require commands |
| [Claude](#claude), chat / Projects | Start a chat or Project, upload selected materials | Produces text/artifacts; no automatic access to your local repository | Code execution only when enabled and applicable, not your local project tests by default | Custom skills may be uploaded as a **ZIP through Customize > Skills** when enabled; not the Toolkit managed install | **Not required** for chat or supported UI skill upload; preparing a ZIP may require a separate local step |

These are **documentation-level capabilities**, reviewed **2026-10-20**, not live acceptance results. Feature access depends on plan, account, platform, region, workspace settings and explicit grants. Never treat a missing control as user error. Source links are below each client. No paid API or subscription is required merely to read these guides; some client execution modes have separate plan/access requirements which must be checked in the actual account.

### OpenAI Codex

**Best for:** making real code changes in a GitHub repository or a local project, when coding tools are available.

1. Open [Codex Cloud](https://learn.chatgpt.com/docs/cloud) on web/desktop; connect an authorized GitHub repository if prompted. Create and publish a cloud environment **only after reviewing its proposed setup and access**. An existing published environment is enough. On mobile you can select an existing environment; first-time setup is documented for web/desktop.
2. Select that environment, describe one of the tasks below and set the constraint: *inspect first, do not deploy, charge or publish without approval*. Review the diff and the test output before allowing a commit or PR.
3. **If Toolkit skills are needed**, arrange for the selected skills to exist under the relevant repository's `.agents/skills/<skill-name>/SKILL.md`. Do not assume that opening the Toolkit README installs skills in a different repository. Use the [managed CLI](#optional-local-managed-install) in a supported local coding environment, or have an authorized coding agent propose file changes for review; these are distinct from merely reading the documentation.
4. When blocked without a repository/environment: ask for an MVP specification and a file list, **not** a fictional edited project. Stop if access, environment preparation or test tools are missing.

**Terminal:** optional for a configured Codex Cloud UI route; not optional for personally running the current Toolkit's local `adt.py`. Codex Desktop can operate on selected local folders but requires an installed supported app and local permissions. Account, cloud availability and quotas are controlled by OpenAI; do not promise free execution.

**Official references (checked 2026-10-20):** [Codex Cloud setup](https://learn.chatgpt.com/docs/cloud), [Codex local skill discovery](https://learn.chatgpt.com/docs/build-skills), [ChatGPT/Codex modes](https://help.openai.com/en/articles/20001275). **Unverified here:** actual skill discovery, activation and benefit in a running Codex session.

### ChatGPT

**Best for:** first discussing an idea, studying uploaded material, planning a small app or reviewing code with tools that your selected mode actually provides.

1. Open [ChatGPT](https://chatgpt.com/). Start Chat (text-first) or, if available, Work. Create a Project if you want to keep related chats and uploaded files together; attach only nonsecret materials you may share.
2. Paste one of the requests below. Ask the assistant to report **which tools it actually has**. Regular Chat can discuss and prepare code or downloadable artifacts, but this alone does not change or test your actual repository.
3. If you have an eligible Work mode and have granted access to a repository, connected app or desktop-local folder, request authorized changes there. Work on web/mobile does **not** automatically read files on your computer. Review proposed write actions and tests as evidence.
4. **Toolkit skills:** instructions shared in chat can inform a conversation; neither uploading the README nor having Codex skills installed locally proves ChatGPT Chat has discovered or activated them. ChatGPT workspace Skills and plugins have their **own installation/permission controls**; do not equate them with a Toolkit local copy.

**Fallback:** without Work, repo tools or file-writing access, produce a short specification or files for manual use and label tests `NOT_RUN`. No terminal is needed for this fallback.

**Official references (checked 2026-10-20):** [Using ChatGPT](https://learn.chatgpt.com/docs/use-chatgpt), [Work and Codex](https://help.openai.com/en/articles/20001275), [separate skill distribution paths](https://learn.chatgpt.com/docs/enterprise/skills), [GitHub access limitations](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt-drease). **Unverified:** direct automatic installation/activation of this Toolkit's local skills in ordinary Chat.

### Claude Code

**Best for:** working with existing project code through an authorized coding agent.

1. In [Claude Desktop Code](https://code.claude.com/docs/en/desktop), open the Code tab, choose a local folder/session or a cloud environment offered to your account, and review project trust and permissions. You need an installed Desktop app for its local GUI, but typing into a terminal is not the sole launch path.
2. Describe one task, ask for inspection and a small diff before changes, then review command/test output. Local dependencies and project setup may still require installation or command execution even when the **human** interacts only through the GUI.
3. Toolkit's managed `--layout claude` installs under `.claude/skills/<skill-name>/SKILL.md`. The client documents project-local skills, but a copied folder is only filesystem evidence until you observe discovery and use. A Claude account skill synced from claude.ai is another mechanism; cloud sessions do not inherit unrelated personal local folders.
4. **Fallback:** without Desktop, a project, installation permissions or executable tools, prepare a change proposal or use an authorized coding environment later.

**Official references (checked 2026-10-20):** [Claude Code Desktop](https://code.claude.com/docs/en/desktop), [skills and scope](https://code.claude.com/docs/en/skills). **Unverified:** live discovery or invocation of installed Toolkit skills on this repository; no AI-agent trial was run.

### Claude

**Best for:** brainstorming, reviewing uploaded documents and code, preparing a feature specification or optional use of supported cloud-created artifacts.

1. Open [Claude](https://claude.ai/) chat or a Project and add a minimal description or permitted files. Projects can hold knowledge and instructions; this does not grant access to an unshared local repository.
2. Paste one of the requests below. Ask for a plan or a prepared artifact and for an explicit account of what was **not** modified or executed.
3. **Optional Skills UI:** if your account exposes `Customize > Skills` and code execution/file creation is enabled, Anthropic documents uploading a **ZIP containing a correctly structured skill folder with SKILL.md**. Review the source content and ZIP before upload. This is **not** running Toolkit's managed install and cannot be assumed for every setup. Upload only a minimal, distributable skill you understand, not the entire Toolkit or protected/private sources; check organization restrictions.
4. If skill upload is unavailable, use a short excerpt or the relevant nonsecret guide as conversation context. If you need changes in an actual repository and Claude chat has no authorized write tool, move the task to a properly configured coding environment.

**Official references (checked 2026-10-20):** [Claude Projects](https://support.claude.com/en/articles/9517075-what-are-projects), [using custom skills](https://support.claude.com/en/articles/12512180-use-skills-in-claude), [skill ZIP structure](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills). **Unverified:** that an arbitrary Toolkit skill ZIP was accepted, discovered or invoked in a real Claude account.

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

The next step for [Issue #52](https://github.com/MikeMoore1337/ai-development-toolkit/issues/52) is **independent human testing** of navigation, client selection, copy/paste, blocked paths and recognizing real evidence vs prepared text. The offline cases in this issue cannot measure human comprehension or speed.
