# Roadmap

[Русская версия](ru/ROADMAP.md)

## Current baseline (24 October 2026)

The latest **published source release** is [v5.5.6](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.6), with `MANIFEST.json.version = 5.5.6` at immutable tag commit `490cec222c4c2551a7bbe6f20bb0e9a316af13e1`. The [archive CI](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/40109117878) verified SHA256 and technical provenance; publication-time docs were stale and are corrected separately. Real-agent effectiveness and independent legal rights remain unverified. Later `main` commits are not automatically released. See [release procedure](RELEASE_PROCESS.md).

The declared catalog at this revision contains **82 skills, 45 profiles and 16 roles**. Use [MANIFEST.json](../MANIFEST.json) for the authoritative current counts. CI checks source format, packaging, provenance, release integrity and offline contracts; it does **not** prove actual agent discovery or improved task outcomes.

This page is a development guide, **not an auto-updating Issue tracker**. Click the linked GitHub Issues for current status and acceptance evidence.

## Completed delivery

- **Earlier foundations:** pinned upstream `skills-ref` structural checks [#24](https://github.com/MikeMoore1337/ai-development-toolkit/issues/24); provenance inventory and publication gate [#28](https://github.com/MikeMoore1337/ai-development-toolkit/issues/28); documentation integrity [#26](https://github.com/MikeMoore1337/ai-development-toolkit/issues/26); safe installation/ownership and rollback [#12](https://github.com/MikeMoore1337/ai-development-toolkit/issues/12); client layout/contract docs [#30](https://github.com/MikeMoore1337/ai-development-toolkit/issues/30) and [#32](https://github.com/MikeMoore1337/ai-development-toolkit/issues/32); engineering packs and profiles [#40](https://github.com/MikeMoore1337/ai-development-toolkit/issues/40) / [#36](https://github.com/MikeMoore1337/ai-development-toolkit/issues/36); offline source metrics [#38](https://github.com/MikeMoore1337/ai-development-toolkit/issues/38).
- **Roadmap I, closed:** [#271](https://github.com/MikeMoore1337/ai-development-toolkit/issues/271) published-release identity, [#272](https://github.com/MikeMoore1337/ai-development-toolkit/issues/272) shared client routing contracts, [#273](https://github.com/MikeMoore1337/ai-development-toolkit/issues/273) additional negative/diagnostic routing checks.
- **Roadmap II, closed:** [#274](https://github.com/MikeMoore1337/ai-development-toolkit/issues/274) source/version diagnostics, [#275](https://github.com/MikeMoore1337/ai-development-toolkit/issues/275) guarded source update/rollback, [#276](https://github.com/MikeMoore1337/ai-development-toolkit/issues/276) bounded context measurement, [#277](https://github.com/MikeMoore1337/ai-development-toolkit/issues/277) task-first onboarding.
- **Roadmap III, closed:** [#278](https://github.com/MikeMoore1337/ai-development-toolkit/issues/278) QA change-impact evidence, [#279](https://github.com/MikeMoore1337/ai-development-toolkit/issues/279) offline orchestration decision checks, [#280](https://github.com/MikeMoore1337/ai-development-toolkit/issues/280) pinned supply chain and reproducible zero-cost examples.
- **Publication, closed:** [#293](https://github.com/MikeMoore1337/ai-development-toolkit/issues/293) released v5.5.5, verified downloadable source ZIP, provenance and post-release documentation. Prior [#259](https://github.com/MikeMoore1337/ai-development-toolkit/issues/259) completed the bilingual editorial baseline.

These completed Issues demonstrate their **stated scopes**, not universal real-agent compatibility or effectiveness.

## Roadmap IV (completed within stated scope)

All eight issues below are closed in their limited accepted scopes; links provide implementation evidence. Source validation does not prove independent real-agent benefit:

1. **P0:** [#294](https://github.com/MikeMoore1337/ai-development-toolkit/issues/294) current-state bilingual documentation and roadmap.
2. **P1:** [#295](https://github.com/MikeMoore1337/ai-development-toolkit/issues/295) clearer ChatGPT / Personal MCP / Project MCP / Skill Manager selection; [#296](https://github.com/MikeMoore1337/ai-development-toolkit/issues/296) new RU/EN routing stress cases.
3. **P1:** [#297](https://github.com/MikeMoore1337/ai-development-toolkit/issues/297) observable L4/L5 client discovery and use; [#298](https://github.com/MikeMoore1337/ai-development-toolkit/issues/298) measured baseline-vs-skill task benefit, only where free and permitted.
4. **P2:** [#299](https://github.com/MikeMoore1337/ai-development-toolkit/issues/299) evidence-driven context de-duplication; [#300](https://github.com/MikeMoore1337/ai-development-toolkit/issues/300) portable synthetic QA/UX/UI scenarios.
5. **P3:** [#301](https://github.com/MikeMoore1337/ai-development-toolkit/issues/301) lean catalog/provenance maintenance.

## Explicitly limited or deferred

- [#11](https://github.com/MikeMoore1337/ai-development-toolkit/issues/11) real Codex/Claude CLI evaluation is **CLOSED / NOT_PLANNED** under the owner's **ZERO-SPEND** restriction. The trial harness exists but cannot be executed to generate paid model runs, including with acknowledgement flags. Do not mark its real executions complete or reopen paid trials implicitly.
- [#141](https://github.com/MikeMoore1337/ai-development-toolkit/issues/141) is **CLOSED / COMPLETED for a narrower zero-cost exploratory orchestration pilot**. It does not substantiate independent L4-L6 compatibility, skill efficacy, universal time savings, or statistically valid A/B results. See [client compatibility](CLIENT_COMPATIBILITY.md) and [pilot protocol](REAL_AGENT_PILOT.md).
- Full live client discovery/activation and measured benefits remain `NOT_TESTED` / `NOT_MEASURED` unless separately supported by execution records. The deterministic lexical router is not a semantic model; curated fixture passes are not independent semantic accuracy.
- Private optional skill submissions and community components require proven rights, project-neutral content and [provenance gates](PUBLICATION_POLICY.md) before redistribution. Do not introduce a second runtime framework or force a paid API to meet this roadmap.
