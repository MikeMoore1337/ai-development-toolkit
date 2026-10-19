# Roadmap

## Near term

- [x] Add pinned official upstream `skills-ref` validation in the existing required CI job (Issue #24). Structural validation only; see [specification](AGENT_SKILLS_SPEC.md).
- [ ] Run controlled Codex/Claude/Hermes activation trials on independent demo repositories.
- [x] Record published component provenance and enforce inventory/release preflight (Issue #28). Owner reports ID1337 permission for exact snapshotted files; release still requires separate owner sign-off and independent legal verification is not asserted; see [audit](PROVENANCE_AUDIT.md).
- [x] Add deterministic checks for broken local links, anchors, profile inventories and declared workflow exclusions (Issue #26). Semantic instruction conflicts and agent discovery behavior remain manual/live checks.
- [ ] Introduce public docs for CLI usage and migration between clients.

## Medium term

- [ ] Evaluate the private optional skill inventory individually; publish only items with verified rights and project-neutral content.
- [ ] Benchmark quick/normal/deep feature-delivery against a plain agent baseline.
- [ ] Add structured skill quality metrics (correctness, context cost, reproducibility, regression risk).
- [x] Improve portable install/update/uninstall with explicit ownership, file-level diff previews, rollback and recovery (Skill Manager v2, #12; passed cross-platform CI).
- [ ] Add optional adapters to real workflow runtimes; no forced framework dependency.

## Later

- [ ] Maintain compatibility matrix for Codex, Claude Code, Hermes and other clients.
- [ ] Publish curated packs for QA, frontend, backend, agent architecture and research.
- [ ] Add automated provenance and release verification to community submissions.

Only checked items with actual results are marked complete.
