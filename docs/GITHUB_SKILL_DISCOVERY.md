# Opt-in GitHub Skill discovery — Issue #199

[Русский](ru/GITHUB_SKILL_DISCOVERY.md) · [Offline candidate review](EXTERNAL_SKILL_CANDIDATE_REVIEW.md) · [Security Gate](EXTERNAL_SKILL_GATE.md)

`scripts/github_skill_discovery.py` is an optional source-metadata lookup, **not** a trusted skill directory. Without `--discover`, no requests are made. With explicit `--discover`, it makes anonymous, time-limited HTTPS requests to the fixed `api.github.com` host, only for repository URLs independently pinned by the operator to exact 40-character commit hashes.

```bash
# Safe default: local diagnostic; no network
python scripts/github_skill_discovery.py --query "qa-strategy"

# Explicit public metadata lookup; replace the placeholders with verified values
python scripts/github_skill_discovery.py --query "backend" --discover \
  --allow-repo "https://github.com/approved-owner/public-repo@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
```

The second example uses an illustrative pin, **not** a verified commit; it must be replaced. The command validates the repository commit SHA via the lightweight Git endpoint `/repos/{owner}/{repo}/git/commits/{sha}` (not the potentially large commit-diff endpoint), obtains its tree hash, and reads only the bounded Git tree metadata (`git/trees/{tree-sha}?recursive=1`). It searches for `SKILL.md` paths, including hidden development folders such as `.agents/skills/`, using deterministic lexical tokens (including short terms such as `QA` and `UI`); at most three repositories and 20 matching entries are returned. A missing match is **not** proof that a useful skill does not exist. Truncated, malformed or oversized results, changed pins, unexpected redirects, API errors and duplicate repositories fail closed. API rate limits can deny lookup.

Returned paths and revisions are untrusted *discovery hints* only. `license=NOT_VERIFIED`, `content=NOT_DOWNLOADED`, `remote_security_gate=NOT_RUN`, `installation=NOT_AUTHORIZED`. The tool never fetches `SKILL.md`, doesn't read any tokens/cookies, uses no paid service, doesn't modify Codex, or enable a resident Hermes agent. There is no implicit fallback to a branch, unpinned default or unknown provider. GitHub tree metadata and the commit endpoint still do not prove licensing, owner endorsement or suitability.

**Human next step:** separately inspect the selected pinned repository and license, obtain an isolated candidate with independently verified hashes, then run [the offline candidate review](EXTERNAL_SKILL_CANDIDATE_REVIEW.md) with an explicit allowlisted URL. A static `ALLOW_FOR_REVIEW` is **not** permission to install.

```bash
python -m unittest tests.test_github_skill_discovery -v
python scripts/validate_pack.py
python scripts/verify_checksums.py
```

CI uses mock responses only; no live GitHub calls or any personal Codex/ChatGPT MCP activation is represented as tested. The direct network path and real-client usability still require separate explicitly scoped acceptance.
