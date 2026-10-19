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
        raise RuntimeError(
            f"Paperclip {method} {path}: HTTP {exc.code}, error_code={label}"
        ) from None
    except URLError as exc:
        raise RuntimeError(f"Paperclip is not reachable at loopback: {exc.reason}") from None


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
    company = request("POST", "/api/companies", {
        "name": "Paperclip Toolkit CI Pilot",
        "description": "Ephemeral zero-spend, no-agent skill compatibility smoke",
        "budgetMonthlyCents": 0,
        "requireBoardApprovalForNewAgents": True,
    })
    company_id = company.get("id") if isinstance(company, dict) else None
    if not isinstance(company_id, str) or not company_id:
        raise RuntimeError("Could not create an ephemeral pilot company")

    imported = request("POST", f"/api/companies/{company_id}/skills/import", {
        "source": "https://github.com/MikeMoore1337/ai-development-toolkit/tree/main/.agents/skills/minimal-safe-change",
    })
    skills = request("GET", f"/api/companies/{company_id}/skills")
    if not isinstance(skills, list):
        raise RuntimeError("Skills listing has unexpected API schema")
    names = [s.get("slug") for s in skills if isinstance(s, dict)]
    if "minimal-safe-change" not in names:
        raise RuntimeError("Toolkit skill not found after Paperclip import")
    if not isinstance(imported, dict):
        raise RuntimeError("Skill import did not return a JSON object")

    print(json.dumps({
        "classification": "PAPERCLIP_CONTROL_PLANE_SMOKE_NOT_AGENT_EVAL",
        "paperclip_version": "2026.1012.0",
        "health_http": 200,
        "company_created": True,
        "budget_monthly_cents": 0,
        "skill_imported": "minimal-safe-change",
        "skill_count": len(skills),
        "real_agent_trials": 0,
        "model_calls_requested_by_test": 0,
        "skill_activation_observed": False,
        "model_comparison": "NOT_PERFORMED",
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
