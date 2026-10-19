#!/usr/bin/env python3
"""Credential-free, loopback-only Paperclip control-plane smoke.

No agents are created or started. No model APIs are invoked.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:3100"
ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents" / "skills" / "minimal-safe-change"


def request(method: str, path: str, payload: dict | None = None):
    assert path.startswith("/api/") and ".." not in path
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(
        BASE + path,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method=method,
    )
    try:
        with urlopen(req, timeout=15) as response:
            if response.status not in (200, 201):
                raise RuntimeError(f"Unexpected status {response.status} on {method} {path}")
            return json.load(response)
    except HTTPError as exc:
        # Summarize only server-supplied error metadata. Never print response
        # bodies or bootstrap logs; these may include environment-specific data.
        try:
            failure = json.load(exc)
        except (ValueError, OSError):
            failure = {}
        if not isinstance(failure, dict):
            failure = {}
        detail = failure.get("details")
        code = detail.get("code") if isinstance(detail, dict) else None
        label = code if isinstance(code, str) and code.replace("_", "").isalnum() else "unknown"
        upstream_status = detail.get("status") if isinstance(detail, dict) else None
        upstream_status = upstream_status if type(upstream_status) is int and 100 <= upstream_status <= 599 else "unknown"
        message = failure.get("error")
        if not isinstance(message, str):
            message = failure.get("message")
        # Safe local error context only, never raw bodies, URLs or credentials.
        safe = "".join(ch for ch in message[:120] if ch.isalpha() or ch in " -_.:,") if isinstance(message, str) else ""
        raise RuntimeError(
            f"Paperclip {method} {path}: HTTP {exc.code}, upstream_http={upstream_status}, error_code={label}, reason={safe!r}"
        ) from None
    except URLError as exc:
        raise RuntimeError(f"Paperclip is not reachable at loopback: {exc.reason}") from None



def make_restricted_company(name: str, description: str) -> str:
    created = request("POST", "/api/companies", {
        "name": name,
        "description": description,
        "budgetMonthlyCents": 0,
    })
    company_id = created.get("id") if isinstance(created, dict) else None
    if not isinstance(company_id, str) or not company_id:
        raise RuntimeError("Paperclip company creation did not return an ID")

    # The create-company API does NOT accept requireBoardApprovalForNewAgents.
    # Its database default is false; enforce the gate through the supported
    # PATCH endpoint, then read back BOTH controls before importing anything.
    request("PATCH", f"/api/companies/{company_id}", {
        "requireBoardApprovalForNewAgents": True,
    })
    stored = request("GET", f"/api/companies/{company_id}")
    if not isinstance(stored, dict) or stored.get("budgetMonthlyCents") != 0:
        raise RuntimeError("Pilot company did not retain its zero budget")
    if stored.get("requireBoardApprovalForNewAgents") is not True:
        raise RuntimeError("Pilot company agent approval policy is not enabled")
    return company_id

def main() -> None:
    source = SKILL / "SKILL.md"
    if not source.is_file() or not source.read_text(encoding="utf-8").startswith("---\n"):
        raise RuntimeError("Toolkit skill missing or has no YAML frontmatter")
    health = request("GET", "/api/health")
    if not isinstance(health, dict) or health.get("status") in ("error", "unhealthy"):
        raise RuntimeError("Paperclip health is not healthy")
    companies_before = request("GET", "/api/companies")
    if not isinstance(companies_before, list):
        raise RuntimeError("Company listing has unexpected API schema")
    company_id = make_restricted_company(
        "Paperclip Toolkit CI Pilot",
        "Ephemeral zero-spend, no-agent skill compatibility smoke",
    )

    # First prove that the official managed-skill API can preserve the exact
    # Toolkit source bytes. This is a separate capability from GitHub import.
    source_markdown = source.read_text(encoding="utf-8")
    managed = request("POST", f"/api/companies/{company_id}/skills", {
        "name": "minimal-safe-change",
        "slug": "minimal-safe-change",
        "markdown": source_markdown,
    })
    skill_id = managed.get("id") if isinstance(managed, dict) else None
    if not isinstance(skill_id, str) or not skill_id:
        raise RuntimeError("Managed skill creation did not return an ID")
    skills = request("GET", f"/api/companies/{company_id}/skills")
    if not isinstance(skills, list) or not any(
        isinstance(item, dict) and item.get("slug") == "minimal-safe-change"
        for item in skills
    ):
        raise RuntimeError("Managed skill is missing from the company inventory")
    detail = request("GET", f"/api/companies/{company_id}/skills/{skill_id}/files?path=SKILL.md")
    if not isinstance(detail, dict) or detail.get("content") != source_markdown:
        raise RuntimeError("Managed skill differs from Toolkit's exact SKILL.md")

    # A GitHub-sourced import is an independent feature: a failure here must
    # not be misreported as a successful GitHub import via the managed API.
    github_company_id = make_restricted_company(
        "Paperclip GitHub Import CI Pilot",
        "Separate zero-spend organization to avoid a duplicate managed skill slug",
    )
    github_status = "PASS"
    try:
        result = request("POST", f"/api/companies/{github_company_id}/skills/import", {
            "source": "npx skills add https://github.com/MikeMoore1337/ai-development-toolkit/tree/73688b472ff3cce8091914b3d1845c414d930c7a --skill minimal-safe-change",
        })
        if not isinstance(result, dict) or not isinstance(result.get("imported"), list):
            raise RuntimeError("GitHub import response has unexpected shape")
        if not any(
            isinstance(item, dict) and item.get("slug") == "minimal-safe-change"
            for item in result["imported"]
        ):
            raise RuntimeError("GitHub import returned no matching skill")
    except RuntimeError as exc:
        github_status = "BLOCKED"
        # The exception contains only HTTP status, error code and a restricted
        # reason string, as enforced by request(). No payloads are logged.
        print(f"PAPERCLIP_GITHUB_IMPORT_DIAGNOSTIC: {exc}")

    print(json.dumps({
        "classification": "PAPERCLIP_CONTROL_PLANE_SMOKE_NOT_AGENT_EVAL",
        "paperclip_version": "2026.1012.0",
        "health_http": 200,
        "company_created": True,
        "budget_monthly_cents_verified": 0,
        "board_approval_required_verified": True,
        "managed_skill_created": "minimal-safe-change",
        "managed_skill_exact_source": True,
        "github_import": github_status,
        "skill_count": len(skills),
        "real_agent_trials": 0,
        "model_calls_requested_by_test": 0,
        "skill_activation_observed": False,
        "model_comparison": "NOT_PERFORMED",
    }, ensure_ascii=False, sort_keys=True))
    if github_status != "PASS":
        raise RuntimeError("GitHub source import not verified: see sanitized diagnostic above")


if __name__ == "__main__":
    main()
