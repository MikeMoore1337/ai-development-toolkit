# Secret lifecycle and CI/CD trust

## Secrets
Create -> store -> transmit -> use -> rotate -> revoke -> delete -> respond to compromise.
Prefer scoped, short-lived tokens and managed secret stores; avoid repository files, plaintext logs, unprotected build artifacts, and passing values through untrusted PR contexts. Review references and configurations without retrieving secret values. For a suspected leak, privately document file/path and class, restrict exposure, examine usage, rotate or revoke **only with owner authority**, validate downstream effects and remove the source. Never paste the leaked value into CI, an issue, or a chat.

## CI
For each workflow: establish triggers, identity of the triggering actor, untrusted inputs, effective top-level/job-level permissions, access to secrets, third-party actions and pinning, network egress, download/execute paths, digest verification, artifact provenance and the deploy boundary.

- A fork PR must not receive write access or live secrets merely to run tests. Check `pull_request_target` and checkout of untrusted HEAD together.
- Do not splice PR titles, branch names, commit messages, labels or responses into shell scripts without safe argument boundaries.
- For downloaded code, verify origin, allowed license and integrity before execution. Check that a workflow artifact is from the expected revision before release.
- Keep existing checks and protected branches. No automated secret rotation, CI privilege escalation or production deploy by this skill.

The Toolkit's current validation includes `permissions: contents: read`, Ruff, actionlint, source archive, SHA256 and provenance checks. A passing checklist or workflow does not establish a security certification.
