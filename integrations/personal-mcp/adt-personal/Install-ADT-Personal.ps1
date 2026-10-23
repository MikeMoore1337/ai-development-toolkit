# Installs the local read-only Toolkit MCP for the current Windows user.
# No writes to the active project or to the Toolkit checkout.
[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [string]$ToolkitPath = '',
    [switch]$Codex,
    [switch]$ClaudeCode,
    [switch]$McpOnly,
    [switch]$SkipGlobalInstructions
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($McpOnly -and ($Codex -or $ClaudeCode)) { throw '-McpOnly cannot be combined with client registration switches.' }
if (-not $Codex -and -not $ClaudeCode -and -not $McpOnly) { $Codex = $true }
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$server = Join-Path $packageRoot 'mcp\adt_mcp.py'
$discovery = Join-Path $packageRoot 'mcp\adt_discovery.py'
if (-not (Test-Path -LiteralPath $server -PathType Leaf) -or
    -not (Test-Path -LiteralPath $discovery -PathType Leaf)) {
    throw 'Incomplete MCP package: adt_mcp.py and adt_discovery.py are both required.'
}

# Preserve existing data and never place Toolkit in a workspace/project folder.
$homeRoot = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME 'AppData\Local' }
$source = if ($ToolkitPath) { (Resolve-Path -LiteralPath $ToolkitPath).Path } else { Join-Path $homeRoot 'ADT-Personal\toolkit-source' }
$source = [IO.Path]::GetFullPath($source)
if ($McpOnly -and -not (Test-Path -LiteralPath (Join-Path $source 'MANIFEST.json') -PathType Leaf)) {
    throw '-McpOnly requires an existing local Toolkit source; refusing Git clone or client configuration.'
}
if (-not $ToolkitPath -and -not (Test-Path -LiteralPath (Join-Path $source 'MANIFEST.json'))) {
    if (Test-Path -LiteralPath $source) { throw "Existing directory is not a Toolkit checkout: $source" }
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) { throw 'Git not found. Pass -ToolkitPath pointing to an existing Toolkit checkout.' }
    if ($PSCmdlet.ShouldProcess($source, 'Clone public Toolkit as read-only reference')) {
        & $git.Source clone --depth 1 -- https://github.com/MikeMoore1337/ai-development-toolkit.git $source
        if ($LASTEXITCODE -ne 0) { throw 'Toolkit clone failed; no MCP configuration changed.' }
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $source 'MANIFEST.json'))) {
    if ($WhatIfPreference) { Write-Host '[WhatIf] Toolkit checkout is not installed; exiting before validation.'; return }
    throw 'Toolkit manifest missing. Check -ToolkitPath.'
}

