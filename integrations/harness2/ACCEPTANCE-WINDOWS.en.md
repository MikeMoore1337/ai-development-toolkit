# Harness²: original upstream acceptance on Windows/WSL2

This Toolkit #421 entry point invokes only the existing install.sh and cli.sh bridges inside Ubuntu WSL2. It does not change Windows Python 3.14, Codex Desktop, Hermes, YFC or Second Brain. No model runs, judges, Codex CLI or Claude CLI are invoked.

Requirements: Windows 11; Ubuntu under WSL2 (use -Distribution Ubuntu-24.04 if needed); an unprivileged Ubuntu user, Git and Python 3.12. A full official benchmark setup additionally needs uv, npm, and the prerequisites in [upstream SETUP](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/SETUP.md). The Toolkit checkout must be reachable from WSL2 through wslpath.

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
