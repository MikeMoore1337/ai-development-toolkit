<#
.SYNOPSIS
    Opt-in acceptance of ORIGINAL pinned Harness2 from Windows/Ubuntu WSL2.
.DESCRIPTION
    Runs only the existing Toolkit installer and safe native CLI bridge in WSL2.
    Does not invoke models, agent benchmarks, judge, Codex CLI or Claude CLI.
    Preflight is read-only. Install and Setup require explicit -Action values.
#>
[CmdletBinding()]
param(
    [ValidateSet('Preflight', 'Install', 'Remove', 'Status', 'SetupPreview', 'Setup', 'Check', 'RunPreview', 'Report', 'Artifacts')]
    [string]$Action = 'Preflight',
    [ValidateSet('lab', 'jb', 'wb')]
    [string]$Benchmark = 'lab',
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')]
    [string]$Distribution = 'Ubuntu',
    [switch]$ConfirmNetworkDownloads,
    [switch]$ConfirmRemove
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
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'HARNESS2_WSL_UNAVAILABLE'
}

function Invoke-WSLChecked {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    & wsl.exe --distribution $Distribution --exec @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "HARNESS2_WSL_EXIT_$LASTEXITCODE"
    }
}

# Strictly inside the named Ubuntu distro, not in the Windows-host Docker relay.
# Do not log environment variables, provider credentials, private file paths, or tokens.
$preflight = @'
set -Eeuo pipefail
[[ "$(id -u)" != 0 ]] || { echo 'HARNESS2_REFUSED_ROOT' >&2; exit 2; }
grep -qi microsoft /proc/sys/kernel/osrelease || { echo 'HARNESS2_NOT_WSL2' >&2; exit 2; }
command -v git >/dev/null || { echo 'HARNESS2_GIT_MISSING' >&2; exit 2; }
command -v python3.12 >/dev/null || { echo 'HARNESS2_PYTHON312_MISSING' >&2; exit 2; }
python3.12 -c 'import sys; assert sys.version_info[:2] == (3, 12)' || { echo 'HARNESS2_PYTHON312_INVALID' >&2; exit 2; }
printf 'HARNESS2_WSL2=READY\nPYTHON=3.12\n'
if command -v uv >/dev/null; then printf 'UV=PRESENT\n'; else printf 'UV=MISSING_FOR_SETUP\n'; fi
if command -v npm >/dev/null; then printf 'NPM=PRESENT\n'; else printf 'NPM=MISSING_FOR_SETUP\n'; fi
printf 'MODEL_EXECUTION=DISABLED\n'
'@
Invoke-WSLChecked -Arguments @('bash', '-c', $preflight)
if ($Action -eq 'Preflight') {
    return
}

# wslpath converts the checked-out Toolkit path without interpolating it into Bash.
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
    default        { throw 'HARNESS2_UNKNOWN_ACTION' }
}
