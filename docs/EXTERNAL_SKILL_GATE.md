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

## Verdicts and limits

| Decision | Reason | Next action |
|---|---|---|
| `REJECT` (exit 2) | Invalid pin/manifest, unsafe paths/symlinks, missing/extra file, checksum mismatch or size limits | Reject input; no installation |
| `NEEDS_MANUAL_REVIEW` (exit 1) | Unsupported/unknown license, scripts/hooks, binary/non-UTF8 material, suspicious instruction patterns or missing frontmatter | Independent manual code, license and permission review |
| `ALLOW_FOR_REVIEW` (exit 0) | Only supported superficial checks passed | Human review remains mandatory; **not** safe-to-install |

Limits: 80 files, 512 KiB per file, 2 MiB aggregate, 32 KiB manifest. The script never executes imported code or follows symlinks. Suspicious-pattern checks are **incomplete heuristics** with false negatives and positives. Even a clean result does not prove absence of injected instructions, malicious behavior, secret exfiltration, hidden binary payloads or source substitution. No result authorizes external network calls, shell access, secrets, production changes or global skill installation.

Next steps: link this offline preflight to Toolkit #199 discovery **only after** scoped candidate acceptance and client-specific install review. Continue to use Skill Manager's preview/apply boundaries, source pins and #190 client compatibility checks. Do not move external skills into Hermes resident runtime.
