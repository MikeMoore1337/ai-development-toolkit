# Source neutrality and release archive gate

[Русская версия](ru/NEUTRALITY_RELEASE_GATE.md) | [Issue #396](https://github.com/MikeMoore1337/ai-development-toolkit/issues/396)

The public Toolkit ships general-purpose skills, not private user project names or personal policies. Git-tracked text sources are scanned by validate_public_docs_neutrality.py; ZIP sources and integration bundles are inspected by audit_source_archive.py without extracting, installing or executing their members.

## Checks

    python scripts/validate_public_docs_neutrality.py --repository example-owner/toolkit
    python -m unittest tests.test_public_docs_neutrality tests.test_audit_source_archive -v
    git archive --format=zip --output=source.zip HEAD
    python scripts/audit_source_archive.py --zip source.zip --repository example-owner/toolkit

Replace the example namespace with the actual repo. An optional literal private identifier list may be provided via --local-denylist /outside/repo/identifiers.txt; do not commit this file. The archive audit redacts member names containing these identifiers and never prints the matched literal itself.

The inspector checks UTF-8 source members (Markdown, Python, JSON, YAML, CSV and SVG), every file path, symlinks, duplicates, nesting, encrypted or damaged entries, excessive compression, and total size. Opaque binaries are counted separately. A PASS verdict means no forbidden patterns in inspected coverage, **not** proof that images and other opaque binaries are entirely private-data-free.

The original SHA256 source inventory, provenance and rights review remain mandatory. Source archive tests are not a client installation, production deployment, model call, L4/L5 activation or performance measurement.

## Use in your own environment

[Personal/project preferences](USER_SETTINGS.md) are not baked into the Toolkit release. [Client routes](CLIENT_POLICY_ROUTES.md) are optional guidance: different users may allow CLI or paid API in private local settings, but execution and spending need a separate client-specific consent and enforceable cost boundary. The default public example remains zero-spend.

The release gate requires exact-head PR CI, merge to protected main and independently checked post-merge CI. Original Git history is not rewritten. No additional marketplace or paid package publication is required to use Toolkit directly from its repository.
