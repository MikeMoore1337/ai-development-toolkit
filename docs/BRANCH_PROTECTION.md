# Enforcing CI checks on `main`

The toolkit's [Validate toolkit](../.github/workflows/validate.yml) workflow runs on pull requests to `main` and on pushes to `main`.

Branch protection is configured separately in GitHub and **cannot be enabled by checking a file into the repository**. The repository owner must have GitHub CLI (`gh`) authenticated with repository administration permission.

The existing branch ruleset must be named `Protect main`, have `active` enforcement, and target the default branch. The script preserves its other rules and bypass list.

```powershell
gh auth status
py -3 scripts/configure_required_checks.py
py -3 scripts/configure_required_checks.py --apply
```

The first invocation is read-only. The second adds and verifies three required GitHub Actions checks:

- `tests (ubuntu-latest, 3.12)`
- `tests (ubuntu-latest, 3.13)`
- `tests (windows-latest, 3.14)`

The checks are pinned to the GitHub Actions app (ID `15368`, verified from the repository's check runs), and branches must be up to date before merge. The script does **not** bypass the pull request requirement, grant bypass privileges, or modify the workflow itself.

For a different checkout, specify `--repo OWNER/REPO`. After applying, inspect `Settings → Rules → Rulesets → Protect main` and confirm the three required checks. A PR with a failing check must remain unmergeable.