$python = Get-Command py -ErrorAction SilentlyContinue
$pyArgs = @()
if ($python) { $pyArgs = @('-3') }
else { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 is required. Neither py nor python is available.' }
& $python.Source @pyArgs $server --source $source --check
if ($LASTEXITCODE -ne 0) { throw 'MCP self-check failed; no client configuration changed.' }

# Unlike `mcp get` on an absent server, `mcp list --json` exits successfully.
# This avoids PowerShell 5.1 treating expected CLI stderr as a terminating error.
function Test-CodexMcpExists([string]$Executable) {
    $output = & $Executable mcp list --json | Out-String
    if ($LASTEXITCODE -ne 0) { throw 'Codex MCP list failed; existing configuration was not changed.' }
    try { $entries = @(ConvertFrom-Json -InputObject $output -ErrorAction Stop) }
    catch { throw 'Codex MCP list returned invalid JSON; existing configuration was not changed.' }
    return (@($entries | Where-Object { $_.name -eq 'ai-development-toolkit' }).Count -gt 0)
}

# Claude Code has no guaranteed machine-readable `mcp get` negative probe.
# Make expected stderr non-terminating only inside this helper.
function Test-ClaudeMcpExists([string]$Executable) {
    $ErrorActionPreference = 'Continue'
    & $Executable mcp get ai-development-toolkit *> $null
    return ($LASTEXITCODE -eq 0)
}

# Built-in SHA256 works even when PowerShell's Get-FileHash module cannot
# auto-load (e.g. a tightly isolated/locked-down user profile).
function Get-ADTFileSHA256([string]$File) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $stream = [IO.File]::OpenRead($File)
        try {
            return [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '')
        }
        finally { $stream.Dispose() }
    }
    finally { $sha.Dispose() }
}
function Backup-IfExists([string]$File) {
    if (Test-Path -LiteralPath $File -PathType Leaf) {
        $backup = "$File.adt-backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
        Copy-Item -LiteralPath $File -Destination $backup -ErrorAction Stop
        Write-Host "Backup: $backup"
    }
}
function Add-InstructionBlock([string]$File) {
    $begin = '<!-- ADT-PERSONAL BEGIN -->'
    $end = '<!-- ADT-PERSONAL END -->'
    $block = @'
<!-- ADT-PERSONAL BEGIN -->
For every software engineering, QA, UI/UX, security or DevOps task in the active Codex workspace:
1. First honor the active project's applicable AGENTS.md, approved project rules and current workspace permissions. Identify the actual target workspace; never assume the Toolkit checkout is the target.
2. Inspect names of relevant project/ancestor and user-level Codex skills and available agent roles, using allowed read-only file access. Do not load all skill bodies. The names should be reported to the MCP as existing_skills and existing_roles. Do not claim the inventory is complete if a source is inaccessible.
3. Automatically call the globally connected `ai-development-toolkit` MCP tool `toolkit_prepare_task` using the user's task and observed existing skill/role names. No repository URL needs to be supplied by the user. Use returned `loaded_skills` and `loaded_roles` as guidance for this task, consulting `toolkit_get_reference` only as necessary. Prefer existing project guidance over any conflicting Toolkit content.
4. A Toolkit role is a guidance document; it is NOT a spawned Codex subagent. Reading a remote skill via MCP is NOT installing or activating a native Codex skill. Don't claim native activation, model-inferred routing, or actual subagent execution without separate evidence.
5. Do not install or copy Toolkit skills or roles, scripts, test artifacts or reports into the corporate project or other workspaces without explicit owner approval. If native installation is explicitly requested, use the Toolkit Skill Manager preview before its `--apply` stage. Never overwrite unmanaged skills.
6. Keep Toolkit itself read-only for non-Toolkit work, comply with company network/data policies, do not use paid APIs by default, respect design and release approval gates, and report real test results accurately. If MCP is unavailable, say so and continue using permitted project-local guidance.
<!-- ADT-PERSONAL END -->
'@
    $dir = Split-Path -Parent $File
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $existing = if (Test-Path -LiteralPath $File) { [IO.File]::ReadAllText($File) } else { '' }
    $start = $existing.IndexOf($begin, [StringComparison]::Ordinal)
    $finish = $existing.IndexOf($end, [StringComparison]::Ordinal)
    if ($start -ge 0 -and $finish -lt $start) { throw "Malformed ADT block in $File; leaving unchanged" }
    if ($start -lt 0 -and $finish -ge 0) { throw "Malformed ADT block in $File; leaving unchanged" }
    if ($start -ge 0) {
        $before = $existing.Substring(0, $start)
        $after = $existing.Substring($finish + $end.Length)
        $updated = $before + $block + $after
    } else {
        $updated = $existing + [Environment]::NewLine + $block + [Environment]::NewLine
    }
    if ($updated -ceq $existing) { Write-Host "Global instructions already up to date: $File"; return }
    Backup-IfExists $File
    [IO.File]::WriteAllText($File, $updated, [Text.UTF8Encoding]::new($false))
    Write-Host "Updated global instructions: $File"
}

