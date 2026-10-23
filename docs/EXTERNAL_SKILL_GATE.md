# Offline third-party Skill gate (Issue #200)

[Русская версия](ru/EXTERNAL_SKILL_GATE.md) | [Existing external skill review](../.agents/skills/external-skill-review/SKILL.md) | [Adoption policy](EXTERNAL_METHODS_ADOPTION.md)

The `scripts/external_skill_gate.py` command provides a **small, offline, read-only, fail-closed preflight** for a locally available third-party Agent Skill candidate. It does **not** fetch external sources, attest GitHub ownership, prove a license grant, analyze all possible prompt injections, execute scripts or grant installation permission. It complements, rather than replaces, the human `external-skill-review` process.

## Inputs

The operator must supply a local candidate directory and an **independent manifest** stored outside the candidate directory, including an HTTPS GitHub repository URL, full 40-character commit SHA, claimed SPDX license and SHA-256 digests for **all candidate files**. The independently verified upstream revision and file hashes must be obtained through an authorized source inspection; metadata supplied by an untrusted candidate is **not provenance evidence**.

Example schema (illustrative placeholder digest, not a real verified source):

```json
{
  "schema_version": 1,
  "candidate_id": "example-skill",
  "source_url": "https://github.com/example/example-skill",
  "source_revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "license": "MIT",
  "files": {
    "SKILL.md": "0000000000000000000000000000000000000000000000000000000000000000"
  }
}
```

```bash
python scripts/external_skill_gate.py \
  --candidate-dir /path/to/isolated/example-skill \
  --manifest /path/to/review-manifest.json
python -m unittest tests.test_external_skill_gate -v
```

Replace all placeholders with independently checked values before use. There is no automatic installation, no Agensi account dependency and no paid API.


## Execution/reference threat review (real pinned source, no import)

Read-only source inspection: [pbakaus/impeccable at 69c34b7](https://github.com/pbakaus/impeccable/tree/69c34b7c3d6267dfd783dacb9f58f04522656b2b), file `.agents/skills/impeccable/SKILL.md`. GitHub repository metadata declares Apache-2.0 and a root LICENSE exists. **These are licensing claims, not independent legal approval.** The skill text refers to a bundled launcher, a binary that may be fetched on first invocation, and project hooks. **None of these were executed or installed.**

| Threat / uncertainty | Scanner evidence | Gate response | Remaining manual work |
|---|---|---|---|
| Skill text requests running `scripts/...`, `npx` or a launcher/download | `EXECUTION_OR_DOWNLOAD_REFERENCE` | `NEEDS_MANUAL_REVIEW`, not installation approval | Verify exact binary digest, source, network domains, startup behavior and cost |
| Text links to `reference/*.md` missing from candidate inventory | `REFERENCED_FILE_NOT_INCLUDED` | `NEEDS_MANUAL_REVIEW` | Obtain independently pinned complete reference inventory |
| Local relative Markdown reference contains `..` traversal | `UNSAFE_SKILL_REFERENCE` | `REJECT` | Reject unsafe package and investigate input provenance |
| References exist but script source is not present | Static detector is incomplete | Never authorizes installation | Independently inspect dependencies, hooks and permitted file writes |

The added synthetic regression reproduces the **risk pattern**, not the complete third-party package. A positive static result still cannot attest artifact provenance, license scope or actual runtime behavior. Detection uses bounded heuristics and can produce false positives/negatives. Full downstream acceptance requires an isolated, owner-approved review without downloading or launching binaries automatically.


## Supply-chain adoption dossier (Issue #195)

An optional **operator-owned** JSON file outside the untrusted candidate adds structured task, overlap, permissions, dependency, cost and removal claims. It does not authorize downloading, activation or publication:

```json
{
  "schema_version": 1,
  "task_goals": ["audit-api-contracts"],
  "existing_skill_overlap": ["qa-strategy"],
  "requested_permissions": ["project_read"],
  "dependencies": [],
  "cost_class": "NO_PAID_API_CLAIMED",
  "removal_plan": "REMOVE_MANAGED_FILES"
}
```

```bash
python scripts/external_skill_gate.py --candidate-dir /isolated/candidate \
  --manifest /isolated/review-manifest.json \
  --review-context /isolated/operator-review.json
```

The `adoption_dossier` in the machine JSON output records source, complete commit pin and license **claims**, task goals, proposed overlap with existing skills, requested privileges, dependencies, cost category, removal plan and security findings. The context is strictly bounded (16 KiB), validates controlled identifiers and enumerated permissions, and must be independent of the candidate directory. Invalid input is `REJECT`; declared paid API use is `REJECT`; risky privileges, declared overlap, unverified cost or absent removal plan require manual review.

A clean report is `ALLOW_FOR_REVIEW`, **never safe-to-publish**. Operator declarations do not independently attest the upstream revision, license grant, completeness, cost, absence of injection, or removal feasibility. `publication_gate=BLOCKED_PENDING_INDEPENDENT_PROVENANCE_AND_OWNER_APPROVAL` always applies to this scanner; final release still requires the separate `validate_provenance.py --mode release` owner and source hash gates. Do not load this JSON as agent instructions or execute commands from it.

## Verdicts and limits

| Decision | Reason | Next action |
|---|---|---|
| `REJECT` (exit 2) | Invalid pin/manifest, unsafe paths/symlinks, missing/extra file, checksum mismatch or size limits | Reject input; no installation |
| `NEEDS_MANUAL_REVIEW` (exit 1) | Unsupported/unknown license, scripts/hooks, binary/non-UTF8 material, suspicious instruction patterns or missing frontmatter | Independent manual code, license and permission review |
| `ALLOW_FOR_REVIEW` (exit 0) | Only supported superficial checks passed | Human review remains mandatory; **not** safe-to-install |

Limits: 80 files, 512 KiB per file, 2 MiB aggregate, 32 KiB manifest. The script never executes imported code or follows symlinks. Suspicious-pattern checks are **incomplete heuristics** with false negatives and positives. Even a clean result does not prove absence of injected instructions, malicious behavior, secret exfiltration, hidden binary payloads or source substitution. No result authorizes external network calls, shell access, secrets, production changes or global skill installation.

Next steps: link this offline preflight to Toolkit #199 discovery **only after** scoped candidate acceptance and client-specific install review. Continue to use Skill Manager's preview/apply boundaries, source pins and #190 client compatibility checks. Do not move external skills into Hermes resident runtime.
