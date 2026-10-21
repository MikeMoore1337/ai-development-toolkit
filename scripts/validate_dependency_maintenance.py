#!/usr/bin/env python3
"""Offline normalized dependency-upgrade oracle. Synthetic models ONLY.

No package installation, scanner, registry, network access or production writes.
Real lockfiles must be interpreted using the actual package manager.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "dependency-maintenance"
VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){2}$")
DECISIONS = {"UPGRADE_RECOMMENDED", "UPGRADE_OPTIONAL", "DEFER", "REPLACE",
             "REMOVE", "BLOCKED", "INSUFFICIENT_EVIDENCE"}
STATES = {"INVENTORIED", "ASSESSMENT_PREPARED", "CHANGE_PROPOSED",
          "CHANGE_APPLIED_LOCALLY", "TESTED", "READY_FOR_REVIEW",
          "MERGED", "RELEASED", "ROLLBACK_REQUIRED", "ROLLED_BACK", "BLOCKED"}
ADVISORIES = {"ADVISORY_CONFIRMED", "ADVISORY_NOT_VERIFIED",
              "NO_KNOWN_ADVISORY_IN_CHECKED_SOURCES"}
APPLICABILITY = {"PACKAGE_AFFECTED", "NOT_AFFECTED_BY_RANGE",
                 "APPLICABILITY_UNKNOWN"}
DIMENSIONS = {"runtime", "os", "framework", "database", "api", "build",
              "container", "browser", "toolchain", "deployment"}
CHECKS = {"SUPPORTED_BY_SOURCE", "TESTED_PASS", "TESTED_FAIL",
          "NOT_TESTED", "UNKNOWN", "NOT_APPLICABLE"}
SCOPES = {"production", "development", "build", "optional", "platform", "toolchain"}
CHANGE_KEYS = ("id", "category", "old_version", "new_version", "direct",
               "scope", "source_changed", "checksum_changed",
               "license_changed")


def load(name="ordinary"):
    return json.loads((FIXTURES / (name + ".json")).read_text(encoding="utf-8"))


def patch(source, changes):
    """Apply fixture mutations to a COPY; validator has no mutant-specific branches."""
    result = copy.deepcopy(source)
    for entry in changes:
        keys = entry["path"].split(".")
        node = result
        for key in keys[:-1]:
            node = node[int(key)] if isinstance(node, list) else node[key]
        key = int(keys[-1]) if isinstance(node, list) else keys[-1]
        if entry.get("delete"):
            if isinstance(node, list):
                del node[key]
            else:
                node.pop(key, None)
        else:
            node[key] = entry["value"]
    return result


def version(value):
    """SemVer-like fixture versions; NOT a real ecosystem resolver."""
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise ValueError("unsupported synthetic version")
    return tuple(map(int, value.split(".")))


def affected(candidate, introduced, fixed):
    return version(introduced) <= version(candidate) < version(fixed)


def graph_index(rows):
    if not isinstance(rows, list):
        raise ValueError("graph must be a list")
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("non-object graph node")
        key = row.get("id")
        if not isinstance(key, str) or not key or key in result:
            raise ValueError("missing/duplicate package ID")
        if not isinstance(row.get("direct"), bool) or row.get("scope") not in SCOPES:
            raise ValueError("invalid dependency metadata")
        for field in ("version", "source", "checksum", "license"):
            if not isinstance(row.get(field), str) or not row[field]:
                raise ValueError("incomplete graph node: " + field)
        version(row["version"])
        result[key] = row
    return result


def graph_diff(old, new):
    """Normalized snapshot comparison: includes indirect changes and provenance."""
    changes = {}
    for ident in sorted(old.keys() | new.keys()):
        a, b = old.get(ident), new.get(ident)
        if a == b:
            continue
        category = "ADDED" if a is None else "REMOVED" if b is None else "MODIFIED"
        changes[ident] = {
            "id": ident, "category": category,
            "old_version": a["version"] if a else None,
            "new_version": b["version"] if b else None,
            "direct": b["direct"] if b else a["direct"],
            "scope": b["scope"] if b else a["scope"],
            "source_changed": bool(a and b and a["source"] != b["source"]),
            "checksum_changed": bool(a and b and a["checksum"] != b["checksum"]),
            "license_changed": bool(a and b and a["license"] != b["license"]),
            "old_source": a["source"] if a else None,
            "new_source": b["source"] if b else None,
            "old_checksum": a["checksum"] if a else None,
            "new_checksum": b["checksum"] if b else None,
            "old_license": a["license"] if a else None,
            "new_license": b["license"] if b else None,
        }
    return changes


def inspect(data):
    errors = set()

    def bad(code, condition):
        if condition:
            errors.add(code)

    if not isinstance(data, dict):
        return ["SCHEMA"]
    bad("ORIGIN", data.get("origin") != "SYNTHETIC")
    bad("ECOSYSTEM_CLAIM", data.get("claims", {}).get("real_lockfile_parser") is not False)
    bad("ASSESSMENT", not all(data.get(k) for k in
        ("assessment_id", "project", "ecosystem", "package", "source_sha")))
    bad("STATUS", data.get("change_status") not in STATES or
        data.get("decision") not in DECISIONS)
    bad("SOURCE_REVISION", not data.get("source_sha", "").startswith("synthetic-"))
    try:
        old = graph_index(data["old_graph"])
        new = graph_index(data["new_graph"])
        expected = graph_diff(old, new)
    except (ValueError, KeyError, TypeError):
        return sorted(errors | {"GRAPH_SCHEMA"})
    manifest = data.get("manifest", {})
    primary = data.get("package")
    bad("UNKNOWN_CURRENT_VERSION", primary not in old or
        not data.get("current_resolved"))
    if primary in old:
        bad("CURRENT_RESOLVED_MISMATCH", data.get("current_resolved") != old[primary]["version"])
        bad("MANIFEST_LOCK_MISMATCH", manifest.get("old", {}).get(primary) != old[primary]["version"])
    if primary in new:
        bad("CANDIDATE_RESOLVED_MISMATCH", data.get("candidate_version") != new[primary]["version"])
        bad("MANIFEST_LOCK_MISMATCH", manifest.get("new", {}).get(primary) != new[primary]["version"])
    bad("UNKNOWN_TRANSITIVES", data.get("transitive_status") not in
        {"COMPLETE_SYNTHETIC_GRAPH", "UNKNOWN"} or
        (data.get("transitive_status") == "UNKNOWN" and
         data.get("decision") == "UPGRADE_RECOMMENDED"))
    actual = data.get("reported_changes")
    if not isinstance(actual, list) or any(not isinstance(x, dict) for x in actual):
        errors.add("DIFF_SCHEMA")
    else:
        recorded = {x.get("id"): x for x in actual}
        bad("HIDDEN_TRANSITIVE", set(recorded) != set(expected) or
            len(recorded) != len(expected))
        for ident in expected.keys() & recorded.keys():
            bad("LOCKFILE_DIFF", any(recorded[ident].get(k) != v
                for k, v in expected[ident].items()))
            item = recorded[ident]
            bad("DIFF_EVIDENCE", not item.get("reason") or not item.get("evidence")
                or not item.get("risk"))
            bad("SOURCE_CHANGE", expected[ident]["source_changed"] and
                not item.get("supply_chain_reviewed"))
            bad("CHECKSUM_CHANGE", expected[ident]["checksum_changed"] and
                not item.get("checksum_reviewed"))
            bad("LICENSE_CHANGE", expected[ident]["license_changed"] and
                not item.get("license_reviewed"))
    changed = set(expected)
    plan = data.get("plan", {})
    authorized = plan.get("components", [])
    bad("MASS_UPGRADE", not isinstance(authorized, list) or
        set(authorized) != changed or len(authorized) != len(changed) or
        plan.get("strategy") not in {"MINIMAL", "COORDINATED"} or
        (plan.get("strategy") == "COORDINATED" and not plan.get("coordination_reason")))
    bad("UPGRADE_REASON", not data.get("upgrade_reason", {}).get("project_impact")
        or not data.get("upgrade_reason", {}).get("source")
        or not data.get("upgrade_reason", {}).get("reason"))
    notes = data.get("changelog", {})
    bad("RELEASE_NOTES", notes.get("status") not in
        {"SOURCE_CONFIRMED", "PARTIAL", "UNKNOWN", "NOT_CHECKED"} or
        (notes.get("status") == "SOURCE_CONFIRMED" and not notes.get("evidence")))
    bad("UNVERIFIED_RELEASE_NOTES", notes.get("status") in {"UNKNOWN", "NOT_CHECKED"}
        and data.get("decision") == "UPGRADE_RECOMMENDED")
    contracts = data.get("contracts", {})
    bad("BREAKING_API", bool(set(contracts.get("required_by_consumer", [])) -
        set(contracts.get("provided_by_candidate", []))))
    bad("BREAKING_CHANGE_REVIEW", notes.get("breaking_changes") is None)
    runtime = data.get("runtime", {})
    try:
        incompatible = version(runtime["target"]) < version(runtime["candidate_minimum"])
    except (KeyError, ValueError, TypeError):
        incompatible = True
        errors.add("RUNTIME_SCHEMA")
    bad("UNSUPPORTED_RUNTIME", incompatible and
        data.get("decision") not in {"BLOCKED", "DEFER", "REPLACE"})
    rows = data.get("compatibility_matrix", [])
    bad("COMPATIBILITY_MATRIX", not isinstance(rows, list) or not rows or
        not any(r.get("dimension") == "runtime" and
        r.get("value") == runtime.get("target") for r in rows))
    for r in rows:
        bad("COMPATIBILITY_MATRIX", r.get("dimension") not in DIMENSIONS or
            r.get("source_status") not in CHECKS or
            r.get("test_status") not in CHECKS)
        bad("COMPATIBILITY_EVIDENCE", r.get("test_status") == "TESTED_PASS"
            and not r.get("test_id"))
    advisory = data.get("advisory", {})
    status = advisory.get("status")
    applicability = advisory.get("applicability")
    bad("ADVISORY_STATUS", status not in ADVISORIES or applicability not in APPLICABILITY)
    if status == "ADVISORY_CONFIRMED":
        try:
            is_affected = (advisory.get("package") == primary and
                           affected(data["current_resolved"],
                                    advisory["introduced"], advisory["fixed"]))
        except (ValueError, KeyError, TypeError):
            is_affected = None
            errors.add("ADVISORY_RANGE")
        if is_affected is not None:
            bad("AFFECTED_RANGE", applicability !=
                ("PACKAGE_AFFECTED" if is_affected else "NOT_AFFECTED_BY_RANGE"))
        bad("ADVISORY_EVIDENCE", not advisory.get("source") or
            not advisory.get("evidence_id"))
        if is_affected and data.get("decision") == "UPGRADE_RECOMMENDED":
            try:
                bad("FIX_VERSION", version(data["candidate_version"]) <
                    version(advisory["fixed"]))
            except (ValueError, KeyError, TypeError):
                errors.add("FIX_VERSION")
    else:
        bad("UNVERIFIED_ADVISORY", applicability != "APPLICABILITY_UNKNOWN")
        bad("FALSE_ADVISORY_CLAIM", status == "ADVISORY_NOT_VERIFIED" and
            data.get("decision") == "UPGRADE_RECOMMENDED" and
            data.get("upgrade_reason", {}).get("reason") == "SECURITY")
    if advisory.get("evidence_id"):
        bad("EVIDENCE_REFERENCE", advisory["evidence_id"] not in data.get("evidence", {}))
    testing = data.get("tests", {})
    required = set(testing.get("required", []))
    executed = testing.get("executed", [])
    proof = data.get("evidence", {})
    if not isinstance(executed, list) or not isinstance(proof, dict):
        errors.add("TEST_SCHEMA")
        executed = []
        proof = {}
    seen = set()
    for test in executed:
        test_id = test.get("id")
        seen.add(test_id)
        fact = proof.get(test.get("evidence_id"))
        bad("FALSE_TEST_PASS", test.get("outcome") != "PASS" or
            not isinstance(fact, dict) or fact.get("kind") != "test_execution" or
            fact.get("test_id") != test_id or fact.get("executed") is not True or
            fact.get("result") != "PASS")
    bad("MISSING_REGRESSION", not required.issubset(seen) or
        not set(contracts.get("critical_test_ids", [])).issubset(required))
    for r in rows:
        if r.get("test_status") == "TESTED_PASS":
            bad("COMPATIBILITY_EVIDENCE", r.get("test_id") not in seen)
    if data.get("change_status") in {"TESTED", "READY_FOR_REVIEW", "MERGED", "RELEASED"}:
        bad("MISSING_TEST_EVIDENCE", not executed or not required.issubset(seen))
    approval = data.get("approval", {})
    if data.get("change_status") not in {"INVENTORIED", "ASSESSMENT_PREPARED",
                                         "CHANGE_PROPOSED", "BLOCKED"}:
        bad("UNAUTHORIZED_APPLY", approval.get("status") != "APPROVED" or
            not approval.get("evidence_id") or
            approval["evidence_id"] not in proof)
    rollback = data.get("rollback", {})
    bad("ROLLBACK_INCOMPLETE", not rollback.get("old_manifest_revision") or
        not rollback.get("old_lockfile_revision") or
        not rollback.get("old_source_sha") or
        not rollback.get("verification_test") or
        rollback.get("old_source_sha") != data.get("source_sha"))
    bad("IRREVERSIBLE_MIGRATION", rollback.get("data_migration_reversible") is False
        and rollback.get("status") != "ROLLBACK_BLOCKED")
    bad("FALSE_RELEASE", data.get("change_status") in {"RELEASED", "ROLLED_BACK"}
        and not data.get("release", {}).get("production_verification"))
    bad("MISSING_EVIDENCE", not proof or not data.get("lockfile_revision")
        or not data.get("limitations"))
    return sorted(errors)


def evaluate():
    result = {}
    for name in ("ordinary", "security"):
        result[name] = inspect(load(name))
    mutants = json.loads((FIXTURES / "broken_cases.json").read_text(encoding="utf-8"))["cases"]
    result["broken"] = [
        {"id": case["id"], "errors": inspect(patch(load(case["base"]), case["changes"])),
         "expected": case["expected_error"]}
        for case in mutants
    ]
    return result


def main():
    results = evaluate()
    assert not results["ordinary"], results["ordinary"]
    assert not results["security"], results["security"]
    for item in results["broken"]:
        assert item["expected"] in item["errors"], item
    print("DEPENDENCY_MAINTENANCE=PASS references=2 broken=" +
          str(len(results["broken"])) + " real_upgrades=0 network=0")


if __name__ == "__main__":
    main()
