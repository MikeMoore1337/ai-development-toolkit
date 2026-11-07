# Toolkit native eval capsules / receipts (#437)

Toolkit bundles **18 byte-identical original files** from `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, solely as an **optional offline evidence library** under `third_party/ecc-v2.2.3/eval-harness/`. This is source incorporated into Toolkit, **not an external ECC installation, plugin, CLI, MCP, agent runtime or sidecar**. The MIT root license is retained at `third_party/ecc-v2.2.3/LICENSE`; exact original Git blobs and SHA-256 are pinned in `SOURCE_SNAPSHOT.json`. Upstream source/tests are unmodified; Toolkit's own `scripts/skill_eval.py` remains the scoring authority.

## What is available

- Canonical JSON envelopes, default-deny payload fields, credential canaries and five event lineages
- Local append-only, SHA-256 predecessor-linked journal, integrity verify and reproducible projection
- Offline artifact-/journal-/gate-digest receipts, where verification rejects forged or stale evidence
- Content-addressed, deterministic fixture replay, with **no live tool implementation calls**; SE3/SE4 effects refused
- Static variant inspection and explicit **candidate execution refusal** (`gate.isolation_required`)

An appended hash chain proves detected changes to the supplied journal; it is **not independently witnessed** and cannot prove that an operator did not rewrite all files. A syntactically valid receipt is not verified agent success or owner permission. No actual model outputs, CI verdicts, deployment rights or real skill effectiveness are inferred.

### Explicit CLI (Node.js required, no npm install)

From a trusted Toolkit checkout, with a capsule created by a separately authorized local recorder:

```text
node scripts/native_eval_capsules.js capsule verify /local/capsule
node scripts/native_eval_capsules.js capsule project /local/capsule
node scripts/native_eval_capsules.js receipt build /local/capsule --artifact /local/approved/artifact
node scripts/native_eval_capsules.js receipt verify /local/receipt.json /local/capsule --artifact /local/approved/artifact
```

`verify` operations read only. `project` and `receipt build` **explicitly write `projection.json`** inside the selected capsule; do not call on untrusted, privileged or production paths. Only invoke on authorized disposable or bounded local evidence. The wrapper does **not** expose `example`, candidate execution, automatic recording, background collectors, tool hooks, project edits or network execution. The bundled library API also requires explicit trusted caller permission before any record-mode invocation; replay never runs live implementations. Do not supply secrets or raw conversation material.

**Fail-closed native receipt policy (#437):** The Toolkit CLI refuses receipt fields it does not recognize, sensitive identity/receipt strings caught by the bundled credential canaries, and purported `gate_verdict`, `gate_receipt_digest` or detached `signature` values. There is no OS-isolated gate or trusted signature verifier in this CLI, so even a self-consistent, rehashed `PASS` cannot be accepted as attestation. The CLI also refuses symbolic links in input paths and capsule metadata, journal and projection files. Sensitive capsule identities are refused before the `project`/`receipt build` producer writes. These are bounded format and known-secret checks, **not general personal-data detection**, proof of origin, or prevention of complete hash-consistent replacement; use pseudonymous identifiers and a separate trusted witness when authenticity matters.

**Distinct run binding:** With skill_eval.py --verify-native-receipts, every paired run requires a distinct receipt file and capsule directory, and a distinct hash of its verified run_id/capsule_id. Reusing or copying one capsule into multiple baseline/candidate records is rejected even when all hashes match. This hash is a uniqueness marker, not a signed witness or proof of model quality.

## Reproducible offline validation

`tests/test_native_ecc_eval_capsules.py` validates each upstream Git blob and SHA256, runs five unmodified Node.js source suites where Node is present, and checks Toolkit-specific forged receipts, mutated journal, missing fixtures, replay SE4 denial, CLI gating and no unwanted writes. Passing these tests proves **source and local deterministic behavior only**, not verified Codex Desktop activation. With Node absent, the source integrity test still runs but runtime evaluation is **NOT_VERIFIED**, not PASS.

**No additional cost or automatic activation.** No Codex CLI, Claude CLI, external ECC component or paid API is required. For a rollback, remove the optional files and wrapper in an ordinary reviewed PR; no install hooks, global state or persistent services were changed. A new versioned Toolkit release still requires its independent owner-controlled release gates.

