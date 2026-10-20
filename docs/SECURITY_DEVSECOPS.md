# Security Engineering & DevSecOps (Issue #60)

[Русская версия](ru/SECURITY_DEVSECOPS.md)

**Purpose:** connect real assets and boundaries to threat hypotheses, risk decisions, controls and independent negative tests. This is not a scanner, certification, penetration test, or live-model evaluation. The optional `security-engineering` profile reuses existing security boundaries, security-review and security-testing skills.

## Quick start
Beginner: **"Review my application's security. First identify actual assets, trust boundaries and important risks in simple language. Start read-only, do not touch other people's servers, and use only free tools."**

Expert: **"Create a threat model with actor-resource-action tenant matrix, CI trust boundaries, secret lifecycle, dependency provenance, risks, verifiable invariants and negative acceptance tests; label missing evidence explicitly."**

Inspect source and available tests first. Never assume access to a running service. Toolkit is a read-only reference when used for someone else's project; provide reports in chat by default.

## Practical sequence
1. **Scope:** identify user assets, legitimate actors, data flows, entry points, storage and trust boundaries actually present.
2. **Threats:** state prerequisites, impacts, observed controls and hypothetical abuses; a theoretical threat is not a confirmed vulnerability.
3. **Controls:** build Threat ID -> Risk ID -> Control ID -> test. Each rule defines a legitimate ALLOW, a forbidden DENY and absence of unauthorized side effects.
4. **Execution:** only approved environments and isolated test users. An owner-A request for owner-B data must be DENY even if the client supplies owner-B's ID. An expired session is DENY. Hiding a button does not enforce backend authorization.
5. **Remediation:** finding -> prioritization -> minimal fix -> negative regression -> functional ALLOW test -> residual risk -> owner decision.

Authentication establishes identity; authorization determines whether that identity may access a particular resource. Tenant isolation prevents actions in another owner's partition. A trusted backend must enforce these boundaries.

## Secret lifecycle, CI and dependencies
Protect creation, storage, transit, use, rotation, revocation, deletion and compromise response. Never print token values in logs, PRs or findings. CI must account for fork PRs, shell injection in workflow expressions, least-privilege permissions, action pinning, external binaries and build artifact trust. Do not grant untrusted PR code write access.

Inspect direct/transitive dependencies, lockfiles, sources and versions; indicate license `UNKNOWN` and `VULNERABILITY_STATUS=NOT_CHECKED` where evidence is missing. **Integrity** (expected checksum), **provenance** (origin), **authenticity** (publisher), **license** (distribution rights) and **security** (tested properties) are different claims. SHA256 does not prove safe code. SBOM in SPDX/CycloneDX is optional, not a complete transitive inventory unless inputs support it.

Static source inspection supports hypotheses or static findings, not actual exploitability. Synthetic tests only demonstrate model behavior, not the deployed application's security. No findings within tested scope does not mean 100% secure.

## Self-contained demonstration
Run `python scripts/validate_security.py` and `python -m unittest tests.test_security_engineering -v`. Ten in-memory reference/mutant pairs cover cross-tenant read, client-owner spoofing, write-before-DENY, secret logging, tool path escape, missing approval, unsafe PR permissions, false provenance, checksum mismatch and sensitive report output. The independent contract oracle must pass every reference and reject every faulty variant. **No sockets, real tokens, servers or billable APIs.**

[Threat/risk/verification contract](../extensions/security/skills/security-engineering/references/CONTRACTS.md) · [Secret and CI guidance](../extensions/security/skills/security-engineering/references/OPERATIONS.md) · [Supply chain](../extensions/security/skills/security-engineering/references/SUPPLY_CHAIN.md).

Official references (checked 2026-10-20): [OWASP ASVS 5.0.0](https://asvs.owasp.org/), [NIST SSDF SP 800-218 1.1 final](https://csrc.nist.gov/pubs/sp/800/218/final), [SLSA v1.2 approved](https://slsa.dev/spec/v1.2/), [OWASP Software Component Verification](https://owasp.org/projects/software-component-verification-standard). These are guidance sources, not certifications.
