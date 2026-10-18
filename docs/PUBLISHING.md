# Publish on GitHub

Target: `https://github.com/MikeMoore1337/ai-development-toolkit` (proposed, **not yet created**).

Use an authenticated machine with `gh` and `git` available. The owner can run from PowerShell:

```powershell
.\scripts\publish_github.ps1
```

The script validates the package, prepares a commit, asks for an explicit `PUBLISH` confirmation, then creates the **public** repository and pushes `main`. It does **not** run automatically in a pipeline. If the target repository was created beforehand, use the standard `git remote add origin ...; git push -u origin main` workflow instead of re-running repository creation.

Previous toolkit distribution archives and private Make Feature tarball must not be included in the upload. Do not commit the containing directory of this toolkit.

After publication, follow [GitHub appearance and topics](GITHUB_SETUP.md) to set the social preview, description and community settings.
