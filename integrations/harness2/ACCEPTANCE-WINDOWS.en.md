# Harness²: original upstream acceptance on Windows/WSL2

This Toolkit #421 entry point invokes only its own read-only `preflight.sh` and the existing `install.sh` and `cli.sh` bridges inside Ubuntu WSL2. It does not change Windows Python 3.14, Codex Desktop, Hermes, YFC or Second Brain. No model runs, judges, Codex CLI or Claude CLI are invoked. Preflight is executed as a checked-in Bash file path, not a multiline `bash -c` argument, avoiding Windows PowerShell 5.1 quote and newline corruption.

Requirements: Windows 11 and Ubuntu under WSL2. The script automatically selects an installed `Ubuntu-24.04`, `Ubuntu`, `Ubuntu-22.04` or another versioned `Ubuntu-XX.YY` distribution; use `-Distribution Ubuntu-24.04` for explicit selection. The Docker-managed `docker-desktop` distro is not used. A non-root Ubuntu user, Git and Python 3.12 are required. A full official benchmark setup additionally needs uv, npm, and the prerequisites in [upstream SETUP](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/SETUP.md). The Toolkit checkout must be reachable from WSL2 through wslpath.

If Ubuntu is missing, run `wsl --list --verbose`, `wsl --list --online`, then `wsl --install -d Ubuntu-24.04` in Windows PowerShell. Installing a distribution is an explicit Windows administrator decision; this Harness² script **never** installs Linux, selects Docker, or changes your WSL defaults. On first launch create an unprivileged Linux account; a Windows restart may be necessary.


**A WSL localhost-proxy warning in NAT mode** is not a Bash parse error or a preflight failure by itself. If a subsequent installation cannot access GitHub/PyPI, investigate networking and proxy availability inside Ubuntu separately. This script never modifies system proxy settings or weakens security checks.

From Windows PowerShell in the Toolkit checkout:

~~~powershell
.\integrations\harness2\acceptance.ps1 -Action Preflight
.\integrations\harness2\acceptance.ps1 -Action Install
.\integrations\harness2\acceptance.ps1 -Action Status
.\integrations\harness2\acceptance.ps1 -Action SetupPreview -Benchmark lab
.\integrations\harness2\acceptance.ps1 -Action Check -Benchmark lab
.\integrations\harness2\acceptance.ps1 -Action Artifacts
~~~

**Check is expected to fail** until official benchmark prerequisites and credentials are configured. A failed readiness check is not proof that the bridge failed. A dry run is not evidence of a real benchmark result.

An explicit setup action is available only after reviewing licences, third-party downloads, disk/network effects and isolation:

~~~powershell
.\integrations\harness2\acceptance.ps1 -Action Setup -Benchmark lab -ConfirmNetworkDownloads
~~~

Setup downloads and executes upstream dependencies; it does not authorize model/paid-API calls or execution on a secrets-bearing host.

Safe rollback also requires explicit confirmation:

~~~powershell
.\integrations\harness2\acceptance.ps1 -Action Remove -ConfirmRemove
~~~

Removal touches only the verified pinned installation; external results remain. Resolve missing WSL2, Git or Python 3.12 inside Ubuntu rather than modifying global Windows Python. These steps do not establish Codex Desktop compatibility, model effectiveness, or complete live acceptance of Toolkit #421.
