# Run locally ONLY after reviewing contents; requires gh and git authenticated for the owner.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
# Prefer the Windows Python Launcher when present; `python` may be a Store alias.
$pythonCommand = 'python'
$pythonArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = 'py'
    $pythonArgs = @('-3')
}
& $pythonCommand @pythonArgs scripts/check_public_package.py
if ($LASTEXITCODE -ne 0) { throw "Private-file check failed" }
& $pythonCommand @pythonArgs scripts/validate_pack.py
if ($LASTEXITCODE -ne 0) { throw "Validation failed" }
& $pythonCommand @pythonArgs -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
gh auth status
if ($LASTEXITCODE -ne 0) { throw "GitHub CLI not authorized" }
if (-not (Test-Path .git)) { git init -b main }
git add .
git status --short
Write-Host "Before publication, confirm your rights to publish QA work-derived adaptations (see docs/QA_PORTABILITY.md)."
Write-Host "Review the staged changes before confirming the commit and public publication."
$confirm = Read-Host "Type PUBLISH to create a PUBLIC GitHub repository and push these files"
if ($confirm -cne 'PUBLISH') { throw "Publication cancelled" }
git commit -m "Initial public AI Development Toolkit v5.2.0"
if ($LASTEXITCODE -ne 0) { throw "Commit failed" }
gh repo create ai-development-toolkit --public --source . --remote origin --push --description "Portable agent skills, QA workflows, specialist roles and tools for reliable AI-assisted development"
if ($LASTEXITCODE -ne 0) { throw "Repository create/push failed: inspect git status and gh auth" }
# Presentation metadata is optional; a failure must not misrepresent successful git publication.
gh repo edit MikeMoore1337/ai-development-toolkit --add-topic ai-agents,agent-skills,ai-development,codex,claude-code,developer-tools,qa-automation,software-testing,prompt-engineering,agentic-workflows
if ($LASTEXITCODE -ne 0) { Write-Warning "Repository published, but topics could not be set automatically. See docs/GITHUB_SETUP.md." }
Write-Host "Next step: upload assets/branding/social-preview.png via GitHub Settings > General > Social preview."

