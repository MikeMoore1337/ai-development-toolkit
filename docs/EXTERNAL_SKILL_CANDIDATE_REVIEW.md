# Offline candidate review: Toolkit #199 + #200

[Русская версия](ru/EXTERNAL_SKILL_CANDIDATE_REVIEW.md) | [Local skill coverage](SKILL_COVERAGE.md) | [Static Security Gate](EXTERNAL_SKILL_GATE.md)

This is **not** a marketplace, Skill Manager importer, trust certification or installation path. The offline CLI described below does not perform online search; a separately consented pinned metadata discovery route exists in personal MCP (#199). The command `scripts/skill_candidate_review.py` combines the existing Toolkit-local lexical coverage result with the existing external Skill Security Gate. A candidate must already be provided locally by an authorized operator. No network request, LLM, package manager, shell script or project mutation is made.

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

The offline wrapper itself performs **no online discovery**. The separate, explicitly consented personal MCP metadata search does not download Skill contents. This is an offline bridge for a human-presented allowlisted candidate, not an automated candidate source search. No direct import into Skill Manager; no auto-install or auto-update. Untrusted SKILL.md content is read as data for static patterns only. Static checks cannot prove safety, authorship or licensing. Do not use this command to inspect production secret directories. Recheck upstream sources in an approved separate procedure and use the read-only external candidate preview described below. The preview does **not** authorize an external apply; the existing install/apply path only accepts Toolkit-owned catalog skills.

```bash
python -m unittest tests.test_skill_candidate_review -v
python scripts/validate_pack.py
python scripts/verify_checksums.py
```

Source tests are not live Codex or ChatGPT plugin verification. Remaining work: independent provenance attestations, manual source/rights review, and live installed-client validation under #190. A source-only opt-in pinned metadata discovery exists in personal MCP v0.1.10.


## External candidate preview in the existing Skill Manager (#199)

An operator can examine a **separately provided, pinned, fully inventoried**
candidate on an **existing disposable target directory**, after using the
Security Gate. The candidate and its manifest must live outside both the target
project and each other. This action does not import the candidate into Toolkit.

```bash
python3.12 scripts/skill_manager.py external-preview \
  --target /isolated/existing-target \
  --candidate-dir /isolated/external-skill \
  --manifest /isolated/review-manifest.json
```

The command reuses the offline Security Gate and Skill Manager's bounded file
diff/ownership checks. Output lists file paths, added/changed/deleted status,
and SHA-256 digests, **never file contents**. Its outcomes are
`CANDIDATE_ONLY`, `NEEDS_MANUAL_REVIEW`, or a `REFUSED_*` code for invalid
metadata, unmanaged destination collision, or modified managed state.
`--apply`, `--skills`, `--profile` and `--from-layout` are forbidden for
this action. A rejected preview exits 2. Even `CANDIDATE_ONLY` means only
*eligible for additional human review*, not authorization to install.

Operator-declared license, GitHub URL, pinned commit and hashes are **not**
independently verified provenance. The static gate cannot establish safety.
No network, subprocesses, Codex, plugins, auto-install or project writes occur.
Any future external import would need a separate explicitly approved design,
implementation and acceptance; do not pass an external candidate through the
existing Toolkit-owned `install --apply` operation.

```bash
python3.12 -m unittest tests.test_external_skill_preview -v
```


## Optional NVIDIA SkillSpector static review (#358)

The original offline Security Gate and Skill Manager ownership/preview rules remain
unchanged. After independent source/manifest checks and explicit candidate consent,
you may request a **second** static scan in the same candidate-review command:

```bash
python scripts/skill_candidate_review.py --query "new specialization" \
  --review-external --scan-with-skillspector \
  --candidate-dir /isolated/candidate \
  --manifest /isolated/review-manifest.json \
  --allow-source https://github.com/approved-owner/approved-repo
```

Requires `uvx` (uv). The adapter runs `skillspector scan` from pinned
NVIDIA commit `d162d9b343e559be13df8ebba093df3bc9d58c90` with
`--no-llm --format json --fail-on-incomplete`, requesting JSON on stdout
(the secure `--output` file option is not portable to Windows). It passes
only a minimal allowlist of process environment variables, never API keys,
model/provider settings, HTTP proxy credentials or package index credentials.

**Network boundary:** this opt-in invocation can download pinned scanner
dependencies via uv and the upstream scanner may query OSV.dev using dependency
coordinates. It is **not** an offline operation; omit the flag to retain the
previous fully offline workflow. No paid API or Codex CLI is required. Scan
only a separate disposable candidate tree without secrets.

The result includes `skillspector.status`: `NOT_RUN`, `PASS`,
`REVIEW_REQUIRED` or `BLOCKED`. Missing scanner, malformed/incomplete report,
unexpected LLM usage, unsupported result schema, timeout or scan failure all
fail closed as `BLOCKED`. A scanner PASS is only an **advisory input**:
the outer candidate decision remains `MANUAL_REVIEW_REQUIRED`, never automatic
install or `--apply`. `BLOCKED` becomes outer `REJECT`.

Static patterns are not a comprehensive semantic audit, especially for Russian
or mixed-language instructions. Manually examine high-risk instructions,
permissions, references and scripts regardless of scanner score. The untrusted
candidate never gets a shell execution path or access to the internal Skill
Manager installer. `external-preview` is still a read-only diff, not a
separate approval path and not evidence that SkillSpector ran.

```bash
python -m unittest tests.test_skillspector_adapter -v
```

Synthetic tests verify the adapter and negative outcomes; they do **not**
establish that a live upstream scan has completed on a particular machine.
