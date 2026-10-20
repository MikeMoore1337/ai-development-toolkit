# Offline skill routing regression checks

[Русская версия](ru/SKILL_ROUTING_EVALS.md) | [Agent Skills specification](AGENT_SKILLS_SPEC.md) | [Real-agent evaluation](SKILL_EVALS.md)

This **zero-cost lexical diagnostic** compares natural-language requests against the `name` and `description` frontmatter of **all 65 declared skills** in `MANIFEST.json`. It is inspired by the layered evaluation methodology in [Addy Osmani's agent-skills](https://github.com/addyosmani/agent-skills), not a copy of that implementation. No external repository code was imported.

```bash
python scripts/skill_routing_eval.py --strict
python -m unittest tests.test_skill_routing_eval -v
```

The cases in [fixtures/skill_routing_cases.json](../fixtures/skill_routing_cases.json) contain positive requests (the target should rank in the top three) and neighboring negative requests (the target must not rank first). The strict CI gate checks **only these curated expectations**. It is not a universal accuracy percentage and does not infer that uncovered skills were tested. Expand cases when descriptions change or semantic overlap is suspected, and review their expected targets rather than weakening assertions to silence failures.

The ranking algorithm uses deterministic lowercase tokenization, simple English suffix normalization, weighted skill names and descriptions, and corpus frequency. It is deliberately a lexical approximation: paraphrases, Russian-language requests, client selection behavior and actual runtime activation can differ. A high lexical rank **does not prove** a skill is installed, discovered, invoked or effective. All those observations remain `NOT_MEASURED` and belong to [Issue #11](https://github.com/MikeMoore1337/ai-development-toolkit/issues/11).

New test case format: `{ "id": "unique-id", "target": "declared-skill-name", "positive": ["..."], "negative": ["..."] }`. Every case requires both types of prompt. Unknown skills, duplicates, invalid prompt data or missing source skills fail closed. The script reads `SKILL.md` but never executes bundled scripts, downloads dependencies, accesses external accounts or writes to user projects.

Do not use static rank as justification to rewrite short or protected skills without a specific demonstrated problem. Compare results with real client runs only after a separately authorized, verified zero-spend path becomes available.
