"""Set the three required CI checks on an existing GitHub branch ruleset.

Requires authenticated GitHub CLI (gh) and repository admin permission.
Dry-run by default. --apply performs and verifies the update.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from copy import deepcopy
from typing import Any

REQUIRED_CHECKS = (
    "tests (ubuntu-latest, 3.12)",
    "tests (ubuntu-latest, 3.13)",
    "tests (windows-latest, 3.14)",
)
GITHUB_ACTIONS_APP_ID = 15368


def gh_json(*args: str, input_data: dict[str, Any] | None = None) -> Any:
    command = ["gh", "api", *args]
    try:
        process = subprocess.run(
            command,
            input=json.dumps(input_data, ensure_ascii=False) if input_data is not None else None,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("GitHub CLI (gh) is not installed or is not in PATH") from exc
    if process.returncode:
        message = process.stderr.strip() or f"exit code {process.returncode}"
        raise RuntimeError(f"GitHub API command failed: {message}")
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GitHub CLI returned invalid JSON") from exc


def detect_repo() -> str:
    command = ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
    except FileNotFoundError as exc:
        raise RuntimeError("GitHub CLI (gh) is not installed or is not in PATH") from exc
    if result.returncode:
        raise RuntimeError("Cannot identify repository. Run inside a clone or supply --repo OWNER/NAME")
    return result.stdout.strip()


def find_ruleset(repo: str, name: str) -> int:
    records = gh_json(f"repos/{repo}/rulesets")
    candidates = [
        record for record in records
        if record.get("name") == name and record.get("source_type") == "Repository"
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected exactly one ruleset named {name!r}, found {len(candidates)}")
    return int(candidates[0]["id"])


def desired_status_checks() -> list[dict[str, Any]]:
    return [{"context": check, "integration_id": GITHUB_ACTIONS_APP_ID} for check in REQUIRED_CHECKS]


def prepare_update(ruleset: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if ruleset.get("target") != "branch" or ruleset.get("enforcement") != "active":
        raise RuntimeError("Ruleset must be an active branch ruleset")
    includes = ruleset.get("conditions", {}).get("ref_name", {}).get("include", [])
    if "~DEFAULT_BRANCH" not in includes and "refs/heads/main" not in includes:
        raise RuntimeError("Ruleset does not protect the default/main branch")
    if "bypass_actors" not in ruleset:
        raise RuntimeError("Cannot read bypass actors; refusing to remove unknown exemptions")

    rules = deepcopy(ruleset.get("rules", []))
    matches = [rule for rule in rules if rule.get("type") == "required_status_checks"]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one required_status_checks rule, found {len(matches)}")

    previous = deepcopy(matches[0].get("parameters", {}))
    params = matches[0].setdefault("parameters", {})
    params["required_status_checks"] = desired_status_checks()
    params["strict_required_status_checks_policy"] = True
    params["do_not_enforce_on_create"] = False

    payload = {
        "name": ruleset["name"],
        "target": ruleset["target"],
        "enforcement": ruleset["enforcement"],
        "conditions": ruleset["conditions"],
        "bypass_actors": ruleset["bypass_actors"],
        "rules": rules,
    }
    return payload, previous != params


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="GitHub OWNER/NAME (default: current clone)")
    parser.add_argument("--ruleset", default="Protect main", help="Name of an existing ruleset")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default: preview only)")
    args = parser.parse_args(argv)
    try:
        repo = args.repo or detect_repo()
        if repo.count("/") != 1 or not all(repo.split("/")):
            raise RuntimeError("Repository must be OWNER/NAME")
        ruleset_id = find_ruleset(repo, args.ruleset)
        endpoint = f"repos/{repo}/rulesets/{ruleset_id}"
        payload, changed = prepare_update(gh_json(endpoint))
        print(f"Repository: {repo}; ruleset: {args.ruleset} (id={ruleset_id})")
        for check in REQUIRED_CHECKS:
            print(f"  - {check} (GitHub Actions)")
        if not changed:
            print("PASS: all required checks are already configured")
            return 0
        if not args.apply:
            print("PREVIEW ONLY: run again with --apply to enable required checks")
            return 0
        gh_json("--method", "PUT", endpoint, "--input", "-", input_data=payload)
        _, changed = prepare_update(gh_json(endpoint))
        if changed:
            raise RuntimeError("Update not verified: recheck GitHub ruleset settings")
        print("PASS: three required CI checks saved and independently verified")
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
