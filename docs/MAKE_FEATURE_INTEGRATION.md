# Make Feature 0.3.0 - English user guide

[Русская версия](ru/MAKE_FEATURE_INTEGRATION.md) | [Installation](INSTALLATION.md) | [Canonical skill (Russian)](../extensions/make-feature/skills/make-feature/SKILL.md)

**Make Feature** is an optional feature-delivery workflow: a short request → solution choice → contract and plan → implementation → verification and hand-off. Its bundled `SKILL.md`, README and most references are **written in Russian**. This page explains how to use it in English. It is **not a second installable skill**, nor evidence of automatic activation by an English-speaking client.

The source is Make Feature 0.3.0 by Artemiy Miller. The Toolkit bundles its original source with a portable Agent Skills metadata adjustment, workspace/budget/state helpers, templates and tests. Consult its [portability notes](../extensions/make-feature/skills/make-feature/PORTABILITY_NOTES.md), [license](../extensions/make-feature/skills/make-feature/LICENSE) and [publication restrictions](PUBLICATION_POLICY.md). The owner reports separate authorization; it has not been independently verified. Its protected source snapshot is **not** changed by localization.

## When to use Make Feature

Use it when implementing a feature requires coordinated requirements, technical decisions, scoped changes and proof of completion. For a trivial edit with a clear plan, prefer direct work. **Never run `make-feature` and `feature-delivery` as two controllers of the same task.**

| Mode | Appropriate circumstances | Default ceiling per run |
| --- | --- | --- |
| `quick` | Clear, reversible change in one established area, without unknown high-risk permissions, money or data | 2 delegations, 1 post-review correction, 10 minutes |
| `normal` | A new feature or connected areas with known contracts | 6 delegations, 1 correction, 25 minutes |
| `deep` | Money, permissions, irreversible migration/data loss, unknown decisive integration or disputed product decisions | 12 delegations, 2 corrections, 45 minutes |

Ceilings are not quotas; a lower user-defined limit prevails. Changing mode or resuming work does not reset the counters, extend time or confer permissions.

## Safe project-local installation

Run these commands **from the Toolkit checkout**, with Python 3.12+ and a **pre-existing trusted target directory**:

~~~bash
python scripts/skill_manager.py catalog --profile make-feature
python scripts/skill_manager.py install --target /path/to/project --profile make-feature
python scripts/skill_manager.py install --target /path/to/project --profile make-feature --apply
python scripts/skill_manager.py status --target /path/to/project
~~~

The first install is a **read-only preview**. Confirm paths and existing skills before explicitly using `--apply`. For a Claude Code layout consistently add `--layout claude` to install and status. The manager controls only its own files and does not replace unrelated skills, `AGENTS.md` or `CLAUDE.md`. See [installation and recovery](INSTALLATION.md).

The [original package INSTALL.md (Russian)](../extensions/make-feature/skills/make-feature/INSTALL.md) describes manually installing an issued archive for clients such as Hermes. This does **not** imply a dedicated Hermes adapter in the Toolkit. Verify client capabilities, exact package, paths and permissions separately; never combine different installed versions.

Sample **human request** after the client has demonstrably discovered the skill:

> Use the installed make-feature skill for the following change: “Add a CSV import preview with clear validation errors.” Show options, respect project rules, and record actual tests.

The source activation description uses the Russian words “Сделай мне функцию”. An English-language request **cannot prove** that an AI client discovered or selected the Russian skill automatically. Use the client's actual explicit skill-selection mechanism and verify the result.

## Workflow and evidence

1. **Understand** the request, current behavior, objective acceptance criteria (`C*`), baseline and risks.
2. **Choose** among reuse and minimal alternatives; record the decision (`D*`), sources, costs and trade-offs.
3. **Design** data paths, contracts, errors, retries, permissions, tasks (`T*`) and verifications.
4. **Implement** in approved files within the real tool/permission limits; execute relevant regression tests.
5. **Review** independently only when a distinct reviewer context actually exists. Otherwise report tests and self-checks without fabricating reviewer approval.

Usually four current Markdown artifacts in `.make-feature/<slug>/` suffice: original request, index, solution/plan and verification. The authoritative source references are in Russian: [documents](../extensions/make-feature/skills/make-feature/references/documents.md), [workflow](../extensions/make-feature/skills/make-feature/references/workflow.md), [runtime](../extensions/make-feature/skills/make-feature/references/runtime.md), [agents](../extensions/make-feature/skills/make-feature/references/agents.md), [verification](../extensions/make-feature/skills/make-feature/references/verification.md).

State/budget helpers track recorded attempts and local state; they **do not** intercept LLM calls, measure real token/cost usage or enforce external client execution limits.

| Status | Meaning |
| --- | --- |
| `SELF_CHECK` | Work reviewed by its author - not independent acceptance |
| `TESTED` | Actual tests ran, with command/output and covered criteria |
| `INDEPENDENT_REVIEW` | A separate context not involved in implementing the reviewed version |
| `DONE_WITHOUT_INDEPENDENT_REVIEW` | Reversible quick/normal work only, with all required criteria proven and no mandatory independent gate |
| `INDEPENDENT_REVIEW_PENDING` / `INCOMPLETE` | Required review or acceptance criteria remain unresolved |
| `BLOCKED_REVIEW` | Required high-risk deep review/owner gate not met; do not perform the risky action |

Report exact changes, factual checks, outstanding criteria, actual reviewer availability and next steps. Copying files is **not evidence** of discovery, model use, deploy readiness or improved task effectiveness. The [original test report](../extensions/make-feature/skills/make-feature/TEST-REPORT.md) gives limited source-package evidence; no Toolkit runtime/client benchmark is claimed.

**Language boundary:** this English **human guide** summarizes the single original Russian skill; it is not a byte-for-byte translation. For executable behavior and permission decisions use the actual `SKILL.md` and project rules. English-only skill activation is **NOT_TESTED**.
