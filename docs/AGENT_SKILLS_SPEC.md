# Agent Skills specification contract

Authoritative sources:
- https://github.com/agentskills/agentskills
- https://agentskills.io/specification

As reviewed on 2026-10-17:

- Each skill lives in a folder with `SKILL.md`.
- YAML frontmatter requires `name` (same as directory) and `description`.
- Allowed optional top-level fields: `license`, `compatibility`, `metadata`, and experimental `allowed-tools`.
- Name: <=64 characters, lowercase alphanumeric Unicode/hyphens, no edge or double hyphens; description <=1024 characters; compatibility <=500 characters.
- Metadata map must consist of string keys and string values.
- Prefer progressive disclosure: small `SKILL.md`, `references/`, `scripts/` and `assets/` loaded only when needed.

Run local checks:

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate_pack.py
python -m unittest discover -s tests -v
```

For independent upstream validation, install **the official skills-ref** separately and run all skills using:

```bash
python scripts/validate_with_skills_ref.py --scope all
```

Or run, for each installed skill:

```bash
skills-ref validate .agents/skills/feature-delivery
skills-ref validate .agents/skills/skill-portability
```

**Limits:** This pack only executed its own PyYAML-based validator, not the upstream CLI. Validation checks metadata format, not whether scripts are safe, features correct, license permits redistribution or client supports a particular activation mechanism.
