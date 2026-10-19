# Roadmap

## Near term

- [x] Add pinned official upstream `skills-ref` validation in the existing required CI job (Issue #24). Structural validation only; see [specification](AGENT_SKILLS_SPEC.md).
- [ ] Run controlled Codex/Claude/Hermes activation trials on independent demo repositories.
- [x] Record published component provenance and enforce inventory/release preflight (Issue #28). Owner reports ID1337 permission for exact snapshotted files; release still requires separate owner sign-off and independent legal verification is not asserted; see [audit](PROVENANCE_AUDIT.md).
- [x] Add deterministic checks for broken local links, anchors, profile inventories and declared workflow exclusions (Issue #26). Semantic instruction conflicts and agent discovery behavior remain manual/live checks.
- [x] Document CLI catalog and safe managed Codex/Claude migration (Issue #30; filesystem acceptance only, live client trials remain open).
- [x] Add versioned Codex/Claude/Hermes source-contract matrix and offline compatibility checks (Issue #32; L1-L3 only, no live discovery or activation). See [client evidence](CLIENT_COMPATIBILITY.md).

## Medium term

- [x] Add technology-neutral Frontend, Backend and Fullstack engineering extensions with focused opt-in profiles (Issue #40, source-only; live agent outcomes not yet measured).

- [ ] Evaluate the private optional skill inventory individually; publish only items with verified rights and project-neutral content.
- [ ] Benchmark quick/normal/deep feature-delivery against a plain agent baseline.
- [x] Add offline per-skill source quality metrics (structure, file bytes, repeatability, regression indicators) with independent empirical results still NOT_MEASURED (Issue #38; see [methodology](SKILL_QUALITY_METRICS.md)).
- [x] Improve portable install/update/uninstall with explicit ownership, file-level diff previews, rollback and recovery (Skill Manager v2, #12; passed cross-platform CI).
- [ ] Add optional adapters to real workflow runtimes; no forced framework dependency.

## Later

- [x] Document filesystem layouts and explicit client-support limitations for Codex, Claude Code, Hermes and custom clients (Issue #30; no live execution).
- [x] Curate task-based Backend, Frontend, QA, Agent Engineering and Research profiles (Issue #36, source-only; live-client activation unverified).
- [ ] Add automated provenance and release verification to community submissions.

Only checked items with actual results are marked complete.
