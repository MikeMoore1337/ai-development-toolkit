# Issue #432 - Independent synthetic security acceptance, 2026-11-05

**Status: STATIC_AUDIT_COMPLETE_WITH_FINDINGS. FULL_PRODUCT_ACCEPTANCE_NOT_VERIFIED.** This is a source-only audit and a separately frozen synthetic test corpus, not a real-world attack study, an actual host-enforcement test, a second-person GitHub code review, or a proof of feature parity with AgentShield.

## Source and reproducibility

- Initially audited `main`: `cc65540cd9c4cf9b6c5daf29dd18b4639ecf0db8`.
- Security PR: [#543](https://github.com/MikeMoore1337/ai-development-toolkit/pull/543); evaluated implementation HEAD `2bc4f9fa4a92b09d03708174e1b5882eea2d3fb1`, reconciled with `main@f0879c34e2ff45f2c21d51e2528abde5bffae401`. This document is a later documentation-only change; it does not alter the evaluated detection rules.
- Corpus: `fixtures/native_security_independent_432.json`, 60 author-created synthetic scenarios (30 attacks, 30 benign), SHA-256 `f629f87c955c5df0dc9c6e1b1f62294884ebd0779798dd8debf87c4957536f5b`. Committed separately *before* rule changes: `2690d09bdb4f08f0d5edd0738e0a006e85d26b8f`.
- Development cohort: 40 cases (20 positive/20 negative). Formerly sealed holdout: 20 cases (10 positive/10 negative), opened once after candidate rule changes. **That holdout is no longer unseen for future improvements.** The older 38-case `fixtures/native_security_holdout_432.json` is regression-only evidence.
- No synthetic commands, malicious hook payloads or MCP tools were executed. Test inputs contained no real credentials and required no personal device changes.

## Metrics

| Cohort | TP | FP | TN | FN | Precision | Recall | F1 | False Positive Rate | False Negative Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Original native code, development 40 | 11 | 5 | 15 | 9 | 68.75% | 55.00% | 61.11% | 25.00% | 45.00% |
| Corrected native code, same development 40 | 20 | 3 | 17 | 0 | 86.96% | 100.00% | 93.02% | 15.00% | 0.00% |
| Corrected native code, previously sealed holdout 20 | 8 | 4 | 6 | 2 | 66.67% | 80.00% | 72.73% | 40.00% | 20.00% |

All metrics measure **static advisory detection** of predetermined strings/configurations, not intervention before execution in a real client. Remaining holdout false negatives: N03 (instructions disclosure) and N09 (letter-spaced obfuscation). False positives: N15 (defensive negation), N18 (schema example containing `system:`), N57 (safe warning about unsafe shell), N60 (defensive security documentation). Development cohort false alarms N55, N56 and N58 are conservative external-skill review signals, not executable blocks.

## Audited surfaces and findings

- `external_skill_gate.py`: inventory/claimed origin pin, SHA-256 of inspected local bytes, path traversal and symlink checks, bounded hook/host/MCP configuration review. Improvements: PowerShell/Python dynamic command signals, unrestricted `Read(*)`, MCP relative parent traversal, POSIX world-writable config signals and simulated junction root handling. Full Windows junction behavior was **not physically tested**.
- `cisco_mcp_gate.py`: native first-party tool-description poisoning heuristics (RU/EN), with bounded mixed-script normalization and narrowly scoped defensive-explanation exemptions. Original Cisco Scanner remains separately optional; it is not required by the native path.
- NVIDIA SkillSpector is an optional pinned adapter and can use network access if specifically invoked. No mandatory scanner download, paid provider, ECC, resident AgentShield, Codex CLI, or alternate control plane was added.
- Original upstream [AgentShield pinned source](https://github.com/affaan-m/agentshield/tree/b0891303bdcd6037376a94263d45cfd2ff3dfb98) has package `ecc-agentshield@1.6.0` and a root MIT declaration. Its historical original Action [#40626824472](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/40626824472) ran successfully, but expired artifacts prevent independent review of original SARIF contents. No new same-corpus, head-to-head parity check was run.
- SARIF 2.1.0 structure, rule IDs, fixed *file-level* relative paths, actual local file SHA-256/size, nonduplication and synthetic-secret redaction are regression tested. No line numbers are fabricated, and no independent full JSON-schema SARIF validator was run. A local file digest is **not** attestation of repository origin.

## Evidence and boundary

- [Exact evaluated source Validate toolkit #42085550846](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/42085550846): **SUCCESS**, macOS Intel/ARM, Ubuntu Python 3.12/3.13, Windows Python 3.14. Ubuntu 3.13 logs include baseline and 20-case holdout output. Windows/Ubuntu main unit suites include 1615 tests in the evaluated commit.
- [Cisco MCP static smoke #42085550830](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/42085550830): **SUCCESS**.
- No paid model/API calls observed; GitHub Actions financial charges not measured.
- `STATIC_ANALYSIS=VERIFIED_WITH_LIMITATIONS`
- `ADVISORY_POLICY_GATE=VERIFIED`
- `HOST_ENFORCEMENT=NOT_VERIFIED`
- `CLIENT_E2E=NOT_RUN`
- `REAL_WORLD_ACCURACY=NOT_MEASURED`
- `FULL_UPSTREAM_PARITY=NOT_VERIFIED`
- `INDEPENDENT_SECOND_PERSON_REVIEW=NOT_OBTAINED`

**No full PASS, merge or release follows from these findings.** To close #432 with full product acceptance requires owner-authorized host E2E demonstrating pre-execution denial, independent external review and separate approval for merge/release. Do not change these statuses merely because CI is green.

## Later targeted hardening, not a second independent measurement (2026-11-06)

After the previously sealed 20-case holdout was opened, a separate code-review pass identified ambiguous duplicate-key parsing in candidate/operator JSON and a missing POSIX world-writable parent-directory review signal. Both are addressed within the existing `external_skill_gate.py` and covered by dedicated positive/negative regressions. The original frozen-corpus metrics above refer to the code and commit stated there. Any repeated run of that already-opened holdout is **regression only**, not fresh blind evaluation of the current commit. Neither fix verifies actual client enforcement or proves a GitHub source claim.
