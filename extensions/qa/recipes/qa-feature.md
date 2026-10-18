# Feature QA recipe

1. Read product change and confirm acceptance criteria (`requirement-analysis`).
2. Enumerate threats, state transitions and test oracles (`test-analysis-design`).
3. Identify shared callers and contracts (`change-impact-analysis`).
4. Add focused tests in the repository's actual framework (`api-testing`, `pytest-test-design`, `playwright-testing`, or another project skill).
5. Independently review tests (`test-review`) and collect observed results.
6. Assess release evidence (`quality-gate-assessment`), respecting existing merge/deploy gates.

For small bug fixes omit redundant stages, but never skip a material risk check purely to be faster.
