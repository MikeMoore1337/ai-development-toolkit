# Skill quality metrics (Issue #38)

## Purpose and scope

Run **read-only offline source metrics** for each skill declared by MANIFEST.json. This is an
engineering diagnostic, not a subjective rating or a test of real model behavior.
The implementation reuses profile_metrics.skill_paths, validate_pack.validate_skill,
validate_quality.check_markdown and verify_client_compatibility.load_registry.
The independent pinned official skills-ref CLI remains enforced separately in CI.

Existing commands are complementary:

- scripts/profile_metrics.py: installed-byte estimates and overlapping manifest profiles.
- scripts/skill_eval.py / scripts/agent_eval_review.py: aggregate explicitly provided paired real-agent evidence;
  they do not generate real evaluations.
- scripts/validate_quality.py and scripts/validate_pack.py: package-wide static checks.
- scripts/validate_with_skills_ref.py: official pinned specification validation in a separate CI step.
- scripts/skill_quality_metrics.py: read-only **per-skill** file inventory, declared size,
  link/frontmatter diagnostics and comparative change indicators.

## Commands

Run at the actual repository checkout. No model download, agent runtime or external
service is used by this tool.

    python scripts/skill_quality_metrics.py --summary --check-repeat
    python scripts/skill_quality_metrics.py --skill feature-delivery --summary
    python scripts/skill_quality_metrics.py --json-report skill-quality.json --check-repeat

For historical comparison, make a **full-inventory** report from an exact clean
historical checkout, then use that report against a new exact checkout:

    git switch --detach <known-40-hex-historical-sha>
    python scripts/skill_quality_metrics.py --json-report /safe/path/baseline.json
    git switch <candidate-branch>
    python scripts/skill_quality_metrics.py --baseline /safe/path/baseline.json --json-report /safe/path/candidate.json

Both reports identify source_revision with a full Git commit SHA. A report from
a working tree with uncommitted changes still states Git HEAD, *not* a proof
that the working tree is clean: verify git status and the per-file SHA256 values
before accepting it as a trustworthy historical baseline. Use only
owner-checked baseline reports tied to the correct repository and commit.
There is no automatic fetch, Git checkout, file modification or remote upload.

Exit codes: 0 = all measured structural contracts PASS; 1 = confirmed FAIL
(including a newly introduced structural failure during comparison); 2 =
invalid configuration or report/I/O error. WARNING changes do not fail CI.

## Report schema v1

The JSON output is deterministic for an unchanged tree, Git revision and
tool version: sorted skill names, sorted paths, sorted findings, no timestamp,
no absolute local file paths and no random samples.

Root: schema_version, measurement_method, source_revision, scope, skill_count,
structural_pass, status, skills, limitations; optional comparison.

Each skill: skill_id, skill_path, schema_version, source_revision,
measurement_method, structural_validation, portability, context_footprint,
reproducibility, regression_indicators, empirical_effectiveness, findings,
frontmatter_sha256, file_inventory.

Every context_footprint measurement has value, unit, method, status.
The file inventory contains path, kind, bytes and SHA256 for each ordinary
file. No executable content is run and no file is modified.

| Metric | Unit / algorithm | Interpretation |
| --- | --- | --- |
| skill_md_bytes | bytes; exact byte count of root SKILL.md | File size, not model tokens |
| skill_md_lines | lines; Python str.splitlines() | Includes frontmatter |
| skill_md_words | whitespace_delimited_words; len(str.split()) | Whitespace-delimited strings, not linguistic words |
| metadata_bytes | bytes; UTF-8 frontmatter and YAML delimiters | Missing/invalid: NOT_MEASURED |
| reference_files | files; all regular files under references/ segments | Includes nested references |
| reference_bytes | bytes; sum of those file byte lengths | Not a model context charge |
| auxiliary_files | files; all files except root SKILL.md | Examples, scripts, configs, references |
| total_directory_bytes | bytes; sum of measured ordinary files | Byte footprint for the whole folder |
| main_file_share | fraction; SKILL.md bytes / total bytes | Undefined if no main content |
| model_tokens | tokens; NOT_MEASURED, value: null | No tokenizer or real model invoked |

Structural validity uses the existing local frontmatter parser and Markdown
link checks; the official skills-ref result is NOT_MEASURED **in this report**
unless evidence is obtained separately from its own required CI job. Markdown
checks are not a complete CommonMark/semantic/dependency audit.

Portability includes path/link containment and documented client compatibility
registry fields (supported layouts and **source-level** status). Live
activation, correctness on Windows/Linux, installed optional tools and runtime
dependencies are NOT_MEASURED. The registry is not proof of real skill loading
or task success. Directory symlinks, junctions, out-of-tree paths and linked
files produce FAIL without executing resources.

