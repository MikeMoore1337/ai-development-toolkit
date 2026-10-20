#!/usr/bin/env python3
"""Offline provenance inventory and release preflight. This is NOT legal verification."""
from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from datetime import date
import json
from pathlib import Path, PurePosixPath
import re
import sys

from verify_checksums import canonical_bytes

ROOT = Path(__file__).resolve().parents[1]
REGISTER = "provenance/skills.json"
ORIGINS = {"original", "adapted", "redistributed", "inspired_by", "unknown"}
STATUSES = {"verified", "documented", "requires_owner_review", "restricted", "unknown", "not_applicable"}
DISTRIBUTION = {"included", "owner_gate", "excluded"}
KINDS = {"skill", "role", "recipe", "script", "template", "reference", "asset", "profile", "documentation", "test", "workflow", "metadata"}
SKIP = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", ".hermes-compat"}
SHA = re.compile(r"[a-fA-F0-9]{40}\Z")
SPDX = re.compile(r"(?:MIT|Apache-2\.0|BSD-2-Clause|BSD-3-Clause|CC0-1\.0|CC-BY-4\.0|ISC|MPL-2\.0|GPL-3\.0-only|NOASSERTION|NONE)\Z")
FIELDS = {"id", "path", "name", "kind", "author", "origin", "source_url", "source_reference", "source_revision", "license", "distribution_basis", "attribution_required", "attribution_path", "status", "evidence", "last_reviewed", "distribution", "notes"}

# Project-specific sensitive distribution scopes. A missing approval or a
# rewritten origin field must not turn the previously gated files into
# automatically permitted "original" content. This is an anti-accident guard,
# NOT tamper-proof approval authority: code, registry and CI must be reviewed.
REVIEW_REQUIRED_PATH = "extensions/make-feature/skills/make-feature"
REVIEW_REQUIRED_PREFIXES = (
    "extensions/qa/skills/",
    "extensions/qa/roles/",
    "extensions/qa/recipes/",
    "assets/branding/",
)


def requires_owner_review(path: str) -> bool:
    return path == REVIEW_REQUIRED_PATH or any(
        path.startswith(prefix) for prefix in REVIEW_REQUIRED_PREFIXES
    )



def safe_path(root: Path, name: object) -> Path | None:
    if not isinstance(name, str) or not name or "\\" in name or name.startswith("/"):
        return None
    pure = PurePosixPath(name)
    if any(part in {"", ".", ".."} for part in name.split("/")) or pure.is_absolute():
        return None
    target = root.joinpath(*pure.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        return None
    for node in [target, *list(target.parents)]:
        if node == root.parent:
            break
        if node.is_symlink():
            return None
    return target


def files_in_package(root: Path) -> set[str]:
    results: set[str] = set()
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in SKIP for part in rel.parts):
            continue
        if path.is_file() or path.is_symlink():
            results.add(rel.as_posix())
    return results


def skill_dirs(root: Path, manifest: dict) -> set[str]:
    found: set[str] = set()
    roots = [manifest["skill_root"]] + [
        config["skill_root"] for config in manifest.get("extension_packs", {}).values()
    ]
    for location in roots:
        base = safe_path(root, location)
        if base is None or not base.is_dir():
            raise ValueError(f"Invalid skill root: {location}")
        for directory in base.iterdir():
            if directory.is_dir():
                found.add(directory.relative_to(root).as_posix())
    return found


