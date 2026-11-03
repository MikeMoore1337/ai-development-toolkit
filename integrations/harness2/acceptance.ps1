<#
.SYNOPSIS
    Opt-in acceptance of ORIGINAL pinned Harness2 from Windows/Ubuntu WSL2.
.DESCRIPTION
    Runs original Harness2 readiness checks and optional bounded Groq Free
    OpenCode smoke in WSL2. No paid models, judge, Codex or Claude CLI.
    Preflight is read-only. Install and Setup require explicit -Action values.
#>
[CmdletBinding()]
param(
    [ValidateSet('Preflight', 'Install', 'Remove', 'Status', 'SetupPreview', 'Setup', 'Check', 'RunPreview', 'Report', 'Artifacts', 'GroqFreeCheck', 'GroqFreeSmoke')]
    [string]$Action = 'Preflight',
    [ValidateSet('lab', 'jb', 'wb')]
    [string]$Benchmark = 'lab',
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')]
    [string]$Distribution = 'auto',
    [switch]$ConfirmNetworkDownloads,
    [switch]$ConfirmRemove,
    [switch]$ConfirmGroqFree
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Reject unauthorized setup before invoking any external process.
if ($Action -eq 'Setup' -and -not $ConfirmNetworkDownloads) {
    throw 'HARNESS2_SETUP_REQUIRES_NETWORK_CONFIRMATION'
}
if ($Action -ne 'Setup' -and $ConfirmNetworkDownloads) {
    throw 'HARNESS2_UNEXPECTED_NETWORK_CONFIRMATION'
}
if ($Action -eq 'Remove' -and -not $ConfirmRemove) {
    throw 'HARNESS2_REMOVE_REQUIRES_CONFIRMATION'
}
if ($Action -ne 'Remove' -and $ConfirmRemove) {
    throw 'HARNESS2_UNEXPECTED_REMOVE_CONFIRMATION'
}
if ($Action -eq 'GroqFreeSmoke' -and -not $ConfirmGroqFree) {
    throw 'HARNESS2_GROQ_FREE_SMOKE_REQUIRES_CONFIRMATION'
}
if ($Action -ne 'GroqFreeSmoke' -and $ConfirmGroqFree) {
    throw 'HARNESS2_UNEXPECTED_GROQ_FREE_CONFIRMATION'
}
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'HARNESS2_WSL_UNAVAILABLE'
}

# Accept installed Ubuntu distro names without touching Docker or WSL defaults.
# PowerShell 5.1 may receive NUL-interleaved output from wsl.exe --list.
$installedRaw = @(& wsl.exe --list --quiet 2>$null)
if ($LASTEXITCODE -ne 0) {
    throw 'HARNESS2_WSL_LIST_FAILED: run wsl --list --verbose'
}
$installedDistros = @($installedRaw | ForEach-Object {
    ([string]$_).Replace([string][char]0, '').Replace([string][char]0xFEFF, '').Trim()
} | Where-Object { $_.Length -gt 0 })

if ($Distribution -eq 'auto') {
    foreach ($preferred in @('Ubuntu-24.04', 'Ubuntu', 'Ubuntu-22.04')) {
        if ($installedDistros -ccontains $preferred) {
            $Distribution = $preferred
            break
        }
    }
    if ($Distribution -eq 'auto') {
        $otherUbuntu = @($installedDistros | Where-Object {
            $_ -cmatch '^Ubuntu-[0-9]{2}\.[0-9]{2}$'
        } | Sort-Object -Descending)
        if ($otherUbuntu.Count -eq 0) {
            throw 'HARNESS2_UBUNTU_DISTRO_MISSING: run wsl --list --verbose; install with wsl --install -d Ubuntu-24.04'
        }
        $Distribution = $otherUbuntu[0]
    }
}
elseif ($installedDistros -cnotcontains $Distribution) {
    throw "HARNESS2_WSL_DISTRO_NOT_FOUND: $Distribution; run wsl --list --verbose"
}
if ($Distribution -cmatch '^docker-desktop(?:-data)?$') {
    throw 'HARNESS2_DOCKER_INTERNAL_DISTRO_REFUSED'
}
Write-Output "HARNESS2_WSL_DISTRIBUTION=$Distribution"

function Invoke-WSLChecked {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    & wsl.exe --distribution $Distribution --exec @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "HARNESS2_WSL_EXIT_$LASTEXITCODE"
    }
}

