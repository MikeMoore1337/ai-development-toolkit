# Toolkit Native Host Config Security (#432)

This is an **opt-in static host configuration audit**, added to the existing Toolkit `external_skill_gate.py` rather than a second controller. Toolkit does not install or run ECC, AgentShield, a plugin, model, external scanner, MCP server, hook or daemon.

## Usage

Point at an **explicitly selected synthetic or approved project directory**, not the home directory:

```sh
python scripts/external_skill_gate.py --host-config-root /path/to/approved/project
python scripts/external_skill_gate.py --host-config-root /path/to/approved/project --format sarif
python -m unittest tests.test_external_skill_gate -v
```

Exit codes: `0 PASS` means *only the configured subset* is free of these static findings, `1 REVIEW_REQUIRED` means uncertainty or medium findings, `2 BLOCKED` means high-risk or invalid input. Output is JSON or SARIF 2.1.0 to stdout; the JSON `evidence.files` includes relative allowlisted paths, byte counts and SHA-256 of inspected bytes, not contents. No evidence files are written without an operator choosing a redirect. Never treat a clean scan as a runtime authorization.

## Supported exact file paths and checks

| File | Static checks |
| --- | --- |
| `.codex/config.toml` | `danger-full-access`, approval `never`, declared MCP server env/roots |
| `.codex/hooks.json` | Command strings nested under hooks: network egress, pipe to shell, untrusted interpolation, destructive command |
| `.claude/settings.json` and `settings.local.json` | Hooks as above, explicit `Bash(*)`/`Write(*)` allow permissions |
| `.mcp.json` | Inline credential-looking env values, broad filesystem roots, npx/bunx auto-install signal |

Malformed JSON/TOML, duplicate JSON keys, invalid structures, oversized data, linked paths and unreadable files produce high-severity findings. A missing allowlisted file is *out of scope*, not clean evidence for that subsystem; no supported file produces `REVIEW_REQUIRED`.

**Security boundaries:** No user secrets are echoed. Files are inspected up to 128 KiB each and 512 KiB total. Input is never executed or sent to a model or network. `HOST_CONFIG...` findings are advisory policy decisions; no Codex Desktop or Claude hook interception is registered. An `approval_policy` setting in a file does **not** prove the actual client honored it. Static flags are a conservative subset and can have false positives or miss threats; code execution and permissions still require host control.

## Differentiation, provenance and rollback

This complements (not replaces) `external_skill_gate.py`'s existing third-party Skill checks, Cisco MCP declaration scans (#359) and SkillSpector (#200). Original research comparison: [AgentShield source `b0891303bdcd6037376a94263d45cfd2ff3dfb98`](https://github.com/affaan-m/agentshield/tree/b0891303bdcd6037376a94263d45cfd2ff3dfb98), license MIT. The implementation is Toolkit-authored Python; no original TypeScript, package dependency, binary, or model inference is copied. Upstream source review is not live AgentShield execution.

Remove/rollback only this opt-in code revision via normal Git history; no files or permissions are changed by the audit. The original Skill candidate scan mode and its output remain supported. Native Windows Codex Desktop security enforcement, upstream parity and complete Host AgentShield-grade coverage remain **NOT_VERIFIED**. Issue #432 stays open pending remaining security controls and accepted real-client evidence.
