# Provenance, licenses and distribution audit (2026-10-19)

**Scope:** source tree at `main@b81cd6dc8c60c2466242928e37b237de25eddd12`, plus the provenance controls introduced by Issue #28. This document is **not legal advice or an authorization to publish**.

## Coverage and classification

`provenance/skills.json` lists **163 distribution units**: **51 skills** (23 core/extension and 27 QA plus one Make Feature), 16 roles, QA recipes, standalone scripts, profiles, branding assets, test sources, docs, workflows and repository metadata. A skill's directory is a single unit that includes its SKILL.md, Python helpers, reference Markdown, templates, notices and tests. All other published files are individually listed. There are no bundled third-party runtime binaries. `optional-original-skills` contains only an empty placeholder.

Initial review classifications: **0 verified, 118 documented, 42 requires_owner_review, 2 unknown, 0 restricted, 1 not_applicable**. `documented` is not a legal confirmation. Existing claims about authorship and license are attributed to their corresponding documents; they have not been independently authenticated. File-level cross-checks and similarity assessment against privately supplied source are unavailable.

## Owner review record reference (2026-10-19)

The owner supplied external review record ID **`ID1337`** and states supporting rights confirmations are retained privately. This identifier is non-secret tracking metadata only; this audit has **not** received the record's findings, the applicable files/revisions, the reviewed rights grant or restrictions. The relevant `owner_gate` statuses and next-release `BLOCKED` outcome remain unchanged pending component-scoped confirmation. No private evidence is included.

## Make Feature - OWNER GATE

- Exact shipped scope: `extensions/make-feature/skills/make-feature/` (SKILL.md, scripts, references, templates, tests, license, installation/portability metadata).
- The shipped LICENSE says `MIT`, Copyright (c) 2026 Artemiy Miller, and SKILL.md claims the same license. SOURCES.md identifies the state helper's earlier `make-it-real` revision `0282a33ccbe2c149dc4a9301b7d2f25152ff3bf1`. **That revision is NOT a pinned commit of the bundled Make Feature 0.3.0 tree.**
- `docs/PUBLICATION_POLICY.md` and `PORTABILITY_NOTES.md` describe a *different*, personally issued license that reportedly prohibits redistribution and an additional permission reportedly granted later. The later authorization is not in the public evidence set and was **not independently verified**.
- Therefore the rights applicable to the exact bundled files are unresolved, despite an MIT label and prior public v5.3/v5.4 tags. Status: `requires_owner_review`; `distribution=owner_gate`; next-release preflight **BLOCKED**.
- No public personal license documents, emails, addresses, names of recipients, tokens, or private evidence are collected. The owner should verify the version/files/scope of any later authorization privately with the rightsholder; record a *non-secret* review reference, reviewing person/date and applicable conditions. Alternatively approve a **separate, reversible** exclusion before preparing a new release. No automatic removal or rewriting here.

## QA Engineering Pack - OWNER GATE

`extensions/qa/SOURCE_MAPPING.md` documents 27 portable skills and 11 QA roles, with three QA recipes also present. The owner describes adaptation of methodology from a work project. Universal testing strategies are not necessarily protectable expression, but adapted original prose/code could be. Without underlying source comparison or relevant employment/IP obligations it is incorrect to conclude either infringement or unrestricted publication. The QA pack is recorded as `adapted`, `NOASSERTION` for underlying-source license, `requires_owner_review`; the mapping document remains published while the upstream archive does not. Publication requires an owner-confirmed review of rights and confidentiality under applicable agreements.

## Core, Clear Voice, roles, scripts, templates, assets

- Core skills and reference roles are declared Toolkit work or original expression inspired by external ideas. `docs/SOURCE_EVALUATION.md` contains third-party *methodology* references and some reviewed upstream SHA values; those commits are not proofs of origin for the actual Toolkit text. No external binary/hook runtime is bundled. All recorded as `documented`, **not** independently verified ownership.
- Clear Voice declares its own MIT license and links to human-writing (codemistake) and humanizer (blader). The `SOURCES.md`, `THIRD_PARTY_NOTICES.md`, and `licenses/*-LICENSE` files are included; profiles, examples, and offline synthetic checks are within its subtree. The two bundled third-party MIT notices have matching upstream Git blob SHA values at checked source commits: human-writing `3d06941d99d78bb495d11a98f6cd30eeec7a701b` (LICENSE blob `2068fb4d84b6212043e26e2ac6f325801e2fc944`) and humanizer `8c307f367c91bd974002f10f2be2965d642c13df` (LICENSE blob `625297fb778f32eb39d3a5b97e3e3b611b7304d6`). This verifies those license notice bytes at those commits, NOT whether any protected expressions were copied. A manual content-similarity check still remains necessary. Status `documented`. Do not conflate reused editorial *ideas* with copied copyrighted *expression*.
- Main scripts, tests, docs, workflow files, generic templates and role instructions are declared Toolkit-maintained; each individual path is inventoried. The registry does not assert copyright originality is proven.
- The two branding PNGs have no independent creation/asset-rights record in the checked documentation: `unknown` and `owner_gate`, pending owner confirmation of generation/source/licensing.
- There is no evidence in this audit sufficient to label any item `verified`. The recorded `restricted=0` does **not** establish that no restriction exists; it means no verified current blocking license condition has been conclusively attributed to a specific published copy.

## Release and technical controls

Run `python scripts/validate_provenance.py --mode inventory --report /path/to/report.json` for inventory consistency (CI). Run `python scripts/validate_provenance.py --mode release` for the mandatory **prepublication gate** on the exact proposed release tree. The second command rejects `owner_gate`/`excluded`, `restricted`, `unknown`, `requires_owner_review`. It currently **fails intentionally**, pending owner decisions. CI inventory PASS is **not** permission to release.

The release workflow also runs gate checks on tag pushes, post-publication events, and manual archive validation, but **GitHub release:published jobs run after publishing**; they cannot retroactively prevent an owner/API from creating a release. Tag-push checks and the documented mandatory owner approval must occur *before* publication; branch protection/release permission configuration remains a separate owner-admin control. The checksums inventory verifies bytes and completeness, not licensing. Existing released tags and source archives are deliberately unchanged.

The offline validator checks inventory drift, path containment, allowed statuses/types, source descriptions, claimed SPDX license fields, header conflicts, notices, revisions and false verified declarations. It does not authenticate license signatures, permissions, underlying employment contracts, code similarity, copyright or the identity of rightsholders.

## Onboarding new components

1. Identify the *actual files* to distribute and their author/source and whether code or protected text, not just ideas, was copied.
2. Link the corresponding upstream URL and immutable revision where available. Read license and copyright notices at that revision. For private material, use an opaque non-secret source reference instead of leaking it.
3. Record license using an applicable SPDX identifier or `NOASSERTION` when unresolved. Record required notices and the exact public evidence file.
4. Mark uncertain or restricted materials `owner_gate` or `excluded`. Never infer `verified` from a LICENSE, a public URL or an author's claim.
5. Run offline inventory tests, official skills-ref where relevant, checksums and release preflight. Escalate contradictory rights before publication, without inserting private proof into Git history.
6. Have the owner explicitly approve any permission-based status change or exclusion, and record non-secret references/date. Publishing a previous version is not approval for a future one.

**Pending owner decisions:** Make Feature authorization scoped to current 0.3.0 files, QA work-derived licensing/confidentiality obligations, and branding art chain of title. All are documented **BLOCKED for a new release** until resolved.