# Avoid passing multiline Bash source via Windows PowerShell's native argument
# marshalling; it can split/alter quotes and CRLF before WSL receives -c.
# Resolve a fixed checked-in .sh file instead, with no shell interpolation.
$translated = @(& wsl.exe --distribution $Distribution --exec wslpath -a $PSCommandPath)
if ($LASTEXITCODE -ne 0 -or $translated.Count -ne 1) {
    throw 'HARNESS2_TOOLKIT_PATH_UNAVAILABLE'
}
$sourcePath = $translated[0].Trim()
if (-not $sourcePath.StartsWith('/') -or -not $sourcePath.EndsWith('/acceptance.ps1')) {
    throw 'HARNESS2_TOOLKIT_PATH_INVALID'
}
$sourceDirectory = $sourcePath.Substring(0, $sourcePath.Length - '/acceptance.ps1'.Length)
$installer = "$sourceDirectory/install.sh"
$bridge = "$sourceDirectory/cli.sh"
$preflightScript = "$sourceDirectory/preflight.sh"
$groqFreeScript = "$sourceDirectory/groq-free-smoke.sh"

# Preflight is read-only and never runs models or downloads dependencies.
Invoke-WSLChecked -Arguments @('bash', $preflightScript)
if ($Action -eq 'Preflight') {
    return
}

switch ($Action) {
    'Install'      { Invoke-WSLChecked -Arguments @('bash', $installer, 'install') }
    'Remove'       { Invoke-WSLChecked -Arguments @('bash', $installer, 'remove', '--confirm') }
    'Status'       { Invoke-WSLChecked -Arguments @('bash', $bridge, 'status') }
    'SetupPreview' { Invoke-WSLChecked -Arguments @('bash', $bridge, 'setup-preview', $Benchmark) }
    'Setup'        { Invoke-WSLChecked -Arguments @('bash', $bridge, 'setup', $Benchmark, '--confirm-network-downloads') }
    'Check'        { Invoke-WSLChecked -Arguments @('bash', $bridge, 'check', $Benchmark) }
    'RunPreview'   { Invoke-WSLChecked -Arguments @('bash', $bridge, 'run-preview', $Benchmark) }
    'Report'       { Invoke-WSLChecked -Arguments @('bash', $bridge, 'report', $Benchmark) }
    'Artifacts'    { Invoke-WSLChecked -Arguments @('bash', $bridge, 'artifacts') }
    'GroqFreeCheck' {
        # Original JobBench installation check only. No provider calls or real credentials.
        Invoke-WSLChecked -Arguments @('bash', $groqFreeScript, 'check')
    }
    'GroqFreeSmoke' {
        # The existing Windows desktop gateway owns the actual provider credential.
        # Never copy it into WSL, argv, a public Toolkit repository or a log.
        $configFile = Join-Path $env:APPDATA 'FreeLLMAPI\config.json'
        if (-not (Test-Path -LiteralPath $configFile -PathType Leaf)) {
            throw 'HARNESS2_GROQ_FREE_ROUTER_NOT_INSTALLED'
        }
        $settings = Get-Content -LiteralPath $configFile -Raw | ConvertFrom-Json
        $port = [int]$settings.port
        if ($port -lt 1024 -or $port -gt 65535) {
            throw 'HARNESS2_GROQ_FREE_ROUTER_PORT_INVALID'
        }
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri ("http://127.0.0.1:" + $port + "/health") -TimeoutSec 3
            if ([int]$response.StatusCode -ne 200) {
                throw 'HARNESS2_GROQ_FREE_ROUTER_NOT_RUNNING'
            }
        } catch {
            throw 'HARNESS2_GROQ_FREE_ROUTER_NOT_RUNNING: start the installed FreeLLMAPI desktop app'
        }
        if (-not (Get-Command py.exe -ErrorAction SilentlyContinue)) {
            throw 'HARNESS2_GROQ_FREE_WINDOWS_PYTHON_MISSING'
        }
        $windowsPython = @(& py.exe -3 -c 'import sys; print(sys.executable)' 2>$null)
        if ($LASTEXITCODE -ne 0 -or $windowsPython.Count -ne 1) {
            throw 'HARNESS2_GROQ_FREE_WINDOWS_PYTHON_INVALID'
        }
        $pythonWSL = @(& wsl.exe --distribution $Distribution --exec wslpath -u $windowsPython[0].Trim())
        if ($LASTEXITCODE -ne 0 -or $pythonWSL.Count -ne 1 -or
            -not $pythonWSL[0].Trim().StartsWith('/mnt/')) {
            throw 'HARNESS2_GROQ_FREE_WINDOWS_PYTHON_NOT_MOUNTED'
        }
        Invoke-WSLChecked -Arguments @('bash', $groqFreeScript, 'smoke', $pythonWSL[0].Trim(), '--confirm-groq-free')
    }
    default        { throw 'HARNESS2_UNKNOWN_ACTION' }
}
