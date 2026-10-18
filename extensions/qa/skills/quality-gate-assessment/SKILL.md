---
name: quality-gate-assessment
description: "Assess merge or release readiness from acceptance criteria and actual verification evidence. Use before approving risky changes or deployments."
metadata:
  pack: "qa"
  version: "1.0.0"
---

# Quality Gate Assessment

1. Identify the *project's actual* approval/release policy. Universal skills cannot grant merge/deployment permissions.
2. Check acceptance criteria one by one against observed tests, review evidence, security checks, migrations, documentation and deployment plan.
3. Distinguish `PASS`, `FAIL`, `NOT_RUN`, `NOT_APPLICABLE`, `BLOCKED` and `UNKNOWN` - missing results are not successes.
4. Evaluate failure severity, blast radius, rollback/mitigation and production observability. An automated check is not a substitute for required human approval.
5. State one overall evidence finding: `READY_FOR_REVIEW`, `BLOCKED`, or `INSUFFICIENT_EVIDENCE`. Never claim deployment occurred without production evidence.

See [release gate worksheet](references/GATE.md) for the evidence matrix.
