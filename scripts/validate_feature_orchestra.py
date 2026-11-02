#!/usr/bin/env python3
"""Offline checks for a declared feature-orchestration run. Not proof of live agents."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
SHA = re.compile(r"[a-f0-9]{40}\Z")
WORKER_MODES = {"SEQUENTIAL", "ACTUAL_SUBAGENT", "GENERIC_SUBAGENT"}
CHECK_STATES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED", "UNKNOWN"}
HIGH_RISK = {"privacy", "security", "irreversible", "migration", "billing", "legal"}
GATED = {"visual", "privacy", "security", "irreversible", "billing", "legal", "release"}
ACTUAL_EVIDENCE = {"TEST_RUN", "CI_RUN", "INTEGRATION_RUN"}


def validate(data: Any) -> list[str]:
    """Reject malformed nested JSON safely instead of throwing a traceback."""
    try:
        return _validate(data)
    except (TypeError, KeyError, ValueError, AttributeError):
        return ["INVALID_INPUT_SHAPE"]


def _validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["EXPECTED_OBJECT"]
    required = {"schema_version", "task_id", "revision", "controller", "active_controllers",
                "depth", "risk_flags", "execution", "units", "acceptance",
                "evidence", "checks", "approvals", "outcome"}
    if set(data) != required:
        return ["SCHEMA_FIELDS"]
    if data["schema_version"] != 1 or not isinstance(data["task_id"], str) or not data["task_id"].strip():
        errors.append("SCHEMA_ID")
    revision = data["revision"]
    if not isinstance(revision, str) or not SHA.fullmatch(revision):
        errors.append("REVISION")
    controller = data["controller"]
    if controller not in {"feature-delivery", "make-feature"} or data["active_controllers"] != [controller]:
        errors.append("DUPLICATE_CONTROLLER")
    if data["depth"] not in {"quick", "normal", "deep"}:
        errors.append("DEPTH")
    risks = data["risk_flags"]
    if not isinstance(risks, list) or any(x not in (HIGH_RISK | GATED) for x in risks) or len(set(risks)) != len(risks):
        errors.append("RISK_FLAGS")
        risks = []
    if HIGH_RISK.intersection(risks) and data["depth"] != "deep":
        errors.append("RISK_DOWNGRADE")
    execution = data["execution"]
    if not isinstance(execution, dict) or set(execution) != {"mode", "peak"}:
        return errors + ["EXECUTION"]
    mode, peak = execution["mode"], execution["peak"]
    if mode not in {"SEQUENTIAL", "SUBAGENTS"} or type(peak) is not int or not (1 <= peak <= 3):
        errors.append("EXECUTION")
    if mode == "SEQUENTIAL" and peak != 1:
        errors.append("FAKE_PARALLELISM")
    units = data["units"]
    if not isinstance(units, list) or not (1 <= len(units) <= 12):
        return errors + ["UNITS_COUNT"]
    identities: dict[str, dict] = {}
    actual = 0
    writers = 0
    for item in units:
        if not isinstance(item, dict) or set(item) != {"id", "purpose", "role", "status",
                                                        "execution", "trace", "write_paths", "depends_on"}:
            errors.append("UNIT_FIELDS")
            continue
        uid = item["id"]
        if not isinstance(uid, str) or not ID.fullmatch(uid) or uid in identities:
            errors.append("UNIT_ID")
            continue
        identities[uid] = item
        if not isinstance(item["purpose"], str) or not item["purpose"].strip():
            errors.append("UNIT_PURPOSE")
        if not isinstance(item["role"], str) or not item["role"].strip():
            errors.append("UNIT_ROLE")
        if item["status"] not in {"PLANNED", "EXECUTED"}:
            errors.append("UNIT_STATUS")
        if item["execution"] not in WORKER_MODES:
            errors.append("UNIT_EXECUTION")
        if item["execution"] == "SEQUENTIAL":
            if item["trace"] is not None:
                errors.append("FAKE_SUBAGENT")
        else:
            if mode == "SEQUENTIAL" or item["status"] != "EXECUTED":
                errors.append("FAKE_SUBAGENT")
            if not isinstance(item["trace"], str) or not item["trace"].strip():
                errors.append("MISSING_TRACE")
            actual += 1
        paths = item["write_paths"]
        if not isinstance(paths, list) or len(set(paths)) != len(paths) or any(
            not isinstance(p, str) or not p or p.startswith("/") or
            "\\" in p or ".." in p.split("/") or "." in p.split("/") for p in paths
        ):
            errors.append("WRITE_SCOPE")
        elif paths:
            writers += 1
            if item["role"] != "implementer":
                errors.append("WRITE_OWNER")
            if item["execution"] != "SEQUENTIAL":
                errors.append("SUBAGENT_WRITE")
        if not isinstance(item["depends_on"], list) or len(set(item["depends_on"])) != len(item["depends_on"]):
            errors.append("DEPENDENCIES")
    if writers > 1:
        errors.append("CONCURRENT_WRITERS")
    if mode == "SUBAGENTS" and (actual < 1 or peak > actual):
        errors.append("FAKE_PARALLELISM")
    graph = {}
    for uid, unit in identities.items():
        dependencies = unit["depends_on"]
        if not isinstance(dependencies, list):
            continue
        graph[uid] = dependencies
        for dep in dependencies:
            if dep == uid or dep not in identities:
                errors.append("INVALID_DEPENDENCY")
            elif unit["status"] == "EXECUTED" and identities[dep]["status"] != "EXECUTED":
                errors.append("DEPENDENCY_NOT_COMPLETE")
    temporary: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in temporary:
            errors.append("DEPENDENCY_CYCLE")
            return
        if node in visited:
            return
        temporary.add(node)
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep)
        temporary.remove(node)
        visited.add(node)

    for uid in graph:
        visit(uid)
    approvals = data["approvals"]
    if not isinstance(approvals, list):
        return errors + ["APPROVALS"]
    gate_status: dict[str, str] = {}
    for approval in approvals:
        if not isinstance(approval, dict) or set(approval) != {"gate", "status", "reference"}:
            errors.append("APPROVAL_FIELDS")
            continue
        gate = approval["gate"]
        if gate not in GATED or gate in gate_status:
            errors.append("APPROVAL_ID")
            continue
        gate_status[gate] = approval["status"]
        if approval["status"] not in {"PENDING", "ACCEPTED", "REJECTED"}:
            errors.append("APPROVAL_STATUS")
        if approval["status"] == "ACCEPTED" and (
            not isinstance(approval["reference"], str) or not approval["reference"].strip()
        ):
            errors.append("UNVERIFIED_APPROVAL")
        if approval["status"] != "ACCEPTED" and approval["reference"] is not None:
            errors.append("APPROVAL_REFERENCE")
    for risk in risks:
        if risk in GATED and risk not in gate_status:
            errors.append("MISSING_GATE")
    acceptance = data["acceptance"]
    if not isinstance(acceptance, list) or not acceptance:
        return errors + ["ACCEPTANCE"]
    acs: dict[str, dict] = {}
    for ac in acceptance:
        if not isinstance(ac, dict) or set(ac) != {"id", "requirement", "check_ids"}:
            errors.append("ACCEPTANCE_FIELDS")
            continue
        aid = ac["id"]
        if not isinstance(aid, str) or not ID.fullmatch(aid) or aid in acs:
            errors.append("ACCEPTANCE_ID")
            continue
        acs[aid] = ac
        if not isinstance(ac["requirement"], str) or not ac["requirement"].strip():
            errors.append("ACCEPTANCE_REQUIREMENT")
        if not isinstance(ac["check_ids"], list) or not ac["check_ids"] or len(set(ac["check_ids"])) != len(ac["check_ids"]):
            errors.append("ACCEPTANCE_CHECKS")
    evidence = data["evidence"]
    if not isinstance(evidence, list):
        return errors + ["EVIDENCE"]
    recorded: dict[str, dict] = {}
    for row in evidence:
        if not isinstance(row, dict) or set(row) != {"id", "kind", "revision", "reference"}:
            errors.append("EVIDENCE_FIELDS")
            continue
        eid = row["id"]
        if not isinstance(eid, str) or not ID.fullmatch(eid) or eid in recorded:
            errors.append("EVIDENCE_ID")
            continue
        recorded[eid] = row
        if row["kind"] not in ACTUAL_EVIDENCE | {"CODE_INSPECTION", "SYNTHETIC"}:
            errors.append("EVIDENCE_KIND")
        if row["revision"] != revision:
            errors.append("STALE_EVIDENCE")
        if not isinstance(row["reference"], str) or not row["reference"].strip():
            errors.append("EVIDENCE_REFERENCE")
    checks = data["checks"]
    if not isinstance(checks, list) or not checks:
        return errors + ["CHECKS"]
    by_id: dict[str, dict] = {}
    for check in checks:
        if not isinstance(check, dict) or set(check) != {"id", "status", "evidence_ids"}:
            errors.append("CHECK_FIELDS")
            continue
        cid = check["id"]
        if not isinstance(cid, str) or not ID.fullmatch(cid) or cid in by_id:
            errors.append("CHECK_ID")
            continue
        by_id[cid] = check
        if check["status"] not in CHECK_STATES:
            errors.append("CHECK_STATUS")
        links = check["evidence_ids"]
        if not isinstance(links, list) or any(k not in recorded for k in links):
            errors.append("EVIDENCE_LOOKUP")
            continue
        if check["status"] in {"PASS", "FAIL"} and not any(
            recorded[k]["kind"] in ACTUAL_EVIDENCE for k in links
        ):
            errors.append("FALSE_EXECUTION")
    for ac in acs.values():
        for cid in ac["check_ids"]:
            if cid not in by_id:
                errors.append("MISSING_AC_CHECK")
    if data["outcome"] not in {"PLAN_ONLY", "BLOCKED", "READY_FOR_REVIEW"}:
        errors.append("OUTCOME")
    if data["outcome"] == "READY_FOR_REVIEW" and (
        errors or any(u["status"] != "EXECUTED" for u in identities.values())
        or any(c["status"] != "PASS" for c in by_id.values())
        or not acs or any(x != "ACCEPTED" for x in gate_status.values())
    ):
        errors.append("PREMATURE_READY")
    if data["outcome"] == "PLAN_ONLY" and any(
        c["status"] == "PASS" for c in by_id.values()
    ):
        errors.append("PLAN_CANNOT_PASS")
    return sorted(set(errors))



# Optional static multi-worktree preflight (#440). This is NOT an execution runtime.
import os
import subprocess
import unicodedata

_BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}\Z")
_WINDOWS_DEVICE = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?\Z", re.I)


def _portable_path(value: object, *, directory: bool = False) -> bool:
    if not isinstance(value, str) or not (1 <= len(value) <= 240):
        return False
    candidate = value[:-1] if directory and value.endswith("/") else value
    parts = candidate.split("/")
    return bool(candidate) and all(
        part not in ("", ".", "..") and part.casefold() != ".git"
        and not _WINDOWS_DEVICE.fullmatch(part)
        and not part.endswith((".", " "))
        and not any(ord(char) < 32 or char in '\\:*?"<>|' for char in part)
        for part in parts
    )


def _path_key(value: str) -> str:
    return unicodedata.normalize("NFC", value.rstrip("/")).casefold()


def _write_overlap(left: str, right: str) -> bool:
    a, b = _path_key(left), _path_key(right)
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def validate_parallel_plan(data: Any, *, git_root: Path | None = None) -> list[str]:
    """Validate candidates, not executed agents. Optionally inspect an explicit Git root read-only."""
    try:
        return _validate_parallel_plan(data, git_root=git_root)
    except (TypeError, KeyError, ValueError, AttributeError, OSError, subprocess.SubprocessError):
        return ["INVALID_PARALLEL_INPUT"]


def _validate_parallel_plan(data: Any, *, git_root: Path | None) -> list[str]:
    fields = {"schema_version", "revision", "controller", "active_controllers",
              "runtime_state", "tasks"}
    if not isinstance(data, dict) or set(data) != fields:
        return ["PARALLEL_SCHEMA"]
    errors: list[str] = []
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        errors.append("PARALLEL_SCHEMA_VERSION")
    revision = data["revision"]
    if not isinstance(revision, str) or not SHA.fullmatch(revision):
        errors.append("PARALLEL_REVISION")
    if data["controller"] != "feature-delivery" or data["active_controllers"] != ["feature-delivery"]:
        errors.append("DUPLICATE_CONTROLLER")
    if data["runtime_state"] != "CLIENT_RUNTIME_NOT_VERIFIED":
        errors.append("UNVERIFIED_RUNTIME_CLAIM")
    tasks = data["tasks"]
    if not isinstance(tasks, list) or not (2 <= len(tasks) <= 12):
        return sorted(set(errors + ["PARALLEL_TASK_COUNT"]))
    identifiers: dict[str, dict] = {}
    workspaces: set[str] = set()
    branches: set[str] = set()
    for item in tasks:
        expected = {"id", "base_sha", "branch", "worktree", "writer", "write_paths",
                    "shared_contracts", "depends_on", "acceptance"}
        if not isinstance(item, dict) or set(item) != expected:
            errors.append("PARALLEL_TASK_FIELDS")
            continue
        uid = item["id"]
        if not isinstance(uid, str) or not ID.fullmatch(uid) or uid in identifiers:
            errors.append("PARALLEL_TASK_ID")
            continue
        identifiers[uid] = item
        if not isinstance(item["base_sha"], str) or item["base_sha"] != revision:
            errors.append("STALE_TASK_SHA")
        branch, workspace, writer = item["branch"], item["worktree"], item["writer"]
        if (not isinstance(branch, str) or not _BRANCH.fullmatch(branch)
            or not _portable_path(branch) or branch.endswith(".lock")
            or branch.casefold() in {"main", "master", "head"}
            or branch.startswith("refs/") or ".." in branch
            or any(part.startswith(".") or part.casefold().endswith(".lock")
                   for part in branch.split("/"))):
            errors.append("UNSAFE_BRANCH")
        else:
            key = _path_key(branch)
            if key in branches:
                errors.append("DUPLICATE_BRANCH")
            elif any(_write_overlap(key, previous) for previous in branches):
                errors.append("BRANCH_NAMESPACE_COLLISION")
            branches.add(key)
        if not _portable_path(workspace):
            errors.append("UNSAFE_WORKTREE_PATH")
        else:
            key = _path_key(workspace)
            if key in workspaces:
                errors.append("WORKTREE_COLLISION")
            workspaces.add(key)
        if not isinstance(writer, str) or not ID.fullmatch(writer):
            errors.append("WRITER_ID")
        paths = item["write_paths"]
        if not isinstance(paths, list) or not (1 <= len(paths) <= 24) or any(
                not _portable_path(p, directory=True) for p in paths):
            errors.append("WRITE_SCOPE")
        elif len({_path_key(p) for p in paths}) != len(paths):
            errors.append("WRITE_SCOPE_DUPLICATE")
        contracts = item["shared_contracts"]
        if not isinstance(contracts, list) or len(contracts) > 16 or any(
                not isinstance(c, str) or not ID.fullmatch(c) for c in contracts):
            errors.append("SHARED_CONTRACTS")
        elif len(set(contracts)) != len(contracts):
            errors.append("SHARED_CONTRACTS")
        dependencies = item["depends_on"]
        if not isinstance(dependencies, list) or len(dependencies) > 12 or any(
                not isinstance(d, str) or not ID.fullmatch(d) for d in dependencies):
            errors.append("DEPENDENCIES")
        elif len(set(dependencies)) != len(dependencies):
            errors.append("DEPENDENCIES")
        acceptance = item["acceptance"]
        if not isinstance(acceptance, list) or not (1 <= len(acceptance) <= 12) or any(
                not isinstance(a, str) or not a.strip() or len(a) > 300 for a in acceptance):
            errors.append("ACCEPTANCE")
    graph: dict[str, list[str]] = {}
    for uid, task in identifiers.items():
        deps = task["depends_on"]
        if isinstance(deps, list) and all(isinstance(d, str) for d in deps):
            graph[uid] = deps
            if uid in deps or any(dep not in identifiers for dep in deps):
                errors.append("INVALID_DEPENDENCY")
    pending: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in pending:
            errors.append("DEPENDENCY_CYCLE")
            return
        if node in visited:
            return
        pending.add(node)
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep)
        pending.remove(node)
        visited.add(node)

    for uid in graph:
        visit(uid)

    def ordered(before: str, after: str) -> bool:
        seen: set[str] = set()
        queue = list(graph.get(after, []))
        while queue:
            current = queue.pop()
            if current == before:
                return True
            if current not in seen:
                seen.add(current)
                queue.extend(dep for dep in graph.get(current, []) if dep not in seen)
        return False

    for i, left in enumerate(tasks):
        if not isinstance(left, dict) or left.get("id") not in identifiers:
            continue
        for right in tasks[i + 1:]:
            if not isinstance(right, dict) or right.get("id") not in identifiers:
                continue
            if (isinstance(left.get("worktree"), str) and isinstance(right.get("worktree"), str)
                and _portable_path(left["worktree"]) and _portable_path(right["worktree"])
                and _write_overlap(left["worktree"], right["worktree"])):
                errors.append("WORKTREE_COLLISION")
            if (isinstance(left.get("writer"), str) and left.get("writer") == right.get("writer")
                and not (ordered(left["id"], right["id"]) or ordered(right["id"], left["id"]))):
                errors.append("WRITER_REUSED")
            if isinstance(left.get("write_paths"), list) and isinstance(right.get("write_paths"), list):
                for a in left["write_paths"]:
                    for b in right["write_paths"]:
                        if isinstance(a, str) and isinstance(b, str) and _write_overlap(a, b):
                            errors.append("OVERLAPPING_WRITE_SCOPE")
            a_contracts, b_contracts = left.get("shared_contracts"), right.get("shared_contracts")
            if (isinstance(a_contracts, list) and isinstance(b_contracts, list)
                and all(isinstance(x, str) for x in a_contracts + b_contracts)
                and set(a_contracts) & set(b_contracts)
                and not (ordered(left["id"], right["id"]) or ordered(right["id"], left["id"]))):
                errors.append("UNORDERED_SHARED_CONTRACT")
    if git_root is not None:
        errors.extend(_git_preflight(git_root, revision, tasks))
    return sorted(set(errors))


def _git_preflight(root: Path, revision: str, tasks: list[dict]) -> list[str]:
    """Only Git metadata reads. No worktree add/remove, branch changes or cleanup."""
    if not isinstance(root, Path) or not root.is_absolute() or not root.is_dir():
        return ["GIT_ROOT_INVALID"]
    current = root
    while True:
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            return ["GIT_PATH_LINKED"]
        if current == current.parent:
            break
        current = current.parent
    metadata = root / ".git"
    if metadata.is_symlink() or (hasattr(metadata, "is_junction") and metadata.is_junction()):
        return ["GIT_METADATA_LINKED"]
    if not metadata.is_dir() and not metadata.is_file():
        return ["GIT_METADATA_UNAVAILABLE"]
    # Prevent inherited Git trace/config/repository environment from redirecting
    # reads or writing trace files outside this explicitly requested checkout.
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"

    def git(*args: str) -> str:
        cmd = ["git", "-c", "core.fsmonitor=false", "-C", str(root), *args]
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=10, env=env, check=False)
        if process.returncode:
            raise ValueError("GIT_READ_FAILED")
        return process.stdout.strip()

    try:
        top = Path(git("rev-parse", "--show-toplevel")).resolve()
        common = git("rev-parse", "--git-common-dir")
        head = git("rev-parse", "HEAD")
        dirty = git("status", "--porcelain=v1", "--untracked-files=all")
        listing = git("worktree", "list", "--porcelain")
        refs = git("show-ref", "--heads")
        if top != root.resolve() or not common:
            return ["GIT_ROOT_MISMATCH"]
    except (OSError, ValueError, subprocess.SubprocessError):
        return ["GIT_STATE_UNAVAILABLE"]
    problems: list[str] = []
    if head != revision:
        problems.append("STALE_GIT_HEAD")
    if dirty:
        problems.append("DIRTY_GIT_STATE")
    records: list[dict[str, str]] = []
    for block in listing.split("\n\n"):
        if not block.strip():
            continue
        row = {}
        for line in block.splitlines():
            if " " in line:
                key, value = line.split(" ", 1)
            else:
                key, value = line, ""
            if key not in {"worktree", "HEAD", "branch", "detached", "locked", "prunable", "bare"}:
                problems.append("UNKNOWN_WORKTREE_METADATA")
            row[key] = value
        if not row.get("worktree") or not row.get("HEAD"):
            problems.append("INVALID_WORKTREE_METADATA")
        records.append(row)
    if not records or len(records) > 128:
        problems.append("INVALID_WORKTREE_METADATA")
    known_branches = {_path_key(line.split("refs/heads/", 1)[1])
                      for line in refs.splitlines() if "refs/heads/" in line}
    active_branches = {_path_key(record["branch"][len("refs/heads/"):])
                       for record in records if record.get("branch", "").startswith("refs/heads/")}
    active_paths = {_path_key(record["worktree"].replace(chr(92), "/"))
                    for record in records if record.get("worktree")}
    for task in tasks:
        if not isinstance(task, dict):
            continue
        branch, relative = task.get("branch"), task.get("worktree")
        if isinstance(branch, str):
            if _path_key(branch) in active_branches:
                problems.append("BRANCH_ALREADY_CHECKED_OUT")
            elif _path_key(branch) in known_branches:
                problems.append("BRANCH_ALREADY_EXISTS")
            elif any(_write_overlap(branch, existing)
                     for existing in known_branches | active_branches):
                problems.append("BRANCH_NAMESPACE_COLLISION")
        if not _portable_path(relative):
            continue
        candidate = root.parent.joinpath(*relative.split("/"))
        if _path_key(str(candidate.resolve()).replace(chr(92), "/")) in active_paths:
            problems.append("WORKTREE_ALREADY_REGISTERED")
        current = candidate
        while current != root.parent and current != current.parent:
            if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
                problems.append("WORKTREE_PATH_LINKED")
                break
            current = current.parent
        if candidate.exists() or candidate.is_symlink():
            problems.append("WORKTREE_PATH_OCCUPIED")
    return sorted(set(problems))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--parallel-plan", action="store_true", help="Read-only #440 plan preflight")
    parser.add_argument("--git-root", type=Path, help="Explicit Git root for read-only state checks; only with --parallel-plan")
    args = parser.parse_args()
    try:
        if args.git_root is not None and not args.parallel_plan:
            raise ValueError("--git-root requires --parallel-plan")
        if args.parallel_plan and args.report.stat().st_size > 65536:
            raise ValueError("Parallel plan is too large")
        data = json.loads(args.report.read_text(encoding="utf-8"))
        issues = validate_parallel_plan(data, git_root=args.git_root) if args.parallel_plan else validate(data)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"INVALID_INPUT: {exc}")
        return 2
    for issue in issues:
        print(f"FAIL: {issue}")
    if issues:
        return 1
    if args.parallel_plan:
        print("PASS: STATIC_PLAN_VALIDATED; GIT_STATE=" +
              ("READ_ONLY_CHECKED" if args.git_root else "NOT_VERIFIED") +
              "; CLIENT_RUNTIME_NOT_VERIFIED; NATIVE_SUBAGENTS_NOT_VERIFIED; MODEL_EXECUTION_NOT_RUN")
    else:
        print("PASS: internal declarations consistent; actual tool runs and authority NOT authenticated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
