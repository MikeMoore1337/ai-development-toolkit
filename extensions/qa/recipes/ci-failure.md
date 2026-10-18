# CI failure recipe

Capture exact run, commit, environment, failing step and first causal observation. Classify via `failure-triage`. Use `flaky-analysis` only if nondeterminism has evidence. Propose one falsifiable fix and verify against both the failing case and a nearby regression. Explain what remains unverified.
