# Original ECC AgentShield integration (#432)

This optional GitHub workflow runs the **original** [AgentShield](https://github.com/affaan-m/agentshield) action, not a rewritten scanner. Reviewed upstream source: `affaan-m/agentshield@b0891303bdcd6037376a94263d45cfd2ff3dfb98` (package `ecc-agentshield` 1.6.0; root MIT). GitHub Actions executes the action bundled in the upstream repository: no local npm/global install, no Codex CLI or Claude CLI, no model calls, and no Toolkit runtime or skill changes.

## When it runs

- **On PRs changing this integration:** scans only the deliberately vulnerable **synthetic** fixture at `fixtures/ecc-agentshield/vulnerable/.claude`. Asserts that the original scanner discovers at least one issue and that its redacted evidence pack verifies. The same PR also makes a **separate advisory scan of the actual public Toolkit checkout** (SARIF and evidence pack); findings are evidence for human review, not an automatic release gate. These are real original-scanner invocations, not mocked unit tests.
- **Manually:** Actions → **ECC AgentShield (opt-in)** → Run workflow → `repository` to scan the checked-out Toolkit source or `synthetic` to recheck the fixture. Repository scans are *advisory*: `fail-on-findings=false` while false positives and policy baselines are reviewed. Missing/malformed SARIF and action failures still fail the job.
- Only `contents: read` is granted; checkout does not persist credentials. The action writes SARIF and an evidence pack under the runner temporary directory and uploads redacted artifacts retained for seven days. It does **not** upload SARIF to Code Scanning, modify repository sources, accept private credentials or activate runtime hooks.

## Safety and support

The upstream action itself is trusted executable software with permissions of a hosted runner. Source SHA pinning protects from moving Git tags but **does not independently attest** all dependencies, package rights, external egress or supply-chain security. The scanner's offline supply-chain option is enabled; online npm metadata, active injection tests, sandbox hook execution, taint mode, Opus/deep analysis, `--fix`, live monitoring and new providers are **not enabled**.

A passing synthetic PR run demonstrates only that this original action runs and recognizes deliberately unsafe config. It is **not** proof that the real source has no security issues, that the local Windows Codex Desktop has AgentShield, or that there are no hidden false negatives. The scan's numeric grade is not a release authorization. Compare with Toolkit SkillSpector and Cisco MCP Scanner results; use their existing owner-review gates.

**Rollback:** remove or disable `.github/workflows/ecc-agentshield.yml` in a reviewed PR. No global installation, resident service, Codex plugin, database or project-local state is created. For a manual scan, delete GitHub Actions evidence artifacts when no longer needed (seven-day retention is the default here). No paid API calls are requested; runner consumption still follows the repository's GitHub Actions plan and policies.

## Verification states

- `SOURCE_REVIEWED`: official action manifest has `node24` entrypoint and bundled `dist/action.js`; source pin confirmed. This does not mean it ran.
- `ORIGINAL_SCANNER_SMOKE`: requires a successful **actual workflow job** with numeric nonzero findings for the fixture, SARIF 2.1.0, and verified evidence pack.
- `REAL_REPOSITORY_SCAN`: PR advisory run or separate manual dispatch on the public repo; findings require human triage.
- `WINDOWS_DESKTOP`: not part of this GitHub integration; never infer live Codex hook/skill activation from Actions.
