# Enables a user-scoped Windows scheduled task for the personal Toolkit reference checkout.
# Does not change the MCP launcher, projects, or global Codex/Claude instructions.
[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [string]$DailyAt = '10:35',
    [switch]$SkipFirstCheck,
    [switch]$Disable
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$taskName = 'ADT-Personal-Toolkit-Update'

if ($Disable) {
    $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($null -eq $existing) {
        Write-Host 'Updater task is already absent.'
    } elseif ($PSCmdlet.ShouldProcess($taskName, 'Unregister daily Toolkit updater task')) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
        Write-Host 'Updater task disabled. Toolkit source and MCP are untouched.'
    }
    return
}

if ($DailyAt -notmatch '^([01][0-9]|2[0-3]):[0-5][0-9]$') {
    throw 'DailyAt must use 24-hour HH:mm (e.g. 10:35)'
}
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$bundledUpdater = Join-Path $packageRoot 'updater\update_toolkit.py'
if (-not (Test-Path -LiteralPath $bundledUpdater -PathType Leaf)) {
    throw "Updater file not found: $bundledUpdater"
}
$pyCommand = Get-Command py -ErrorAction SilentlyContinue
if (-not $pyCommand) { throw 'Python launcher py.exe is required for scheduling. No task registered.' }
$localRoot = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME 'AppData\Local' }
$base = Join-Path $localRoot 'ADT-Personal'
$source = Join-Path $base 'toolkit-source'
$installed = Join-Path $base 'updater\update_toolkit.py'
$stateDir = Join-Path $base 'updater\state'
if (-not (Test-Path -LiteralPath (Join-Path $source 'MANIFEST.json') -PathType Leaf)) {
    throw "Dedicated Toolkit checkout not found: $source. Install MCP first."
}

# Register a task for the CURRENT user only; no password, elevation or machine-wide policy.
# Interactive logon requires the user to be signed in. Missed daily runs start when available.
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$when = [DateTime]::Today.AddHours([int]$DailyAt.Substring(0, 2)).AddMinutes([int]$DailyAt.Substring(3, 2))
$actionArgs = '-3 -B "' + $installed + '" --source "' + $source + '" --state-dir "' + $stateDir + '"'
$action = New-ScheduledTaskAction -Execute $pyCommand.Source -Argument $actionArgs -WorkingDirectory $base
$daily = New-ScheduledTaskTrigger -Daily -At $when
$atLogon = New-ScheduledTaskTrigger -AtLogOn -User $identity
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -MultipleInstances IgnoreNew

if ($PSCmdlet.ShouldProcess($taskName, 'Install auto updater and register current-user task')) {
    $targetDir = Split-Path -Parent $installed
    if (-not (Test-Path -LiteralPath $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    if (-not (Test-Path -LiteralPath $installed -PathType Leaf) -or
        (Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $bundledUpdater -Algorithm SHA256).Hash) {
        if (Test-Path -LiteralPath $installed -PathType Leaf) {
            $backup = "$installed.adt-backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
            Copy-Item -LiteralPath $installed -Destination $backup -ErrorAction Stop
            Write-Host "Updater backup: $backup"
        }
        Copy-Item -LiteralPath $bundledUpdater -Destination $installed -Force -ErrorAction Stop
    }
    try {
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($daily, $atLogon) `
            -Settings $settings -Principal $principal -Description 'Daily read-only source synchronization for AI Development Toolkit Personal MCP' `
            -Force -ErrorAction Stop | Out-Null
    } catch {
        throw "Cannot register a current-user scheduled task (corporate restrictions are possible): $($_.Exception.Message)"
    }
    $registered = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    if ($registered.State -eq 'Disabled') { throw 'Task exists but is disabled.' }
    Write-Host "Scheduled updater: $taskName ($identity)"
    Write-Host "Triggers: daily at $DailyAt local time and at user logon (once per local calendar day)."
    Write-Host "Installed updater: $installed"
    Write-Host "State file: $(Join-Path $stateDir 'state.json')"
    if (-not $SkipFirstCheck) {
        Write-Host 'Running first update check (GitHub access required)...'
        & $pyCommand.Source -3 -B $installed --source $source --state-dir $stateDir --force
        if ($LASTEXITCODE -ne 0) {
            Write-Warning 'First check failed. The scheduled task remains installed; check state/network and retry.'
        }
    }
}
