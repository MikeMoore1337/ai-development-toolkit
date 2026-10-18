#!/usr/bin/env python3
"""Offline, source-only ADT #11 / Hermes #349 compatibility gate.

Reads a pinned local Hermes checkout as DATA (AST); never imports Hermes,
invokes an agent, communicates with providers, or enables a worker.
A clean source contract is not evidence of OS isolation or model efficacy.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import subprocess
import sys

from agent_eval_fixtures import FIXTURES

ROOT = Path(__file__).resolve().parents[1]
HERMES_PIN = "db7ed22d4faef39af3d5aafa0cc6f20b91b23a3a"
FLAGS = (
    "--provider", "--model", "--cases", "--trials", "--max-seconds",
    "--output", "--execute", "--acknowledge-costs", "--acknowledge-isolation",
)
PROVIDERS = frozenset({"codex", "claude"})
KIND = "adt_skill_eval_pilot_v1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_ast(root: Path, name: str) -> ast.Module:
    path = root / name
    require(path.is_file() and not path.is_symlink() and
            path.resolve().is_relative_to(root.resolve()), "unsafe_or_missing_source:" + name)
    require(path.stat().st_size < 200_000, "unbounded_source:" + name)
    return ast.parse(path.read_text(encoding="utf-8"), filename=name)


def assignment(tree: ast.Module, name: str) -> ast.expr:
    matches = [
        node.value for node in tree.body
        if isinstance(node, ast.Assign) and
        any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
    ]
    require(len(matches) == 1, "missing_or_duplicated_constant:" + name)
    return matches[0]


def constant_set(tree: ast.Module, name: str) -> frozenset[str]:
    value = assignment(tree, name)
    require(isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and
            value.func.id == "frozenset" and len(value.args) == 1 and not value.keywords,
            "unsupported_constant_set:" + name)
    try:
        result = ast.literal_eval(value.args[0])
    except (TypeError, ValueError, SyntaxError) as exc:
        raise ValueError("nonliteral_constant_set:" + name) from exc
    require(isinstance(result, (set, tuple, list)) and
            all(type(item) is str for item in result),
            "invalid_constant_set:" + name)
    return frozenset(result)


def function(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = [node for node in tree.body
               if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(matches) == 1, "missing_function:" + name)
    return matches[0]


def direct_call(statement: ast.stmt, name: str) -> bool:
    return (isinstance(statement, ast.Expr) and
            isinstance(statement.value, ast.Call) and
            isinstance(statement.value.func, ast.Name) and
            statement.value.func.id == name)


def frozen(tree: ast.Module, guard_name: str) -> bool:
    value = assignment(tree, guard_name)
    return isinstance(value, ast.Constant) and value.value is True


def pinned_clean_checkout(root: Path, expected_sha: str) -> None:
    require(re.fullmatch(r"[0-9a-f]{40}", expected_sha) is not None,
            "invalid_expected_sha")
    require(root.is_absolute() and root.is_dir() and not root.is_symlink() and
            (root / ".git").exists() and not (root / ".git").is_symlink(),
            "hermes_checkout_required")
    for command, label in (
        (["git", "-C", str(root), "rev-parse", "HEAD"], "hermes_revision_unavailable"),
        (["git", "-C", str(root), "rev-parse", "--show-toplevel"], "hermes_root_unavailable"),
        (["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
         "hermes_cleanliness_unavailable"),
    ):
        try:
            completed = subprocess.run(command, capture_output=True, text=True,
                                       timeout=10, check=True)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError(label) from exc
        if label == "hermes_revision_unavailable":
            require(completed.stdout.strip() == expected_sha, "hermes_sha_mismatch")
        elif label == "hermes_root_unavailable":
            require(Path(completed.stdout.strip()).resolve() == root.resolve(),
                    "hermes_root_mismatch")
        else:
            require(not completed.stdout.strip(), "hermes_checkout_dirty")


def inspect_hermes(root: Path, *, expected_sha: str = HERMES_PIN) -> dict:
    """Verify static interop, without loading or executing Hermes code."""
    root = root.resolve(strict=True) if not root.is_symlink() else root
    pinned_clean_checkout(root, expected_sha)
    protocol = read_ast(root, "eval_lane/protocol.py")
    plan = read_ast(root, "eval_lane/fixed_plan.py")
    adapter = read_ast(root, "eval_lane/local_executor.py")
    hermes_lock = read_ast(root, "eval_lane/owner_spend_lock.py")
    toolkit = read_ast(ROOT, "scripts/agent_eval_runner.py")

    kind = assignment(protocol, "KIND")
    require(isinstance(kind, ast.Constant) and kind.value == KIND,
            "hermes_job_kind_drift")
    require(constant_set(protocol, "CASES") == frozenset(FIXTURES),
            "hermes_case_registry_drift")
    require(constant_set(protocol, "PROVIDERS") == PROVIDERS,
            "hermes_provider_registry_drift")
    require(frozen(hermes_lock, "OWNER_REAL_AGENT_EXECUTION_LOCKED") and
            frozen(toolkit, "OWNER_REAL_AGENT_EXECUTION_LOCKED"),
            "owner_execution_freeze_removed")

    exec_body = function(toolkit, "execute").body
    require(bool(exec_body) and
            direct_call(exec_body[0], "require_owner_real_execution_permission"),
            "toolkit_execution_guard_moved")
    methods = [
        node for cls in adapter.body if isinstance(cls, ast.ClassDef)
        and cls.name == "LocalBoundedExecutor"
        for node in cls.body if isinstance(node, ast.FunctionDef)
        and node.name == "__call__"
    ]
    require(len(methods) == 1 and len(methods[0].body) >= 2 and
            direct_call(methods[0].body[1], "assert_owner_real_execution_allowed"),
            "hermes_execution_guard_moved")

    plan_fn = function(plan, "fixed_plan")
    assignments = [
        node.value for node in plan_fn.body if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "argv" for t in node.targets)
    ]
    require(len(assignments) == 1 and isinstance(assignments[0], ast.Tuple),
            "hermes_argv_no_longer_fixed_tuple")
    actual_flags = tuple(
        element.value for element in assignments[0].elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
        and element.value.startswith("--")
    )
    require(actual_flags == FLAGS, "hermes_cli_flags_drift")
    runner_options = {
        arg.value for call in ast.walk(function(toolkit, "main"))
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
        and call.func.attr == "add_argument"
        for arg in call.args[:1]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
    }
    require(set(FLAGS).issubset(runner_options), "toolkit_cli_flags_drift")
    return {
        "classification": "PINNED_SOURCE_ONLY_HERMES_ADT_CONTRACT_NOT_MODEL_EVAL",
        "hermes_source_sha": expected_sha,
        "cases": sorted(FIXTURES),
        "providers": sorted(PROVIDERS),
        "argv_contract": "MATCH",
        "source_execution_guards": "PRESENT_STATICALLY_NOT_EXECUTED",
        "real_agent_trials": 0,
        "real_agent_outcomes": "NOT_MEASURED",
        "isolation_proof": "NOT_PERFORMED",
        "provider_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-root", type=Path, required=True,
                        help="Clean checkout of the pinned public Hermes source revision")
    args = parser.parse_args()
    try:
        report = inspect_hermes(args.hermes_root)
    except (OSError, ValueError, SyntaxError, UnicodeError) as exc:
        print("FAIL: offline Hermes contract: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
