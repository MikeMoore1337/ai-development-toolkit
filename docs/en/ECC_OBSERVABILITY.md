# Original ECC observability tools (Issue #434)

Toolkit can use the original [ECC engineering observability tools](https://github.com/affaan-m/ECC/tree/25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b) (v2.2.3, root MIT license), without vendoring or recreating their implementation.

## Capability boundaries

- `scripts/harness-audit.js` - deterministic repository infrastructure scorecard, **not** real runtime activation, secure execution or model effectiveness proof.
- `scripts/session-inspect.js --list-adapters` - discovers upstream adapters for Claude, dmux, Codex worktrees and OpenCode; this is a **registry inspection**, not a user-session read or evidence that any client adapter activated.
- `scripts/observability-readiness.js` - assesses *the ECC source tree itself*; the score is not evidence that Toolkit has a live HUD or resident service.
- `scripts/loop-status.js` may inspect Claude transcripts; it is **not** enabled or invoked by this opt-in integration, and requires separate authorization with synthetic source data.

[Optional GitHub Actions smoke](../../.github/workflows/ecc-observability.yml) checks out the original ECC source at immutable `25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, runs the first three original Node entry points on ephemeral Linux/Windows runners, checks real JSON schemas, flags unsupported adapters honestly and verifies tracked Toolkit files are unchanged. It never installs a second controller, clones the upstream implementation into Toolkit, starts an agent, calls an LLM or reads the operator's private transcripts. No paid API or Codex/Claude CLI is invoked. The workflow has only `contents:read`, with no publication rights.

For manual use in a **trusted, reviewed** ECC source checkout:

```sh
node scripts/harness-audit.js --root /path/to/project --format json
node scripts/session-inspect.js --list-adapters
node scripts/observability-readiness.js --format json --root /path/to/ECC
```

Do not target genuine sessions, user directories or run `loop-status` without a distinct owner authorization. Static scores and adapter listings must never be advertised as L4-L6 actual-client success. **Rollback:** disable/remove the workflow in a reviewed PR. The current GitHub-synthetic integration does not install a local client, create persistent telemetry or activate Windows Codex Desktop/Hermes - those remain `NOT_VERIFIED`.
