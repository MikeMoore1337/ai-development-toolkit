# Agent Skills specification and official CLI validation

[Русская версия](ru/AGENT_SKILLS_SPEC.md)

Authoritative sources:

- Specification: https://agentskills.io/specification
- Upstream reference source: https://github.com/agentskills/agentskills/tree/main/skills-ref
- Pinned upstream commit: https://github.com/agentskills/agentskills/commit/69ef37e9424c0a7ea9dd2293b559e43ec8176379
- Upstream source version at that commit: `0.1.0`, requires Python >=3.11.

## Structural contract

Each skill has a `SKILL.md` with YAML frontmatter. Required fields:
`name` (matching the directory, lowercase alphanumeric Unicode and hyphens,
no leading/trailing or adjacent hyphens, at most 64 characters) and
`description` (non-empty string, at most 1024 characters). Optional top-level
fields: `license`, `compatibility` (at most 500 characters),
`metadata`, `allowed-tools`. Details and accepted parsing are determined by
the pinned upstream implementation.

## Local execution

The reference implementation is **not** the unrelated `skills-ref` package
published on PyPI; upstream maintainers do not control that package
(https://github.com/agentskills/agentskills/issues/355).
Use a disposable Python virtual environment, then install the pinned official
GitHub source directly (no install.sh or unreviewed scripts):

```bash
python -m venv .venv
# POSIX: source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install "git+https://github.com/agentskills/agentskills.git@69ef37e9424c0a7ea9dd2293b559e43ec8176379#subdirectory=skills-ref"
skills-ref --version
python scripts/validate_pack.py
python scripts/validate_with_skills_ref.py --scope all
python -m unittest discover -s tests -p integration_skills_ref.py -v
```

The default `--scope all` covers **all skills currently declared** in
`MANIFEST.json` (72 in the checked revision: 23 core/generic,
27 QA, 1 Make Feature, 5 Frontend, 6 Backend, 3 Fullstack and 1 Product, 1 Management, 1 Analysis, 1 Design, 1 AI and 1 Reliability).
These counts are a current inventory, not a historic validation result.
The runner compares
the manifest with directories, rejects missing or unlisted entries and requires
an explicit success response from the reference CLI for every skill. A missing
binary, non-zero exit, unexpected/no output, subprocess error or per-skill
timeout is a failure. `--scope core` is available for partial local diagnostics
but is **not** accepted as the CI gate.

The existing `python scripts/validate_pack.py` remains mandatory: it enforces
Toolkit-specific inventory, local path/link conventions and consistency.
`skills-ref validate` checks the upstream frontmatter and directory format.
In GitHub Actions, only the existing required Ubuntu/Python 3.12 `tests` matrix
job installs the pinned CLI and runs the full checks; the other existing
required jobs continue the internal cross-platform checks.

The upstream README describes the reference implementation as demonstrative,
not production security software. Neither validator proves that linked scripts
are safe, a license is valid, an AI client will activate a skill, real model
behavior is correct, or the skill improves outcomes. No model or AI API is used.