# Register the MCP from a stable user-local location, not from Downloads.
# No changes to the caller's project or the Toolkit source checkout.
$targetDir = Join-Path $homeRoot 'ADT-Personal\mcp'
$installedServer = Join-Path $targetDir 'adt_mcp.py'
$installedDiscovery = Join-Path $targetDir 'adt_discovery.py'
if ($McpOnly -and -not (Test-Path -LiteralPath $installedServer -PathType Leaf)) {
    throw '-McpOnly requires an existing MCP launcher at the standard user-local path; refusing new registration.'
}
if ($Codex -or $ClaudeCode -or $McpOnly) {
    # Installing only adt_mcp.py would break imports introduced in MCP 0.1.10.
    $needsBundle = (-not (Test-Path -LiteralPath $installedServer -PathType Leaf) -or
                    -not (Test-Path -LiteralPath $installedDiscovery -PathType Leaf))
    if (-not $needsBundle) {
        $needsBundle = ((Get-ADTFileSHA256 $server) -ne
                        (Get-ADTFileSHA256 $installedServer) -or
                        (Get-ADTFileSHA256 $discovery) -ne
                        (Get-ADTFileSHA256 $installedDiscovery))
    }
    if ($needsBundle -and $PSCmdlet.ShouldProcess($targetDir, 'Install verified MCP module pair')) {
        foreach ($destination in @($installedServer, $installedDiscovery)) {
            if ((Test-Path -LiteralPath $destination) -and
                ((Get-Item -LiteralPath $destination -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw "Refusing linked MCP destination: $destination"
            }
        }
        if (-not (Test-Path -LiteralPath $targetDir)) {
            New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        }
        $stage = Join-Path $targetDir ('.adt-stage-' + [guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $stage -ErrorAction Stop | Out-Null
        $stageServer = Join-Path $stage 'adt_mcp.py'
        $stageDiscovery = Join-Path $stage 'adt_discovery.py'
        $hadServer = Test-Path -LiteralPath $installedServer -PathType Leaf
        $hadDiscovery = Test-Path -LiteralPath $installedDiscovery -PathType Leaf
        $changedInstalled = $false
        try {
            Copy-Item -LiteralPath $server -Destination $stageServer -ErrorAction Stop
            Copy-Item -LiteralPath $discovery -Destination $stageDiscovery -ErrorAction Stop
            & $python.Source @pyArgs $stageServer --source $source --check
            if ($LASTEXITCODE -ne 0) { throw 'Staged MCP module pair self-check failed.' }

            if ($hadServer) {
                Copy-Item -LiteralPath $installedServer -Destination (Join-Path $stage 'old_mcp.py') -ErrorAction Stop
                Backup-IfExists $installedServer
            }
            if ($hadDiscovery) {
                Copy-Item -LiteralPath $installedDiscovery -Destination (Join-Path $stage 'old_discovery.py') -ErrorAction Stop
                Backup-IfExists $installedDiscovery
            }
            $changedInstalled = $true
            # The support module must be present before the new entrypoint runs.
            Copy-Item -LiteralPath $stageDiscovery -Destination $installedDiscovery -Force -ErrorAction Stop
            Copy-Item -LiteralPath $stageServer -Destination $installedServer -Force -ErrorAction Stop
            & $python.Source @pyArgs $installedServer --source $source --check
            if ($LASTEXITCODE -ne 0) { throw 'Installed MCP module pair self-check failed.' }
            Write-Host "Installed MCP module pair: $targetDir"
        }
        catch {
            if ($changedInstalled) {
                if ($hadServer) {
                    Copy-Item -LiteralPath (Join-Path $stage 'old_mcp.py') -Destination $installedServer -Force
                } else {
                    Remove-Item -LiteralPath $installedServer -Force -ErrorAction SilentlyContinue
                }
                if ($hadDiscovery) {
                    Copy-Item -LiteralPath (Join-Path $stage 'old_discovery.py') -Destination $installedDiscovery -Force
                } else {
                    Remove-Item -LiteralPath $installedDiscovery -Force -ErrorAction SilentlyContinue
                }
            }
            throw
        }
        finally {
            Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

if ($Codex) {
    $codexCommand = Get-Command codex -ErrorAction SilentlyContinue
    if (-not $codexCommand) { Write-Warning 'Codex CLI not found: skipping Codex configuration.' }
    elseif ($PSCmdlet.ShouldProcess('Codex user configuration', 'Add read-only ADT MCP')) {
        if (Test-CodexMcpExists $codexCommand.Source) {
            Write-Host 'Codex MCP ai-development-toolkit already exists; preserving its settings.'
        } else {
            $codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
            Backup-IfExists (Join-Path $codexHome 'config.toml')
            & $codexCommand.Source mcp add ai-development-toolkit -- $python.Source @pyArgs $installedServer --source $source
            if ($LASTEXITCODE -ne 0) { throw 'Failed to configure Codex MCP.' }
            if (-not (Test-CodexMcpExists $codexCommand.Source)) { throw 'Codex MCP was not found after registration.' }
        }
        if (-not $SkipGlobalInstructions) {
            $codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
            Add-InstructionBlock (Join-Path $codexHome 'AGENTS.md')
        }
    }
}
if ($ClaudeCode) {
    $claude = Get-Command claude -ErrorAction SilentlyContinue
    if (-not $claude) { Write-Warning 'Claude Code CLI not found: skipping Claude Code configuration.' }
    elseif ($PSCmdlet.ShouldProcess('Claude Code user configuration', 'Add read-only ADT MCP')) {
        if (Test-ClaudeMcpExists $claude.Source) {
            Write-Host 'Claude MCP ai-development-toolkit already exists; preserving its settings.'
        } else {
            Backup-IfExists (Join-Path $HOME '.claude.json')
            & $claude.Source mcp add --transport stdio --scope user ai-development-toolkit -- $python.Source @pyArgs $installedServer --source $source
            if ($LASTEXITCODE -ne 0) { throw 'Failed to configure Claude Code MCP.' }
        }
        if (-not $SkipGlobalInstructions) {
            Add-InstructionBlock (Join-Path (Join-Path $HOME '.claude') 'CLAUDE.md')
        }
    }
}
Write-Host 'Local MCP package ready. Restart the coding client and verify with its MCP menu.'
