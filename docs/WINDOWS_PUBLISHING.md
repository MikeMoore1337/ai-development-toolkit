# Windows publication troubleshooting

[Русская версия](ru/WINDOWS_PUBLISHING.md)

This describes the **initial publication of a different, new repository**, not updating or releasing the existing official Toolkit repository. Do not rerun `scripts/publish_github.ps1` against the official repository. Use [GitHub setup](GITHUB_SETUP.md), [publication policy](PUBLICATION_POLICY.md) and the [reviewed release process](RELEASE_PROCESS.md) for maintenance. The initial-publication script uses `py -3` automatically when the Windows Python Launcher is installed; otherwise it uses `python`.

## PowerShell script execution

If PowerShell blocks the unsigned script, review it and remove the download mark from that file only:

```powershell
Unblock-File -LiteralPath .\scripts\publish_github.ps1
```

## Dependencies and preflight (initial publication only)

```powershell
py -3 -m pip install -r requirements-dev.txt
py -3 scripts/check_public_package.py
py -3 scripts/validate_pack.py
py -3 -m unittest discover -s tests -v
.\scripts\publish_github.ps1
```

## Windows symlinks and junctions

Windows sometimes denies `Path.symlink_to` with `WinError 1314` unless Developer Mode or a suitable privilege is enabled. The portability test now uses an NTFS directory junction when ordinary symlink creation is denied. The installer refuses either kind of redirection when installing to a destination path.

The Windows GitHub Actions job runs the tests with Python 3.14 so this case is checked in CI. Do not weaken the path checks or skip security tests simply to make the release pass.
