# GitHub repository setup

[Русская версия](ru/GITHUB_SETUP.md)

The Toolkit prepares the repository's **content**, not its GitHub account settings. The official [MikeMoore1337/ai-development-toolkit](https://github.com/MikeMoore1337/ai-development-toolkit) repository **already exists**. The following is a configuration reference for that repository or a separate authorized fork; do **not** recreate the official repository or treat the initial-publication script as a maintenance command.

## About (right sidebar)

- **Repository name:** `ai-development-toolkit`
- **Description:** `Portable agent skills, QA workflows, specialist roles and tools for reliable AI-assisted development.`
- **Website:** leave blank until an official project site exists
- **Topics** (suggested): `ai-agents`, `agent-skills`, `ai-development`, `codex`, `claude-code`, `developer-tools`, `qa-automation`, `software-testing`, `prompt-engineering`, `agentic-workflows`

## Appearance

1. **README**: `README.md` is automatically rendered on the repository homepage.
2. **Social preview**: open **Settings → General → Social preview → Edit** and upload `assets/branding/social-preview.png` (1280 × 640).
3. **Featured repository**: pin the repository from your GitHub profile's **Customize your pins** if desired.
4. **Releases**: create a GitHub Release only with an exact checked Git tag, required CI and separate owner rights approval for the *exact source artifact*. A ZIP filename, PR merge or README version is not evidence of a published GitHub Release. See [release procedure](RELEASE_PROCESS.md).
5. **Community health**: enable Issues and Discussions if you intend to maintain a community; the templates and contribution guidance are already in `.github`.
6. **Branch safeguards**: consider rulesets for PR reviews and required CI checks when branch rules are supported by your plan/repository settings.

## Recommended README presentation

- A restrained dark hero with a distinct mark and one-line positioning
- Concise badges with count-based information and actual CI status (when the repository exists)
- A task-oriented quick start, not a wall of prompts
- Separate skill catalog rather than 51 entries on the first screen
- Real links to reference docs, contribution process and security policy

## First publication of a **different, new** repository only

Only when you are deliberately creating a **new public repository** that does not already exist, on your authorized computer and after reviewing all rights and file contents:

```powershell
python scripts/check_public_package.py
python scripts/validate_pack.py
python -m unittest discover -s tests -v
.\scripts\publish_github.ps1
```

The initial-publication script asks for explicit confirmation, creates a public repository using an authenticated `gh` session and pushes `main`. It does not publish without that confirmation. **Never run this command against the existing official Toolkit repository as an update or release procedure.** Ordinary maintenance uses a protected `main`, reviewed PRs, required CI and the separately owner-approved [release process](RELEASE_PROCESS.md). Avoid committing previous ZIP archives, credentials, personal license documents or unrelated workspaces.

**Note:** GitHub repository metadata and uploaded social preview cannot be set by Markdown files alone. The prepared visual assets are included; use the GitHub UI for those settings.