def validate(root: Path = ROOT, mode: str = "inventory") -> dict:
    root = root.resolve()
    errors: list[str] = []
    def fail(code: str, message: str) -> None:
        errors.append(f"{code}: {message}")

    register = safe_path(root, REGISTER)
    try:
        if register is None or not register.is_file():
            raise ValueError("missing or unsafe registry")
        data = json.loads(register.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("components"), list):
            raise ValueError("expected schema_version=1 and components array")
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        return {"ok": False, "mode": mode, "counts": {}, "issues": [f"REGISTRY: {exc}"]}
    try:
        manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
        expected_skills = skill_dirs(root, manifest)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return {"ok": False, "mode": mode, "counts": {}, "issues": [f"MANIFEST: {exc}"]}

    approvals = data.get("owner_review_record")
    approved = {}
    if approvals is not None:
        if not isinstance(approvals, dict) or not isinstance(approvals.get("id"), str) or (
            approvals.get("review_outcomes") != "permitted"
        ) or approvals.get("source") != "owner_reported" or (
            not isinstance(approvals.get("approved_components"), dict)
        ):
            fail("OWNER_RECORD", "invalid approval record or missing explicit owner decision")
        else:
            approved = approvals["approved_components"]

    # The baseline remains immutable. Later user-approved changes must be
    # exact-file pinned. New scope is limited to Markdown QA skill references.
    amended_files = {}
    added_files = {}
    amendments = data.get("owner_review_amendments", [])
    if not isinstance(amendments, list):
        fail("OWNER_AMENDMENT", "owner_review_amendments must be an array")
        amendments = []
    original = {name: digest for snapshot in approved.values()
                if isinstance(snapshot, dict) for name, digest in snapshot.items()}
    for index, amendment in enumerate(amendments):
        if not isinstance(amendment, dict):
            fail("OWNER_AMENDMENT", f"amendment[{index}]: invalid map")
            continue
        changes = amendment.get("approved_files")
        additions = amendment.get("added_files", {})
        predecessors = amendment.get("supersedes_files", {})
        if (not isinstance(approvals, dict)
                or amendment.get("parent_review_id") != approvals.get("id")
                or amendment.get("source") != "owner_reported"
                or amendment.get("review_outcomes") != "permitted"
                or not isinstance(amendment.get("scope_issue"), str)
                or not amendment["scope_issue"].startswith("#")
                or not isinstance(changes, dict) or not isinstance(additions, dict)
                or not isinstance(predecessors, dict) or not (changes or additions)):
            fail("OWNER_AMENDMENT", f"amendment[{index}]: invalid owner decision/scope")
            continue
        if set(predecessors) - set(changes):
            fail("OWNER_CHAIN", f"amendment[{index}]: orphan supersession")
        if additions and (not isinstance(amendment.get("scope_description"), str)
                          or not amendment["scope_description"].strip()
                          or not isinstance(amendment.get("reported_at"), str)
                          or not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", amendment["reported_at"])):
            fail("OWNER_AMENDMENT", f"amendment[{index}]: addition lacks review context")
            continue
        for name, digest in changes.items():
            if name not in original or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                fail("OWNER_AMENDMENT", f"amendment[{index}]: unexpected changed path: {name!r}")
                continue
            if name in amended_files and predecessors.get(name) != amended_files[name]:
                fail("OWNER_CHAIN", f"amendment[{index}]: wrong prior hash: {name}")
                continue
            if name not in amended_files and name in predecessors:
                fail("OWNER_CHAIN", f"amendment[{index}]: unnecessary prior hash: {name}")
                continue
            amended_files[name] = digest
        for name, digest in additions.items():
            match = re.fullmatch(
                r"extensions/qa/skills/([a-z0-9]+(?:-[a-z0-9]+)*)/references/[A-Za-z0-9_-]+[.]md",
                name) if isinstance(name, str) else None
            parent = f"extensions/qa/skills/{match.group(1)}" if match else None
            if (not match or parent not in approved or name in original
                    or name in added_files or not isinstance(digest, str)
                    or not re.fullmatch(r"[0-9a-f]{64}", digest)):
                fail("OWNER_AMENDMENT", f"amendment[{index}]: unreviewed added path: {name!r}")
                continue
            added_files[name] = digest

    # Approval claims, scope and classifications must agree even when a
    # previously adapted component is relabelled "original" or "verified".
    classifications = {}
    if approvals is not None and approved:
        classifications = approvals.get("approved_metadata")
        if not isinstance(classifications, dict) or set(classifications) != set(approved):
            fail("OWNER_CLASSIFICATION", "approved_metadata must match approved component paths")
            classifications = {}
    records = data["components"]
    covered: set[str] = set()
    skill_records: set[str] = set()
    ids: set[str] = set()
    declared_paths: set[str] = set()
    counts: Counter[str] = Counter()
    for number, item in enumerate(records):
        label = f"component[{number}]"
        if not isinstance(item, dict):
            fail("SCHEMA", f"{label}: expected object")
            continue
        missing = FIELDS - item.keys()
        if missing:
            fail("SCHEMA", f"{label}: missing fields {sorted(missing)}")
            continue
        ident, raw_path = item["id"], item["path"]
        label = str(ident)
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", ident):
            fail("ID", f"{label}: unsafe or invalid id")
            continue
        if not isinstance(raw_path, str):
            fail("SCHEMA", f"{label}: path must be a string")
            continue
        if ident in ids:
            fail("DUPLICATE_ID", label)
        ids.add(ident)
        if raw_path in declared_paths:
            fail("DUPLICATE_PATH", str(raw_path))
        declared_paths.add(raw_path)
        target = safe_path(root, raw_path)
        if target is None:
            fail("UNSAFE_PATH", f"{label}: {raw_path}")
            continue
        if not target.exists():
            fail("MISSING_PATH", f"{label}: {raw_path}")
            continue
        if not target.is_file() and not target.is_dir():
            fail("PATH_TYPE", f"{label}: {raw_path}")
            continue
        if not isinstance(item["kind"], str) or item["kind"] not in KINDS:
            fail("KIND", label)
        if not isinstance(item["origin"], str) or item["origin"] not in ORIGINS:
            fail("ORIGIN", label)
        if not isinstance(item["status"], str) or item["status"] not in STATUSES:
            fail("STATUS", label)
        else:
            counts[item["status"]] += 1
        if not isinstance(item["distribution"], str) or item["distribution"] not in DISTRIBUTION:
            fail("DISTRIBUTION", label)
        if not isinstance(item["name"], str) or not item["name"].strip():
            fail("NAME", label)
        if not isinstance(item["author"], str) or not item["author"].strip():
            fail("AUTHOR", label)
        if not isinstance(item["distribution_basis"], str) or not item["distribution_basis"].strip():
            fail("RIGHTS_BASIS", label)
        if not isinstance(item["notes"], str):
            fail("NOTES", label)
        if not isinstance(item["license"], str) or not SPDX.fullmatch(item["license"]):
            fail("LICENSE", f"{label}: SPDX identifier or NOASSERTION required")
        if item["source_revision"] is not None and (
            not isinstance(item["source_revision"], str) or not SHA.fullmatch(item["source_revision"])
        ):
            fail("REVISION", label)
        if item["source_url"] is not None and (
            not isinstance(item["source_url"], str) or not item["source_url"].startswith("https://")
        ):
            fail("SOURCE_URL", label)
        if isinstance(item["origin"], str) and item["origin"] in {"adapted", "redistributed"}:
            if not item["source_url"] and not item["source_reference"]:
                fail("SOURCE_MISSING", label)
            if isinstance(item["license"], str) and item["license"] in {"NONE", ""}:
                fail("LICENSE_MISSING", label)
        if item["status"] == "verified":
            if item["origin"] == "unknown" or (
                isinstance(item["license"], str) and item["license"] in {"NOASSERTION", "NONE"}
            ):
                fail("FALSE_VERIFIED", label)
            if not item["evidence"] or not item["last_reviewed"] or (
                "independently confirmed" not in item["distribution_basis"].lower()
            ):
                fail("FALSE_VERIFIED", f"{label}: verified needs independently confirmed rights evidence")
        if isinstance(item["status"], str) and item["status"] in {"unknown", "restricted", "requires_owner_review"} and item["distribution"] == "included":
            fail("UNSAFE_DISTRIBUTION", label)
        # An owner can authorize publication of a documented, externally derived
        # copy; that does NOT make its copyright/permission independently verified.
        # Freeze the exact reviewed file bytes to prevent the approval from
        # silently applying to later substitutions or new files.
        # An existing approval cannot be bypassed by changing origin/status.
        locked = (raw_path in approved or "owner_approval_id" in item
                  or requires_owner_review(raw_path))
        needs_approval = (locked or (item["distribution"] == "included"
                          and isinstance(item["origin"], str) and item["origin"] in {"adapted", "redistributed", "unknown"}))
        if needs_approval:
            if not isinstance(approvals, dict) or item.get("owner_approval_id") != approvals.get("id"):
                fail("OWNER_APPROVAL", f"{label}: explicit matching owner review required")
            if raw_path in approved:
                frozen = classifications.get(raw_path)
                fields = ("origin", "license", "status", "distribution", "kind")
                if (not isinstance(frozen, dict) or
                        any(item.get(field) != frozen.get(field) for field in fields)):
                    fail("OWNER_CLASSIFICATION", f"{label}: reviewed metadata changed")
            elif locked:
                fail("OWNER_SCOPE", f"{label}: approval reference has no matching reviewed path")
            snapshots = approved.get(raw_path)
            if not isinstance(snapshots, dict) or not snapshots:
                fail("OWNER_SCOPE", f"{label}: owner approval must pin every distributed file")
            else:
                owned_files = ([target] if target.is_file() else
                               sorted(p for p in target.rglob("*") if p.is_file() and
                                      not any(part in SKIP for part in p.relative_to(root).parts)))
                relative = {p.relative_to(root).as_posix() for p in owned_files}
                approved_additions = {p for p in added_files if p.startswith(raw_path + "/")}
                if set(snapshots) | approved_additions != relative:
                    fail("OWNER_SCOPE", f"{label}: reviewed file inventory changed")
                for owner_file in owned_files:
                    relative_path = owner_file.relative_to(root).as_posix()
                    expected = amended_files.get(relative_path, added_files.get(relative_path, snapshots.get(relative_path)))
                    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                        fail("OWNER_FINGERPRINT", f"{label}: missing or malformed reviewed SHA256 for {relative_path}")
                    elif hashlib.sha256(canonical_bytes(owner_file.read_bytes())).hexdigest() != expected:
                        fail("OWNER_FINGERPRINT", f"{label}: source contents changed: {relative_path}")
        if not isinstance(item["attribution_required"], bool):
            fail("ATTRIBUTION", f"{label}: boolean required")
        if item["attribution_required"] and not item["attribution_path"]:
            fail("ATTRIBUTION", f"{label}: required notice missing")
        for field in ("attribution_path", "evidence"):
            value = item[field]
            if value is not None:
                ref = safe_path(root, value)
                if ref is None or not ref.is_file():
                    fail("EVIDENCE_PATH", f"{label}: {field}={value}")
        if item["last_reviewed"] is not None:
            try:
                review_day = date.fromisoformat(item["last_reviewed"])
                if review_day > date.today():
                    fail("REVIEW_DATE", label)
            except (TypeError, ValueError):
                fail("REVIEW_DATE", label)
        if item["kind"] == "skill":
            skill_records.add(raw_path)
            skill_file = target / "SKILL.md"
            if not target.is_dir() or not skill_file.is_file():
                fail("SKILL_PATH", label)
            elif isinstance(item["license"], str) and item["license"] not in {"NOASSERTION", "NONE"}:
                head = skill_file.read_text(encoding="utf-8").split("---", 2)
                if len(head) >= 3:
                    match = re.search(r"(?m)^license:\s*['\"]?([^\s'\"#]+)", head[1])
                    if match and match.group(1) != item["license"]:
                        fail("LICENSE_CONFLICT", label)
        if target.is_file():
            covered.add(raw_path)
        else:
            covered.update(p.relative_to(root).as_posix() for p in target.rglob("*") if p.is_file() or p.is_symlink())
        if mode == "release" and (item["distribution"] != "included"
                                  or (isinstance(item["status"], str) and item["status"] in {"restricted", "unknown", "requires_owner_review"})):
            fail("RELEASE_BLOCKED", f"{label}: {item['status']}/{item['distribution']}")
    for path in sorted(approved):
        if path not in declared_paths:
            fail("OWNER_SCOPE", f"approval references unknown component: {path}")
    # A release archive must be link-free even if the link is nested inside
    # a registered skill directory (rather than at the directory root).
    for path in root.rglob("*"):
        if any(part in SKIP for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            fail("SYMLINK", path.relative_to(root).as_posix())
    for path in sorted(expected_skills - skill_records):
        fail("UNDECLARED_SKILL", path)
    for path in sorted(skill_records - expected_skills):
        fail("EXTRA_SKILL", path)
    actual = files_in_package(root)
    for path in sorted(actual - covered):
        fail("UNDECLARED_FILE", path)
    for path in sorted(covered - actual):
        fail("COVERAGE_MISMATCH", path)
    if not records:
        fail("EMPTY_REGISTRY", "no components")
    return {"ok": not errors, "mode": mode, "counts": dict(sorted(counts.items())),
            "total": len(records), "skills": len(skill_records), "issues": sorted(errors)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--mode", choices=("inventory", "release"), default="inventory")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = validate(args.root, args.mode)
    if args.report:
        args.report.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for issue in result["issues"]:
        print("FAIL:", issue)
    print(f"{'PASS' if result['ok'] else 'FAIL'}: provenance {args.mode}; "
          f"{result.get('total', 0)} components; {result.get('skills', 0)} skills")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
