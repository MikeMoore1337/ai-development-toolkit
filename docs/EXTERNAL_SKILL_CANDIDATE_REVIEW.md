# Offline candidate review: Toolkit #199 + #200

[Русская версия](ru/EXTERNAL_SKILL_CANDIDATE_REVIEW.md) | [Local skill coverage](SKILL_COVERAGE.md) | [Static Security Gate](EXTERNAL_SKILL_GATE.md)

This is **not** a marketplace, online search, Skill Manager importer, trust certification or installation path. The command `scripts/skill_candidate_review.py` combines the existing Toolkit-local lexical coverage result with the existing external Skill Security Gate. A candidate must already be provided locally by an authorized operator. No network request, LLM, package manager, shell script or project mutation is made.

Default read-only task check (no opt-in, never inspects any external directory):

```bash
python scripts/skill_candidate_review.py --query "qa-strategy"
```

Optional **manual** review of one previously inspected candidate:

```bash
python scripts/skill_candidate_review.py --query "new specialization" \
  --review-external \
  --candidate-dir /isolated/candidate \
  --manifest /isolated/review-manifest.json \
  --allow-source https://github.com/approved-owner/approved-repo
```

The manifest must be outside the candidate tree. The exact allowed repository is supplied separately and explicitly; it is not inferred from candidate-supplied text. The manifest declares an HTTPS GitHub repository, a complete pinned SHA-1 commit ID, a claimed SPDX license and SHA-256 for all local candidate files. **The operator must independently verify upstream ownership, pinned revision, all file hashes, license grant and actual source contents.** Matching self-declared metadata is not independent provenance evidence.

The local result can be `FOUND_LOCAL` (readable exact skill name), `AMBIGUOUS` (lexical overlap) or `MISSING` (no lexical result, not proven semantic absence). Even if the scanner reports `ALLOW_FOR_REVIEW`, the wrapper returns `MANUAL_REVIEW_REQUIRED` with nonzero exit (1). `REJECT` exits 2. Only `LOCAL_ONLY` exits 0, which is **not** authorization to activate even a local skill in a client. The Security Gate can also return `NEEDS_MANUAL_REVIEW` or `REJECT`.

## Security and acceptance

There is **no online discovery** yet. This is an offline bridge for a human-presented allowlisted candidate, not an automated candidate source search. No direct import into Skill Manager; no auto-install or auto-update. Untrusted SKILL.md content is read as data for static patterns only. Static checks cannot prove safety, authorship or licensing. Do not use this command to inspect production secret directories. Recheck upstream sources in an approved separate procedure and use existing Skill Manager preview / explicit human apply after a security review.

```bash
python -m unittest tests.test_skill_candidate_review -v
python scripts/validate_pack.py
python scripts/verify_checksums.py
```

Source tests are not live Codex or ChatGPT plugin verification. Further work: an explicit, audited network discovery provider (if separately authorized), provenance attestations and cross-platform client validation under #190.
