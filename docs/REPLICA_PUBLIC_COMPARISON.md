# Replica Skill: selective public UX comparison (#373)

**Only opt-in, read-only comparison.** This is not a clone tool, deployment pipeline, browser crawler, or the target project production integration.

Original project: https://github.com/Jakeschincariol/replica-skill
Pinned upstream commit: `77c9436fb3d18c3d58169efb8caf4fe906b0dc51`
License: MIT (copyright 2026 Jake Schincariol); verify license at pinned SHA before reusing original files.

Selected upstream methodology (referenced, **not installed or vendored**):
- `replica-recon/SKILL.md`: publicly documented screens, flows, features, cited sources
- `replica-diff/SKILL.md`: compare capability, not pixels; avoid copying trade dress
- `replica-test/SKILL.md`: test **our own** the target project flows, never automate/fuzz third-party products

## Boundary

Public documentation/store listings and user-authorized screenshots only. No bulk scraping, sign-in bypass, private APIs, bundled JavaScript extraction, third-party test traffic, original branding/assets/code, secret-bearing sessions, or self-installation. No paid AI/API, Codex CLI, background service, second skill manager, second orchestration engine, or direct the target project writes.

A reviewer creates a local JSON evidence packet. Each feature has separate source URLs and `VERIFIED`, `UNVERIFIED`, `CONTRADICTED` statuses **for each product**, with `gap=CANDIDATE` at most. A candidate is not an independently verified product defect. Screenshot comparisons require matching route, state, viewport, and documented permission; a screenshot alone cannot prove a behavior. Proposals for the target project Product V12 must be separately approved before implementation.

## Offline verification

```sh
python scripts/replica_public_evidence_gate.py docs/examples/replica_public_evidence.json
python -m unittest discover -s tests -p test_replica_public_evidence_gate.py -v
```

The validator only reads the explicitly supplied file. It does not contact GitHub or the competitor. It rejects missing evidence, local/private URLs, sensitive named fields, unpinned sources, and speculative `VERIFIED` gaps. **Limits:** the validator is not a sanitizer for arbitrary prose and cannot independently authenticate website content or a browser screenshot. Store only manually reviewed, public, nonsecret descriptions. Any result requiring a browser, actual screenshots, or user-owned account remains `NOT_RUN` until observed.

## Русский сценарий

1. Зафиксировать одного конкурента и один публичный пользовательский сценарий, ограничить объём.
2. Записать наблюдаемые особенности и отдельные публичные ссылки на конкурента и the target project.
3. Отличать подтверждённые факты от `UNVERIFIED`, указывать `CANDIDATE` вместо выдуманного дефекта.
4. Проверить JSON через валидатор, затем вручную изучить только кандидатов; никаких автоматических PR в the target project.

## English scenario

Select one competitor and one public flow; cite both products separately, keep unknowns explicit, run the offline validator, and require independent the target project owner/UX acceptance before proposing code changes.

**Release scope:** source-only optional evaluation and reproducible offline evidence gate. No original Replica plugin activation, competitive benchmark, visual screenshot proof, or the target project runtime change is claimed.
