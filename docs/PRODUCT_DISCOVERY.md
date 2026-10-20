# Product Discovery: from idea to MVP and PRD

[Русская версия](ru/PRODUCT_DISCOVERY.md) | [Skill catalog](SKILLS_CATALOG.md) | [Profiles](CURATED_SKILL_PACKS.md)

Use this when you want to decide **what to build, for whom and how to test its usefulness**, before implementing it. The optional `product-discovery` profile adds a single new specialist skill alongside existing scoping and research guidance. No AI API, payment, account or extra installer is required.

## Start without a terminal

In a client that can read the Toolkit source, write:

> Use https://github.com/MikeMoore1337/ai-development-toolkit to help turn my idea for a household expense journal into a minimal MVP and a short PRD. Do not change code or create files.

The agent should explain the target user/problem, separate facts and assumptions, propose falsifiable hypotheses, list what is included and excluded from MVP, produce testable requirements and meaningful success metrics, and give one next step. If your client cannot read the repository, provide the relevant skill text; do not pretend it activated a skill. For IDE clients, no link to the user's local project is required.

A **PRD** is a document describing a proposed product, **not a working app**, validated demand or authorization to implement anything. Without real studies, a model-created persona and a baseline are hypothetical or unknown. Do not require users to share sensitive data.

## Expert and optional installation

Ask for a hypothesis backlog, product evidence ledger, metric definitions, R-ID/AC-ID traceability and structured handoff for #54 (delivery), #55 (business/system analysis) or #56 (UX/UI). [The canonical skill](../extensions/product/skills/product-discovery/SKILL.md) and its references contain contracts and synthetic examples.

Use the existing manager's read-only preview before any explicit installation:

```bash
python scripts/skill_manager.py catalog --profile product-discovery
python scripts/skill_manager.py install --target /path/to/project --profile product-discovery
```

Installation is **optional**; only `--apply` installs into an explicitly selected user-project folder. Toolkit source is always read-only for someone else's product. By default deliver the PRD in chat; create a report file only at a destination the user authorized. No new folder or report is automatically created in Toolkit.