Reproducibility means deterministic local file scanning and serialisation,
not repeatability of AI behavior. The --check-repeat command compares two
serialised complete measurements on a single host. Linux and Windows CI can
independently repeat the source-only check, but per-client agent
reproducibility remains NOT_MEASURED.

## Comparison and regression indicators

A comparison accepts a full-inventory schema-v1 report with full 40-hex
source revision; unknown versions, malformed/linked paths, inconsistent
baseline record revisions and unpinned baselines are rejected.

- FAIL: newly introduced reproducible structural failures.
- WARNING: added/removed skills, changed instruction or metadata digest,
  changed/removed/added references, changed executable helper source,
  changed declared client compatibility and folder moves.
- PASS/info: positive or negative instruction-byte delta (unit: bytes);
  neither direction is by itself good or bad.
- NOT_MEASURED: real model behavior, actual token usage, measured safety,
  actual activation, cross-platform execution or acceptance delta.
- NOT_APPLICABLE: ratios requiring nonexistent input bytes.

No numeric regression probability is assigned. To confirm semantic/safety or
licensing implications of any WARNING, conduct scoped manual review subject
to the existing owner provenance gates. No mass rewrite is justified by large
file sizes or repeated strings alone.

### Minimal illustrative shape (not a benchmark)

    {
      "schema_version": 1,
      "measurement_method": "offline-source-metrics-v1",
      "source_revision": "<actual full commit SHA>",
      "scope": "all",
      "skill_count": 51,
      "structural_pass": "<derived at execution>",
      "status": "<PASS or FAIL>",
      "skills": [
        {
          "skill_id": "feature-delivery",
          "skill_path": ".agents/skills/feature-delivery",
          "schema_version": 1,
          "source_revision": "<actual full commit SHA>",
          "measurement_method": "offline-source-metrics-v1",
          "context_footprint": {
            "model_tokens": {
              "status": "NOT_MEASURED",
              "value": null,
              "unit": "tokens",
              "method": "no model tokenizer invoked"
            }
          }
        }
      ]
    }

The excerpt demonstrates the field hierarchy only; a real JSON report has
additional fields, actual file hashes and measurements. A comparison contains
baseline_revision, candidate_revision, changes[] and per-skill indicators.

## Verified source inventory, 2026-10-19

Repository tree analysis at commit
`283e2f42ea773d4007cf914aa8b255035b0f4160` (after registration of
the original tool and tests) found **51 declared SKILL.md files**, with
**72,288 total bytes**, a **966-byte median** and largest file
**clear-voice (11,698 bytes)**. This is a source-tree measurement,
not a per-model token observation.

| Skill | SKILL.md bytes | All folder bytes | Additional files |
| --- | ---: | ---: | ---: |
| clear-voice | 11,698 | 89,809 | 25 |
| make-feature | 8,240 | 138,574 | 27 |
| feature-delivery | 3,137 | 4,059 | 1 |
| skill-portability | 2,087 | 2,807 | 1 |

The larger directories carry licensed/snapshot-protected auxiliary material.
No source changes or optimization assumptions follow from that fact.

CI source-only validation on
[run 39246121679](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/39246121679)
confirmed all **51/51 static structural checks PASS** on Ubuntu 3.12,
with **51/51 official skills-ref** validated separately. A successful
Linux job does not establish per-client activation or execution.
The Windows short-path normalization regression found in synthetic tests
is addressed on the subsequent PR branch commit; consult final exact-HEAD
CI rather than treating this earlier run as final acceptance.

Prioritize manual review, not automatic rewrites, for the biggest
instruction surfaces (clear-voice, make-feature, feature-delivery)
and Python QA workflows (api-testing, pytest-test-design,
database-validation, test-data-management, failure-triage).
Source length is a review scheduling cue, not a quality score.

## Interpretation and follow-up

Review confirmed broken local links, invalid frontmatter, missing files and
unwanted linked paths before merging. Inspect unusually large skills like
clear-voice and make-feature for potential optional references without
changing pinned licensed/owner-snapshot files. Review feature-delivery
independently from make-feature and inspect QA Python profiles as declared
source contracts, not claims about Pytest/Playwright runtime compatibility.

Do not alter protected Make Feature 0.3.0, QA snapshot or branding sources
to optimise this report. Proposed owner-restricted changes require their own
approval and corresponding provenance inventory update.

The required CI job runs this analyzer across all declared skills on Linux
and Windows and preserves the machine report as a GitHub Actions artifact.
It also runs official skills-ref separately on the pinned Ubuntu job.
The analyzer itself never calls AI APIs, executes helpers or consults a
production VPS.

**Empirical effectiveness remains NOT_MEASURED**, including task acceptance
rate, introduced regressions, unsafe actions, token usage, execution duration,
skill activation observed and baseline-vs-candidate deltas, until Issue #11
can gather independent real-agent evidence with separate zero-cost approval.
