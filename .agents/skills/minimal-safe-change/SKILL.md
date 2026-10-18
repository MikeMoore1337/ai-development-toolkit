---
name: minimal-safe-change
description: Prefer the smallest maintainable solution while preserving tests, security and compatibility. Use for implementation, refactoring, debugging or code review.
---

# Minimal safe change
A simple solution is not a shortcut around correctness.

1. Map the relevant call path, entry points and current behavior before proposing changes.
2. Consider removing redundant code, reusing an existing abstraction, a tiny local fix, or a new abstraction; select the least complex **correct** option.
3. Avoid new dependencies, generalized frameworks and large refactors without a demonstrated requirement.
4. Keep valid trust-boundary checks, authorization, recovery, observability and accessibility even when they add lines.
5. Make behavioral changes explicit. If a proposed simplification changes a public interface, storage format or existing semantics, identify migration/regression tests.
6. Add a focused test for risky branches, parsers, state transitions, security-sensitive logic and previously failing cases.
7. Reject one-liners that are harder to debug, reason about or maintain; readability counts.
8. In review, show the smallest alternative and why it would or would not preserve invariants.

**Output:** rationale for smallest safe diff, changed invariants, tests run, trade-offs.
