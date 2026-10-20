#!/usr/bin/env python3
"""Issue #61: offline synthetic DevOps contracts. No network, subprocess or apply."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
STATES = (
    "DRAFT", "PLAN_PREPARED", "PLAN_VALIDATED", "APPROVAL_PENDING",
    "APPLY_AUTHORIZED", "APPLIED", "POST_APPLY_VERIFIED",
)
EVIDENCE = {
    "SOURCE_REVIEWED", "CONFIG_VALIDATED", "PLAN_VALIDATED",
    "APPROVAL_VERIFIED", "APPLY_EXECUTED", "DEPLOYMENT_VERIFIED",
    "RECOVERY_TESTED", "NOT_TESTED", "BLOCKED",
}
REQUIRED = {
    "pipeline_id", "repository", "trigger", "trust", "source_revision",
    "build_environment", "dependencies", "stages", "required_checks",
    "artifact", "permissions", "secrets", "environment", "approval",
    "migration", "recovery", "config", "container", "iac", "deployment",
}
STAGE_FIELDS = {
    "id", "inputs", "success", "failure", "depends_on", "permissions", "evidence",
}


def validate(packet: object) -> list[str]:
    """Return non-secret finding identifiers. No change is ever executed."""
    if not isinstance(packet, dict) or not REQUIRED <= packet.keys():
        return ["INVALID_CONTRACT"]
    p = packet
    errors: set[str] = set()
    if not all(isinstance(p[k], str) and p[k]
               for k in ("pipeline_id", "repository", "build_environment")):
        errors.add("INVALID_CONTRACT")
    if p["trigger"] not in ("pull_request", "push", "manual"):
        errors.add("INVALID_TRIGGER")
    if p["trust"] not in ("trusted", "untrusted"):
        errors.add("INVALID_TRUST")
    if not isinstance(p["dependencies"], list):
        errors.add("INVALID_DEPENDENCIES")
    revision = p["source_revision"]
    if not isinstance(revision, str) or not SHA40.fullmatch(revision):
        errors.add("INVALID_SOURCE_REVISION")

    stages = p["stages"]
    if not isinstance(stages, list) or not stages:
        errors.add("INVALID_STAGE")
    elif not all(isinstance(s, dict) and STAGE_FIELDS <= s.keys()
                 for s in stages):
        errors.add("INVALID_STAGE")
    else:
        names = [s["id"] for s in stages]
        if not all(isinstance(n, str) and n for n in names):
            errors.add("INVALID_STAGE")
        elif len(set(names)) != len(names):
            errors.add("DUPLICATE_STAGE")
        else:
            by_name = {s["id"]: s for s in stages}
            visited: set[str] = set()
            visiting: set[str] = set()

            def visit(name: str) -> None:
                if name in visiting:
                    errors.add("CYCLIC_PIPELINE")
                    return
                if name in visited:
                    return
                if name not in by_name:
                    errors.add("MISSING_STAGE_DEPENDENCY")
                    return
                visiting.add(name)
                for dep in by_name[name]["depends_on"]:
                    if isinstance(dep, str):
                        visit(dep)
                    else:
                        errors.add("INVALID_STAGE")
                visiting.remove(name)
                visited.add(name)

            for n in names:
                visit(n)
        for stage in stages:
            if not isinstance(stage["depends_on"], list) or not all(
                isinstance(stage[k], str) and stage[k]
                for k in ("inputs", "success", "failure", "permissions", "evidence")
            ):
                errors.add("INVALID_STAGE")

    checks = p["required_checks"]
    if not isinstance(checks, dict) or not checks or any(
        passed is not True for passed in checks.values()
    ):
        errors.add("MISSING_REQUIRED_CHECK")
    artifact = p["artifact"]
    if not isinstance(artifact, dict):
        errors.add("INVALID_ARTIFACT")
    else:
        if artifact.get("source_revision") != revision:
            errors.add("ARTIFACT_MISMATCH")
        sha = artifact.get("sha256")
        if not isinstance(sha, str) or not SHA64.fullmatch(sha):
            errors.add("MISSING_PROVENANCE")
        elif (not isinstance(artifact.get("synthetic_bytes"), str)
              or hashlib.sha256(artifact["synthetic_bytes"].encode()).hexdigest() != sha):
            errors.add("ARTIFACT_MISMATCH")
        if artifact.get("provenance") != "SYNTHETIC_KNOWN_SOURCE":
            errors.add("MISSING_PROVENANCE")

    perms = p["permissions"]
    if not isinstance(perms, dict):
        errors.add("INVALID_PERMISSIONS")
    elif p["trust"] == "untrusted" and (
        perms.get("contents") != "read" or perms.get("id_token") is not False
    ):
        errors.add("EXCESSIVE_CI_PERMISSIONS")
    secrets = p["secrets"]
    if not isinstance(secrets, dict):
        errors.add("INVALID_SECRETS")
    else:
        if secrets.get("embedded_value") is not None:
            errors.add("SECRET_EXPOSURE")
        if p["trust"] == "untrusted" and secrets.get("available") is not False:
            errors.add("UNTRUSTED_SECRETS")

    env = p["environment"]
    if not isinstance(env, dict) or env.get("name") not in (
        "local", "ci", "isolated-test", "staging", "production"
    ):
        errors.add("UNKNOWN_ENVIRONMENT")
        target = None
    else:
        target = env["name"]
        if env.get("endpoint_environment") != target:
            errors.add("WRONG_ENVIRONMENT")
        if target == "production" and p["trust"] == "untrusted":
            errors.add("UNTRUSTED_DEPLOYMENT")
    cfg = p["config"]
    if not isinstance(cfg, dict) or type(cfg.get("port")) is not int or not (
        1 <= cfg.get("port", 0) <= 65535
    ) or type(cfg.get("debug")) is not bool:
        errors.add("INVALID_CONFIG")
    elif target in ("staging", "production") and cfg["debug"]:
        errors.add("UNSAFE_DEBUG_CONFIG")

    container = p["container"]
    if not isinstance(container, dict):
        errors.add("INVALID_CONTAINER")
    elif container.get("enabled") is True and (
        container.get("startup") != container.get("expected_startup")
        or not container.get("healthcheck")
    ):
        errors.add("CONTAINER_RUNTIME_CONTRACT")
    iac = p["iac"]
    if not isinstance(iac, dict) or not isinstance(iac.get("deletions"), list):
        errors.add("INVALID_IAC")
    elif any(name not in iac.get("approved_deletions", [])
             for name in iac["deletions"]):
        errors.add("UNAPPROVED_DESTRUCTION")
    migration = p["migration"]
    if not isinstance(migration, dict):
        errors.add("INVALID_MIGRATION")
    elif (migration.get("compatible") is not True
          or migration.get("complete") is not True
          or migration.get("partial") is not False):
        errors.add("UNSAFE_MIGRATION")
    recovery = p["recovery"]
    if not isinstance(recovery, dict) or not recovery.get("procedure"):
        errors.add("INVALID_RECOVERY")
    elif (recovery.get("data_rollback") is True
          and recovery.get("restore_tested") is not True):
        errors.add("UNPROVEN_DATA_RECOVERY")

    approval = p["approval"]
    deploy = p["deployment"]
    if not isinstance(approval, dict) or not isinstance(deploy, dict):
        errors.add("INVALID_TRANSITION")
    else:
        state = deploy.get("state")
        if state not in STATES:
            errors.add("INVALID_TRANSITION")
        elif state in ("APPLY_AUTHORIZED", "APPLIED", "POST_APPLY_VERIFIED"):
            if (approval.get("scoped") is not True or approval.get("target") != target
                    or not approval.get("evidence")):
                errors.add("MISSING_APPROVAL")
        if state in ("APPLIED", "POST_APPLY_VERIFIED") and (
            not deploy.get("apply_evidence") or deploy.get("mode") == "synthetic"
        ):
            errors.add("FALSE_APPLY_CLAIM")
        if state == "POST_APPLY_VERIFIED" and not deploy.get("verification_evidence"):
            errors.add("MISSING_POST_VERIFICATION")
        if deploy.get("mode") != "synthetic":
            errors.add("REAL_OPERATION_FORBIDDEN")
        evidence = deploy.get("evidence")
        if evidence not in EVIDENCE:
            errors.add("INVALID_EVIDENCE")
        elif evidence in (
            "APPROVAL_VERIFIED", "APPLY_EXECUTED", "DEPLOYMENT_VERIFIED",
            "RECOVERY_TESTED",
        ):
            errors.add("EVIDENCE_INFLATION")
    return sorted(errors)


def fixtures() -> dict:
    return json.loads((ROOT / "fixtures/devops/cases.json").read_text(encoding="utf-8"))


def mutate(reference: dict, path: str, value: object) -> dict:
    changed = copy.deepcopy(reference)
    fields = path.split(".")
    node = changed
    for part in fields[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    if isinstance(node, list):
        node[int(fields[-1])] = value
    else:
        node[fields[-1]] = value
    return changed


def run_cases() -> dict:
    data = fixtures()
    baseline = validate(data["reference"])
    observations = {}
    for item in data["negative"]:
        findings = validate(mutate(data["reference"], item["path"], item["value"]))
        observations[item["id"]] = {
            "detected": item["code"] in findings,
            "codes": findings,
        }
    passed = not baseline and all(v["detected"] for v in observations.values())
    return {
        "result": "PASS" if passed else "FAIL",
        "nature": "SYNTHETIC_CONTRACT_ONLY",
        "positive": "PASS" if not baseline else "FAIL",
        "negative_count": len(observations),
        "negatives_rejected": sum(v["detected"] for v in observations.values()),
        "findings": observations,
        "real_deployment": "NOT_RUN",
        "real_iac_plan": "NOT_TESTED",
        "real_container": "NOT_TESTED",
        "real_restore": "NOT_TESTED",
        "real_skill_activation": "NOT_MEASURED",
    }


if __name__ == "__main__":
    report = run_cases()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["result"] == "PASS" else 1)
