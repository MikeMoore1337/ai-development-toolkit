#!/usr/bin/env python3
"""Run paired REAL Codex / Claude CLI attempts against isolated synthetic projects.

Requires explicit --execute + cost and isolation acknowledgements. Never
claims model performance or independent skill activation from presence alone.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from agent_eval_fixtures import FIXTURES, init_git, materialize, oracle_command, snapshot_digest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "minimal-safe-change"
MAX_OUTPUT = 1_000_000

# OWNER POLICY (2026-10-18): zero incremental spending; not an environment,
# command-line or untrusted task option. Future unfreezing requires a reviewed
# code change and a new explicit owner decision backed by zero-charge evidence.
OWNER_REAL_AGENT_EXECUTION_LOCKED = True


def require_owner_real_execution_permission() -> None:
    if OWNER_REAL_AGENT_EXECUTION_LOCKED:
        raise ValueError("owner_zero_incremental_spend_execution_frozen")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_checked(argv: list[str], cwd: Path, seconds: int, *,
                environment: dict[str, str] | None = None) -> dict:
    start = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=cwd, env=environment, check=False,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=seconds)
        return {
            "returncode": result.returncode, "timed_out": False,
            "duration_seconds": round(time.monotonic() - start, 3),
            "stdout": result.stdout[:MAX_OUTPUT].decode("utf-8", "replace"),
            "stderr": result.stderr[:MAX_OUTPUT].decode("utf-8", "replace"),
            "output_truncated": (len(result.stdout) > MAX_OUTPUT
                                 or len(result.stderr) > MAX_OUTPUT),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "returncode": None, "timed_out": True,
            "duration_seconds": round(time.monotonic() - start, 3),
            "stdout": (exc.stdout or b"")[:MAX_OUTPUT].decode("utf-8", "replace"),
            "stderr": (exc.stderr or b"")[:MAX_OUTPUT].decode("utf-8", "replace"),
            "output_truncated": True,
        }


def agent_command(provider: str, model: str, workspace: Path, prompt: str,
                  max_turns: int) -> list[str]:
    if provider == "codex":
        return ["codex", "exec", "--cd", str(workspace),
                "--sandbox", "workspace-write", "--ephemeral", "--json",
                "--model", model, prompt]
    if provider == "claude":
        return ["claude", "-p", prompt, "--model", model, "--output-format", "json",
                "--max-turns", str(max_turns), "--permission-mode", "dontAsk",
                "--tools", "Read,Edit,Write"]
    raise ValueError(f"Unknown provider: {provider}")


def assert_safe_outdir(output: Path) -> None:
    if output.exists():
        raise ValueError("Refusing to overwrite existing evidence output directory")
    if output.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Evidence output must live outside the public toolkit repository")
    for parent in (output, *output.parents):
        if parent.exists() and (parent.is_symlink() or parent.is_junction()):
            raise ValueError(f"Linked evidence output path: {parent}")


def source_hash(path: Path) -> str:
    sha = hashlib.sha256()
    for file in sorted(path.rglob("*")):
        if file.is_symlink() or file.is_junction():
            raise ValueError("Linked skill source is not permitted")
        if file.is_file():
            sha.update(file.relative_to(path).as_posix().encode("utf-8") + b"\0")
            sha.update(file.read_bytes())
    return sha.hexdigest()


def diff_snapshot(before: dict[str, str], workspace: Path, case_id: str) -> str:
    """Record changed tracked source and new files without following links."""
    segments = []
    excluded = {".git", ".agents", ".claude", ".empty-hooks"}
    root = workspace.resolve()
    for name, original in sorted(before.items()):
        path = workspace / name
        if (path.is_symlink() or path.is_junction()
                or not path.resolve().is_relative_to(root)):
            segments.append(f"UNSAFE_REPLACEMENT: {name}\n")
            continue
        after = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        if original != after:
            segments.extend(difflib.unified_diff(
                original.splitlines(keepends=True), after.splitlines(keepends=True),
                fromfile=f"before/{name}", tofile=f"after/{name}"))
    for path in sorted(workspace.rglob("*")):
        relative = path.relative_to(workspace)
        if set(relative.parts).intersection(excluded):
            continue
        name = relative.as_posix()
        if name in before or name == FIXTURES[case_id]["oracle_path"]:
            continue
        if path.is_symlink() or path.is_junction():
            segments.append(f"UNEXPECTED_LINK: {name}\n")
        elif path.is_file():
            segments.append(f"UNEXPECTED_FILE: {name} "
                            f"sha256={hashlib.sha256(path.read_bytes()).hexdigest()}\n")
    return "".join(segments) or "(no changes to initial project files)\n"

def prepare_oracle_destination(workspace: Path, case_id: str) -> Path:
    """Fail closed if an agent has planted links or precreated oracle content.

    An agent-modified workspace is untrusted even when the initial fixture was
    safe. Never follow links while introducing the previously hidden oracle.
    """
    root = workspace.resolve()
    for item in workspace.rglob("*"):
        if item.is_symlink() or item.is_junction():
            raise ValueError(f"Agent workspace contains unsafe link: {item}")
    oracle = workspace / FIXTURES[case_id]["oracle_path"]
    if oracle.exists() or oracle.is_symlink() or oracle.is_junction():
        raise ValueError(f"Agent precreated oracle path, refusing overwrite: {oracle}")
    if not oracle.resolve().is_relative_to(root):
        raise ValueError("Oracle path escapes the disposable workspace")
    oracle.parent.mkdir(parents=True, exist_ok=True)
    return oracle


def build_prompt(case_id: str) -> str:
    return (
        "Fix the following small repository task. Stay inside this scratch repo; "
        "do not install dependencies, access external data, deploy, push, or use secrets. "
        "Use only its current language standard library. Keep the public API stable. "
        "Consult any applicable project skills if available. "
        "Describe the change and exactly which checks you actually ran.\n\n"
        + FIXTURES[case_id]["task"]
    )


def preflight(provider: str, cases: list[str]) -> dict:
    tool = shutil.which(provider)
    return {
        "provider": provider, "cli_found": bool(tool),
        "cli_path": tool, "skill_found": (SKILL / "SKILL.md").is_file(),
        "cases": {key: {
            "initial_snapshot_sha256": snapshot_digest(key),
            "language": FIXTURES[key]["language"],
            "oracle_runtime_found": bool(shutil.which(
                {"python": Path(sys.executable).name, "javascript": "node", "go": "go"}[
                    FIXTURES[key]["language"]]
            )) if FIXTURES[key]["language"] != "python" else Path(sys.executable).is_file(),
        } for key in cases},
        "ready_to_attempt": bool(tool and (SKILL / "SKILL.md").is_file()),
        "no_agents_invoked": True,
    }


def _evidence_file(run_path: Path, name: str, body: str) -> str:
    path = run_path / name
    path.write_text(body if body else "(empty)\n", encoding="utf-8")
    return path.name


def execute(provider: str, model: str, cases: list[str], trials: int,
            output: Path, max_seconds: int, oracle_seconds: int,
            max_turns: int) -> dict:
    # Guard direct Python calls as well as CLI --execute. Zero calls, zero writes.
    require_owner_real_execution_permission()
    assert_safe_outdir(output)
    check = preflight(provider, cases)
    if not check["ready_to_attempt"]:
        raise ValueError("Selected agent CLI or candidate skill not installed")
    if not all(x["oracle_runtime_found"] for x in check["cases"].values()):
        raise ValueError("Required Python/Node/Go oracle runtime not available")
    output.mkdir(parents=True)
    manifest = {
        "schema_version": 1, "dataset": "adt-controlled-pilot-v1",
        "provider": provider, "model": model, "skill": "minimal-safe-change",
        "skill_sha256": source_hash(SKILL),
        "start_utc": utc_now(), "executed": True,
        "independent_review": "NOT_PERFORMED", "records": [],
    }
    (output / "preflight.json").write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
    binary = shutil.which(provider)
    version = run_checked([binary, "--version"], ROOT, seconds=20)
    manifest["client_version_output"] = version["stdout"].strip() or version["stderr"].strip()
    for case_id in cases:
        for trial in range(1, trials + 1):
            # Order alternates to reduce systematic start-order bias.
            variants = ("baseline", "candidate") if trial % 2 else ("candidate", "baseline")
            for variant in variants:
                run_id = f"{case_id}-t{trial}-{variant}"
                entry = output / run_id
                entry.mkdir()
                workspace = entry / "workspace"
                materialize(case_id, workspace)
                sha = init_git(workspace)
                if variant == "candidate":
                    prefix = ".agents" if provider == "codex" else ".claude"
                    destination = workspace / prefix / "skills" / "minimal-safe-change"
                    destination.parent.mkdir(parents=True)
                    shutil.copytree(SKILL, destination, symlinks=False)
                prompt = build_prompt(case_id)
                _evidence_file(entry, "prompt.txt", prompt)
                command = agent_command(provider, model, workspace, prompt, max_turns)
                started = utc_now()
                result = run_checked(command, workspace, seconds=max_seconds)
                _evidence_file(entry, "agent.stdout.txt", result.pop("stdout"))
                _evidence_file(entry, "agent.stderr.txt", result.pop("stderr"))
                diff = diff_snapshot(FIXTURES[case_id]["files"], workspace, case_id)
                _evidence_file(entry, "source.diff", diff)
                # Only expose oracle after agent has exited or hit the timeout.
                oracle = prepare_oracle_destination(workspace, case_id)
                oracle.write_text(FIXTURES[case_id]["oracle"], encoding="utf-8", newline="\n")
                env = os.environ.copy()
                env["PYTHONPATH"] = str(workspace)
                env["GOPROXY"] = "off"
                env["GOSUMDB"] = "off"
                outcome = run_checked(oracle_command(case_id), workspace,
                                      seconds=oracle_seconds, environment=env)
                _evidence_file(entry, "oracle.stdout.txt", outcome.pop("stdout"))
                _evidence_file(entry, "oracle.stderr.txt", outcome.pop("stderr"))
                record = {
                    "case_id": case_id, "trial": trial, "variant": variant,
                    "fixture_commit_sha": sha,
                    "fixture_snapshot_sha256": snapshot_digest(case_id),
                    "cli_started_utc": started, "cli": result, "oracle": outcome,
                    "skill_installed": variant == "candidate",
                    "skill_activation_observed": None,
                    "accepted": None, "regressions": None, "unsafe_actions": None,
                    "tokens": None, "independent_review": "PENDING",
                    "evidence": [f"{run_id}/{p}" for p in (
                        "prompt.txt", "source.diff", "agent.stdout.txt",
                        "agent.stderr.txt", "oracle.stdout.txt", "oracle.stderr.txt")],
                }
                record["evidence_sha256"] = {
                    relative: hashlib.sha256((output / relative).read_bytes()).hexdigest()
                    for relative in record["evidence"]
                }
                (entry / "observation.json").write_text(
                    json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
                manifest["records"].append(record)
                (output / "observations.json").write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    manifest["end_utc"] = utc_now()
    (output / "observations.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"executed": True, "records": len(manifest["records"]),
            "output": str(output), "independent_review": "NOT_PERFORMED"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--provider", choices=("codex", "claude"), required=True)
    p.add_argument("--model", help="Exact model identifier; mandatory for real runs")
    p.add_argument("--cases", nargs="+", choices=sorted(FIXTURES), default=sorted(FIXTURES))
    p.add_argument("--trials", type=int, default=2)
    p.add_argument("--max-seconds", type=int, default=300)
    p.add_argument("--oracle-seconds", type=int, default=30)
    p.add_argument("--max-turns", type=int, default=8)
    p.add_argument("--output", type=Path)
    p.add_argument("--execute", action="store_true", help="Actually call billable agent CLI")
    p.add_argument("--acknowledge-costs", action="store_true")
    p.add_argument("--acknowledge-isolation", action="store_true",
                   help="Confirm running on a disposable, externally isolated computer/VM")
    args = p.parse_args()
    try:
        if not args.execute:
            print(json.dumps(preflight(args.provider, args.cases), indent=2))
            return 0
        if not args.acknowledge_costs or not args.acknowledge_isolation:
            raise ValueError("Live runs require both cost and isolation acknowledgements")
        if not args.model or not args.output:
            raise ValueError("Live runs require --model and --output")
        if args.trials < 1 or args.trials > 5 or not 30 <= args.max_seconds <= 900:
            raise ValueError("Trials must be 1-5; agent timeout must be 30-900s")
        if not 5 <= args.oracle_seconds <= 120 or not 1 <= args.max_turns <= 30:
            raise ValueError("Invalid oracle timeout or agent turn budget")
        info = execute(args.provider, args.model, args.cases, args.trials,
                       args.output.expanduser(), args.max_seconds,
                       args.oracle_seconds, args.max_turns)
        print(json.dumps(info, indent=2))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
