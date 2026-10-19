# Рубрика оценки качества

Оценивайте каждый навык отдельно; неизвестное не равно пройденной проверке.

- **Портируемость:** отсутствуют необъявленные требования к runtime, ветке, ОС, провайдеру и домену.
- **Контракт:** явные цель, условия применения, границы и ожидаемый результат.
- **Формат:** валидный YAML frontmatter и локальные ссылки.
- **Безопасность:** нет автоматического запуска непроверенного кода или необоснованного расширения полномочий.
- **Проверяемость:** исполнимые команды, тестовые сценарии, фактическое evidence.
- **Происхождение:** источники, лицензии, версия и ограничения сторонних компонентов указаны.
- **Согласованность:** нет противоречий проектным AGENTS.md и другим активным навыкам.

Per-skill numeric static diagnostics (file-byte footprint, Markdown and frontmatter checks, portability-contract metadata, deterministic repeat, pinned baseline diffs) are available through `python scripts/skill_quality_metrics.py --summary --check-repeat`. No unified skill score or measured AI task success is inferred. See [measurement methodology](SKILL_QUALITY_METRICS.md). Empirical model effectiveness remains `NOT_MEASURED` until separate Issue #11 trials.

Offline quality gate: `python scripts/validate_quality.py` checks declared skill/role inventories, links and anchors across repository Markdown (including templates and recipes), path containment, profiles and explicit mutually exclusive workflows in `docs/QUALITY_RULES.json`. It does not infer semantic contradictions from keywords. `BLOCKER` findings break CI; `WARNING`/`INFO` denote manual observations outside the required gate. See [audit](SKILLS_QUALITY_AUDIT.md).

Статусы: `verified` (проверено статически/тестом), `manual` (требует эксперта), `not-applicable`, `unknown`, `failed`. Не называйте пакет полностью проверенным по итогам одного статического анализа.

Provenance statuses (`verified`, `documented`, `requires_owner_review`, `restricted`, `unknown`, `not_applicable`) are **separate** from quality-gate statuses. Both `python scripts/validate_provenance.py --mode inventory` and `--mode release` run as required CI steps on Linux and Windows. A separate Ubuntu 3.12 step validates a clean, exported Git source archive using archive-mode SHA256 verification plus the same release gate. Release mode also enforces the exact immutable owner-approved source snapshots and rejects restricted material, missing owner approvals and reclassification attempts. Neither certifies title, permissions or legal compliance. See [PROVENANCE_AUDIT.md](PROVENANCE_AUDIT.md).

For new and substantially revised skills, see [Toolkit Skill Quality v2](SKILL_QUALITY_V2.md). Semantic trigger and output acceptance criteria use a manual review checklist, not compulsory headings. Existing skills remain valid without new optional sections; source-only metrics never prove runtime activation.

## Static quality and publication hygiene (Issue #48)

Baseline at `main` `6aefd4a344d61bab9cea93846630fbff8b8d2a74`:
55 Python files (including bundled third-party code), 2 GitHub Actions workflows,
`requirements-dev.txt` with PyYAML only; 3/3 matrix jobs successful in
[run #39317526236](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/39317526236)
(79 seconds overall, 19 October 2026). The existing checks already cover
pack structure, official skills-ref, inventories, links, checksums, provenance,
distribution, release archive, offline compatibility and unit tests.

| Option | Existing alternative | Verified gap / synthetic counterexample | Decision and maintenance |
| --- | --- | --- | --- |
| Ruff 0.17.1 | unittest, Python parse on import | Undefined name inside an unexecuted function is not rejected by the existing quality gates; CI runs an F821 negative control | **ADOPT narrowly**: F821/F822/F823/E9 for scripts and tests, only in Ubuntu 3.12; one pinned optional pip package, no formatting |
| actionlint 1.7.12 | PyYAML, workflow-specific contract tests | A syntactically valid workflow with `needs: [missing_job]` passes basic YAML parsing; actionlint rejects it | **ADOPT**: one checksum-verified official linux-amd64 binary in the existing Ubuntu 3.12 job; no new action or job |
| Gitleaks / detect-secrets | Built-in high-confidence scanner | Broad heuristic/entropy and Git-history scanning could catch more formats but also requires triage and baseline maintenance; no demonstrated net improvement for this curated package | **REJECT for required CI**, revisit after a concrete missed real-world class or a measured pilot; no second scanner |
| Built-in public scanner | Personal/project-specific regexes, type checks | Unicode read errors and >2 MB text were silently skipped; opaque binary files were not rejected; personalized patterns were not reusable | **REFINE**: fail-closed errors, binary/size checks, generic credential filename rules, redacted line-number diagnostics; only standard library |

The table distinguishes demonstrated synthetic misses from hypotheses about
external scanners. The accepted correctness rules and workflow validation passed the first
Ubuntu 3.12 PR pilot; the broader Ruff statistics are informational, not a
new required formatting policy. Exact-head acceptance still requires all
three matrix checks and the official skills-ref gate. Tool binaries are NOT vendored into the package.
Official sources: [Ruff](https://docs.astral.sh/ruff/),
[actionlint](https://github.com/rhysd/actionlint), and
[detect-secrets](https://github.com/Yelp/detect-secrets).

**Local checks**, from the repository root:

```shell
python scripts/check_public_package.py
python -m unittest discover -s tests -p test_security_scanner.py -v
python -m pip install ruff==0.17.1
ruff check --isolated --target-version py312 --select F821,F822,F823,E9 scripts tests
# Optional: install the official actionlint 1.7.12 binary for your OS,
# verify its release checksum, then:
actionlint -no-color -shellcheck= -pyflakes=
```

For actionlint on Linux CI, the SHA256 for official
`actionlint_1.7.12_linux_amd64.tar.gz` is pinned in `.github/workflows/validate.yml`.
It is downloaded over HTTPS, verified **before extraction/execution**, and
used only for syntax, expressions, workflow dependency and action-schema checks.
ShellCheck and Pyflakes integration are intentionally disabled to avoid an
additional unpinned runtime; they may be assessed separately.

The scanner walks within the supplied root, including **tracked and untracked**
files, without following symlinks/junctions or reading environment variables.
It excludes only documented local build/cache directories; the separate
Git-index checksum gate detects newly tracked paths, and source archive mode
detects unlisted extracted files. Only the two existing branding PNGs are
allowlisted as binary. Forbidden files, unreadable text, unexpected binary and
oversized unknown files fail closed. Diagnostics emit rule, relative path,
and line when applicable, **never matched values**. Treat any finding as a
blocking review item; do not add broad suppression rules to hide it.

**Limits:** Pattern checks cannot certify that a repository has no secrets or
personal data. They do not analyze historical commits, encrypted/obfuscated
secrets, arbitrary proprietary text, binary steganography, new token formats,
legitimate permissions, model runtime behavior or external network behavior.
Manual diff review and the immutable provenance owner gate remain mandatory.
The scanner does not execute inspected files or send their contents externally;
optional installers used by CI require network access to official tool sources.
