# Selective Spec Kit methodology adoption (Issue #375)

Source: [github/spec-kit](https://github.com/github/spec-kit) pinned at `67e0f7294e6e728ab60bf7b4590deb470448bc2d`, MIT (GitHub, Inc.). Reviewed `extensions/bug` and `extensions/assess` READMEs and manifests. No upstream code was copied, installed, or executed.

## Overlap and disposition

- **Full SDD:** REUSE_EXISTING. Toolkit `make-feature` already chooses quick/normal/deep and records criteria, decisions, plans, tests. Do not introduce another mandatory orchestrator.
- **Bug assessment/fix/test:** ADAPT_METHOD. Distinguish a symptom, an unverified root-cause hypothesis, a reproduced failing baseline, and actual post-fix regression evidence. If the reproduction or test has not run, report NOT_REPRODUCED or NOT_VERIFIED, never PASS.
- **Idea intake/research/define/shape/decide:** ADAPT_METHOD. A separate pre-implementation GO / CLARIFY / STOP decision can prevent unnecessary work. GO permits the existing Make Feature process; it does not grant production or spend permissions.
- **Trivial edit:** Existing quick mode without new documents or ceremony.

The normative decision constraints and synthetic RU/EN cases are in `integrations/spec-kit/method_cases.json`, validated by `tests/test_spec_kit_method_cases.py`. Cases are static contract examples, **not** measured live-client agent accuracy. There is no additional dependency, paid API, CLI, live agent, hooks, auto-write or deployment. Rollback consists of reverting these isolated guidance and tests.
