# Supply chain, dependencies and optional SBOM

Inventory direct and, when available, transitive dependencies; lockfiles, package sources, versions, checksums, signatures/attestations, licenses, build steps, actions, downloadable binaries, agent skills and artifacts. For each significant component record purpose, actual source, version, access, license or `UNKNOWN`, advisory check date/source, `VULNERABILITY_STATUS=NOT_CHECKED` when absent, upgrade compatibility and residual risk.

**Separate five claims:** Integrity = bytes match a known digest; provenance = recorded origin; authenticity = publisher identity is verified; license = use/distribution permission; security = findings within a tested scope. SHA256 alone confirms only the first relative to a trusted expected digest. A package may have no known advisory and still be unsafe. Reuse Toolkit `provenance/skills.json`, `SHA256SUMS.txt`, `validate_provenance.py`, `verify_checksums.py` and `external-skill-review`. Never create a shadow registry or change reviewed source snapshots.

**SBOM is optional:** use maintained SPDX or CycloneDX formats only when there is a supply-chain, customer or release need. Identify component/type/version/source, IDs only when known, relationships only when known, generation date, input revision, evidence and completeness. A list of direct packages is not a complete transitive SBOM. Do not claim an SLSA level without verifying requirements in the applicable track.

Official references checked 2026-10-20 (status, not certification):
- OWASP ASVS 5.0.0 stable: https://asvs.owasp.org/
- NIST SSDF SP 800-218 revision 1.1 final: https://csrc.nist.gov/pubs/sp/800/218/final
- SLSA specification v1.2 approved; distinguish Build and Source tracks: https://slsa.dev/spec/v1.2/
- OWASP Software Component Verification Standard: https://owasp.org/projects/software-component-verification-standard
