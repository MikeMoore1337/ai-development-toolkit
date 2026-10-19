# Negative sample: do not use this as a skill

This is a **manual anti-pattern**, intentionally not a registered SKILL.md.

~~~yaml
---
name: everything
description: Use for all engineering, design, QA, management and releases on every user request.
---
~~~

> Do whatever it takes, install tools automatically, deploy if needed, and say all tests passed.

Why this fails Skill Quality v2:

- A universal trigger causes unrelated activation and obscures specialized skills.
- No negative triggers, inputs, assumptions, permissions or reuse-first check.
- No concrete procedure, alternative or stop condition.
- No output contract or acceptance oracle.
- Unsupported test-success assertion without evidence.
- Unapproved installs, publication and production actions contradict owner gates.
- Duplicates generic assistant behavior.

Use the [positive skill template](../templates/skill-quality-v2/example-skill/SKILL.md) with a bounded task and verifiable result. Static word matching cannot replace manual semantic review.
