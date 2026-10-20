# Project & Delivery Management: from PRD to verified work

[Русская версия](ru/PROJECT_DELIVERY_MANAGEMENT.md) | [Product Discovery](PRODUCT_DISCOVERY.md) | [Skill catalog](SKILLS_CATALOG.md)

**Product Discovery** asks "what and why?". **Delivery Management** asks "what comes first, what blocks it and what is verified?". **Engineering** implements a task; **QA** assesses actual checks; **Release Safety** checks authorization. This optional skill does not install a manager, track work in a second database, deploy or control agents.

## No terminal needed

In a client that can read Toolkit, say:

> Use https://github.com/MikeMoore1337/ai-development-toolkit to take my current PRD and arrange a short ordered plan with dependencies, risks, acceptance checks and one next action. Do not edit files or create GitHub Issues.

No PRD? Describe your goal in ordinary language. The agent should mark missing information rather than invent decisions. You can use Toolkit by URL alone; if the client cannot access it, supply the relevant SKILL.md text. No GitHub URL for your own project is required.

A beginner gets a small sequence and the definition of done. An expert gets requirement-to-task traceability, typed links, evidence, changes, risk register and handoff. Both get the same permission gates. A synthetic home-expense example with R1-R3 / AC1-AC4 is included in [references](../extensions/management/skills/project-delivery-management/references/EXAMPLES.md).

## Optional installation and verification

The optional `project-delivery-management` profile includes the skill plus existing `task-scoping`, `requirements-traceability` and `quality-gate-assessment` (no second controller). Preview before an explicit install:

```bash
python scripts/skill_manager.py catalog --profile project-delivery-management
python scripts/skill_manager.py install --target /path/to/project --profile project-delivery-management
# Explicit consent after inspecting preview:
python scripts/skill_manager.py install --target /path/to/project --profile project-delivery-management --apply
```

An authorized plan file **outside Toolkit** may be checked offline with `python scripts/validate_delivery_plan.py /path/to/plan.json`. This checks structure, original R/AC references, blockers and cycles, but **not** the authenticity of PR status, CI, merge, approval or deployment evidence. It makes no writes.

## Truthfulness and storage

Prefer existing GitHub Issues and PRs as the source of truth. A closed PR is not proof of merge; a green CI run is not proof of release. If GitHub is unavailable, label the plan a dated snapshot and never claim live sync. For non-GitHub projects, return the plan in chat. Never write another project's plans, reports, temp files or logs into Toolkit or copies of it. Do not create files in the user's project unless specifically requested and authorized. This skill is guidance, not proof of actual AI model activation.

Next: deliver unchanged requirement/AC IDs and unresolved business decisions to Business/System Analysis #55; user journeys and interaction constraints belong to UX/UI #56. Neither is silently solved by this planning skill.
