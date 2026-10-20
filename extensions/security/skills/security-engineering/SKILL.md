---
name: security-engineering
description: "Model security threats, trust boundaries, authorization, secret and supply-chain risks, then define verifiable controls and residual risk. Use for threat modeling, security architecture and DevSecOps planning, not ordinary unit tests, isolated code fixes or deployments."
metadata:
  pack: "security"
  version: "1.0.0"
---

# Security Engineering

**Use for:** "Threat model my service", "Map access and tenant risks", "Create a security risk register", "Review CI trust boundaries", "Design DevSecOps acceptance", "Смоделируй угрозы", "Проверь архитектуру безопасности".

**Do not use for:** ordinary Python debugging, unit testing, benchmarking, Docker setup, UI redesign or release execution. For narrow code review use `security-review`; authorized negative execution use `security-testing`; backend access-control implementation use `authentication-authorization`; third-party components use `external-skill-review`; release decisions use `release-safety`. This is **not** another controller or scanner.

1. **Scope and authority:** identify the real system, owned assets, legitimate actors, data flows, trust boundaries and exact permission to test. Never test a third-party host or production by default. Toolkit is read-only when used in another project; return findings in chat unless an output location is expressly authorized.
2. **Threat model:** for each real boundary record entry point, preconditions, threat scenario, impact and evidence. Use `HYPOTHETICAL` or `NOT_VERIFIED` unless supported; a theory is not a confirmed vulnerability. STRIDE is optional.
3. **Risk and verification:** link Threat ID -> Risk ID -> Control ID -> test. Specify the observable ALLOW and DENY invariant, forbidden side effects, confidence and evidence classification. Do not invent CVE/CVSS or numeric likelihood.
4. **Select controls:** least privilege, trusted-side resource ownership checks, lifecycle-managed secrets, safe CI trust boundaries and verified dependencies as applicable. Reuse existing Toolkit Security and QA skills; do not add duplicate scanners.
5. **Verify independently:** use authorized isolated test principals or offline synthetic fixtures. Check legitimate actions still work. A proposed fix is not a proven mitigation; a passed synthetic oracle is not a real system penetration test. See [contracts](references/CONTRACTS.md).
6. **Assess delivery chain:** distinguish integrity, provenance, authenticity, license and vulnerability evidence. Review lockfiles, actions, build artifacts and optional SBOM without making an inventory into a security guarantee. See [supply chain](references/SUPPLY_CHAIN.md).
7. **Review secrets and CI:** never print real secret values. Examine secret creation, storage, rotation, revocation and redacted findings; examine untrusted PR workflows, permissions, injections, downloads and artifacts. See [CI and secrets](references/OPERATIONS.md).
8. **Report and hand off:** prioritize confirmed or plausible risk with a minimal fix and regression test, retain uncertainty, identify residual risk and the responsible human decision. Do not claim regulatory compliance, SLSA level, or safety without evidence.

User guides: `docs/SECURITY_DEVSECOPS.md` and `docs/ru/SECURITY_DEVSECOPS.md`. Demonstration: `python scripts/validate_security.py` from the Toolkit root (offline synthetic evidence only).
