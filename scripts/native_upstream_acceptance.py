#!/usr/bin/env python3
"""Bounded, real-CLI acceptance for #492. No Codex/Claude/model execution.

This script runs genuine installed upstream commands in disposable directories,
then exercises both live Toolkit MCP stdio servers and the optional Stop hook.
It verifies a bounded *non-model* workflow, NOT the behavior of Codex Desktop
or the full upstream agent/plugin lifecycle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PERSONAL = ROOT / "integrations/personal-mcp/adt-personal/mcp/adt_mcp.py"
PROJECT = ROOT / "scripts/toolkit_mcp.py"
STOP_HOOK = ROOT / "integrations/personal-mcp/adt-personal/hooks/model_advisor_stop_hook.py"
HARNESS_SHA = "1cfe254e8d25b15f37048c3730134686abe60335"
MAX_CAPTURE = 2_000_000
CLEAN_ENV_KEYS = (
    "HOME", "PATH", "LANG", "LC_ALL", "TMPDIR", "TMP", "TEMP",
    "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "SYSTEMROOT",
    "WINDIR", "COMSPEC",
)
PROVIDER_ENV = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
                "GOOGLE_APPLICATION_CREDENTIALS", "GROQ_API_KEY",
                "OPENROUTER_API_KEY", "CODEX_HOME")


class AcceptanceError(RuntimeError):
    pass


def clean_env() -> dict[str, str]:
    env = {key: os.environ[key] for key in CLEAN_ENV_KEYS if key in os.environ}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               NO_COLOR="1", CI="true")
    if any(key in env for key in PROVIDER_ENV):
        raise AcceptanceError("Provider keys leaked into subprocess environment")
    return env


def execute(argv: list[str], *, cwd: Path = ROOT, stdin: str | None = None,
            timeout: int = 180) -> tuple[str, str]:
    result = subprocess.run(
        argv, cwd=cwd, env=clean_env(), input=stdin, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=timeout,
        check=False)
    if result.returncode:
        raise AcceptanceError(
            f"Command {Path(argv[0]).name!r} exited {result.returncode}: "
            f"{result.stderr[:450]!r} / {result.stdout[:250]!r}")
    if len(result.stdout.encode("utf-8")) + len(result.stderr.encode("utf-8")) > MAX_CAPTURE:
        raise AcceptanceError("Oversized upstream output")
    return result.stdout.replace("\r\n", "\n"), result.stderr.replace("\r\n", "\n")


def assert_passthrough(response: dict, *, controller: str) -> None:
    if response.get("status") != "NATIVE_UPSTREAM_PASSTHROUGH" or response.get("controller") != controller:
        raise AcceptanceError(f"No native passthrough ({response.get('status')})")
    for key in ("skills", "priority_skills", "selected_skills", "roles",
                "loaded_skills", "loaded_roles", "suggested_skills"):
        if response.get(key) != []:
            raise AcceptanceError(f"Unexpected Toolkit overlay: {key}")
    if response.get("execution") != "NOT_RUN" or response.get("project_files_changed") is not False:
        raise AcceptanceError("Toolkit execution or project mutation not excluded")
    if response.get("required_setup", {}).get("status") != "SKIPPED_EXTERNAL_NATIVE":
        raise AcceptanceError("Toolkit attempted native tool setup")
    if response.get("toolkit_hook_injection") != "SKIPPED":
        raise AcceptanceError("Toolkit hook was not excluded")


def mcp_client(script: Path, controller: str, project: bool) -> dict:
    cases = [
        ("toolkit_route_task", {"task": "Review my Python modules", "external_controller": controller}),
        ("toolkit_prepare_stage", {"task": "Review my Python modules", "stage": "inspect",
                                   "requested_skills": ["implementation"],
                                   "external_controller": controller}),
        ("toolkit_route_task", {"task": "Build and test a backend API"}),
        ("toolkit_route_task", {"task": "Review safely", "external_controller": "../bad"}),
    ]
    if not project:
        cases.insert(1, ("toolkit_prepare_task", {"task": "Review my Python modules",
                                                    "proactive_model_advice": True,
                                                    "external_controller": controller}))
    requests = [
        {"jsonrpc": "2.0", "id": i + 1, "method": "tools/call",
         "params": {"name": name, "arguments": arguments}}
        for i, (name, arguments) in enumerate(cases)
    ]
    command = [sys.executable, "-B", str(script)]
    command += ["serve"] if project else ["--source", str(ROOT)]
    stdout, _ = execute(command, stdin="".join(json.dumps(r) + "\n" for r in requests), timeout=60)
    try:
        responses = [json.loads(line) for line in stdout.splitlines()]
    except json.JSONDecodeError as exc:
        raise AcceptanceError("MCP server returned invalid JSON-RPC") from exc
    if len(responses) != len(requests) or [r.get("id") for r in responses] != [r["id"] for r in requests]:
        raise AcceptanceError("MCP response count or IDs do not match")
    for i, ((name, args), response) in enumerate(zip(cases, responses)):
        if i == len(cases) - 1:
            if response.get("result", {}).get("isError") is not True:
                raise AcceptanceError("Malformed external controller did not fail closed")
            continue
        result = response.get("result", {}).get("structuredContent")
        if not isinstance(result, dict):
            raise AcceptanceError(f"No structured MCP response for {name}")
        if args.get("external_controller"):
            assert_passthrough(result, controller=controller)
        elif result.get("status") == "NATIVE_UPSTREAM_PASSTHROUGH" or not result.get("skills"):
            raise AcceptanceError("Normal Toolkit routing was lost")
    return {"stdio_invocation": "OBSERVED",
            "native_passthrough": "PASS",
            "normal_toolkit_routing": "PASS",
            "malformed_controller": "REJECTED",
            "requests": len(requests)}


def check_hook() -> dict:
    report = "Release BLOCKED: confirmed security defect, rollback race, concurrency issue."
    def invoke(message: str, *, repeated: bool = False) -> dict:
        request = {"hook_event_name": "Stop", "stop_hook_active": repeated,
                   "last_assistant_message": message}
        stdout, _ = execute(
            [sys.executable, "-B", str(STOP_HOOK)], stdin=json.dumps(request), timeout=10)
        return json.loads(stdout)
    if invoke(report) != {}:
        raise AcceptanceError("Model Advisor hook intercepted a native report")
    marker = "<!-- ADT-MODEL-ADVISOR-ACTIVE -->"
    if invoke("External quoted text:\n" + marker + report) != {}:
        raise AcceptanceError("Hook reacted to a quoted marker")
    scoped = invoke(marker + "\n" + report)
    if scoped.get("decision") != "block":
        raise AcceptanceError("Explicit Toolkit-owned hook scope no longer operates")
    if invoke(marker + "\n" + report, repeated=True) != {}:
        raise AcceptanceError("Stop hook loop guard failed")
    return {"native_report_interference": "NONE",
            "opt_in_scope": "WORKS_WITH_MARKER",
            "recursive_stop": "DENIED"}


def graph_summary(working: Path) -> dict:
    path = working / "graphify-out" / "graph.json"
    if not path.is_file() or path.stat().st_size > MAX_CAPTURE:
        raise AcceptanceError("Original Graphify did not create graphify-out/graph.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AcceptanceError("Invalid native Graphify graph JSON")
    nodes = data.get("nodes")
    edges = data.get("links", data.get("edges"))
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise AcceptanceError("Unsupported native Graphify graph representation")
    if not nodes or not edges:
        raise AcceptanceError("Upstream code-only graph must include nodes and relationships")
    def category_counts(rows: list) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            if not isinstance(row, dict):
                raise AcceptanceError("Graph elements must be objects")
            kind = str(row.get("type", row.get("kind", "unknown")))
            counts[kind] = counts.get(kind, 0) + 1
        return dict(sorted(counts.items()))
    return {"nodes": len(nodes), "edges": len(edges),
            "node_categories": category_counts(nodes),
            "edge_categories": category_counts(edges)}


def graph_fixture(root: Path) -> None:
    root.mkdir()
    (root / "service.py").write_text(
        "class Meter:\n"
        "    def double(self, value: int) -> int:\n"
        "        return value * 2\n", encoding="utf-8")
    (root / "entry.py").write_text(
        "from service import Meter\n"
        "def compute(value: int) -> int:\n"
        "    return Meter().double(value)\n", encoding="utf-8")
    (root / ".gitignore").write_text("graphify-out/\n", encoding="utf-8")
    execute(["git", "init", "-q", str(root)])
    execute(["git", "-C", str(root), "add", "service.py", "entry.py", ".gitignore"])
    execute(["git", "-C", str(root), "-c", "user.email=ci@example.invalid",
             "-c", "user.name=Integration Acceptance",
             "commit", "-qm", "fixture"])


def native_checks(tool: str, executable: Path, working: Path, *, source: Path | None = None) -> dict:
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise AcceptanceError("Missing executable for real upstream CLI")
    if tool == "graphify":
        commands = [[str(executable), "--version"], [str(executable), "--help"]]
    elif tool == "harness2":
        if source is None or not source.is_dir():
            raise AcceptanceError("Native Harness2 source checkout must be specified")
        sha, _ = execute(["git", "-C", str(source), "rev-parse", "HEAD"])
        if sha.strip() != HARNESS_SHA:
            raise AcceptanceError("Harness2 source revision does not match upstream pin")
        commands = [[str(executable), "--help"],
                    [str(executable.parent / "harness2-judge"), "--help"],
                    [str(executable.parent / "harness2-setup"), "lab", "--dry-run"]]
    else:
        raise AcceptanceError("Tool must be graphify or harness2")
    outputs = [execute(cmd, cwd=working, timeout=120) for cmd in commands]
    result = {"commands": [" ".join(Path(x).name for x in cmd[:1]) + " " + " ".join(cmd[1:]) for cmd in commands],
              "output_digests": [
                  hashlib.sha256((stdout + "\n" + stderr).encode("utf-8")).hexdigest()
                  for stdout, stderr in outputs
              ],
              "native_cli": "INVOKED",
              "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest()}
    if tool == "graphify":
        execute([str(executable), "extract", ".", "--code-only", "--no-cluster"],
                cwd=working, timeout=180)
        result["graph"] = graph_summary(working)
    else:
        result["source_revision"] = HARNESS_SHA
    return result


def run(tool: str, executable: Path, source: Path | None) -> dict:
    with tempfile.TemporaryDirectory(prefix="adt-native-492-") as temp:
        tempdir = Path(temp)
        baseline = tempdir / "original_only"
        overlay = tempdir / "toolkit_present"
        if tool == "graphify":
            graph_fixture(baseline)
            graph_fixture(overlay)
        else:
            baseline.mkdir()
            overlay.mkdir()
        input_hashes = {
            p: [hashlib.sha256((root / p).read_bytes()).hexdigest() for root in (baseline, overlay)]
            for p in ("entry.py", "service.py") if tool == "graphify"
        }
        before = native_checks(tool, executable, baseline, source=source)
        servers = {
            "personal_mcp": mcp_client(PERSONAL, tool, project=False),
            "project_mcp": mcp_client(PROJECT, tool, project=True),
            "stop_hook": check_hook(),
        }
        after = native_checks(tool, executable, overlay, source=source)
        if before != after:
            # Binary hash, native CLI outputs and semantic extracted graph must match.
            raise AcceptanceError("Native upstream command/graph changed when Toolkit was available")
        for name, expected in input_hashes.items():
            if expected != [hashlib.sha256((root / name).read_bytes()).hexdigest()
                            for root in (baseline, overlay)]:
                raise AcceptanceError("Fixture source was modified during acceptance")
        if source is not None:
            tracked, _ = execute(["git", "-C", str(source), "status",
                                  "--porcelain", "--untracked-files=no"])
            if tracked.strip():
                raise AcceptanceError("Native upstream checkout mutated tracked files")
        return {
            "schema": "adt-issue492-native-upstream-acceptance-v1",
            "status": "PASS",
            "tool": tool,
            "native_invocation": "CONFIRMED_BOUNDED_NON_MODEL_COMMANDS",
            "original_source": "UPSTREAM_PACKAGE_NOT_PATCHED_BY_TOOLKIT",
            "baseline_vs_toolkit": "EQUIVALENT_FOR_TESTED_COMMANDS",
            "native_evidence": before,
            "toolkit_checks": servers,
            "codex_desktop": "NOT_RUN",
            "full_agent_or_plugin_hooks": "NOT_VERIFIED",
            "model_execution": "NOT_RUN",
            "paid_api_calls": "NOT_RUN",
            "host_injection": "NOT_OBSERVED_OUTSIDE_TEST_HARNESS",
            "warning": "No claim about arbitrary upstream modes or actual Codex Desktop controller selection.",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", choices=("graphify", "harness2"), required=True)
    parser.add_argument("--native-bin", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.tool, args.native_bin.resolve(strict=True),
                     args.source.resolve(strict=True) if args.source else None)
    except (AcceptanceError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        report = {"schema": "adt-issue492-native-upstream-acceptance-v1",
                  "status": "FAIL", "tool": args.tool,
                  "error_type": type(exc).__name__, "reason": str(exc)[:700],
                  "codex_desktop": "NOT_RUN", "model_execution": "NOT_RUN"}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("NATIVE_492_STATUS=" + report["status"])
    print("NATIVE_492_TOOL=" + args.tool)
    print("NATIVE_492_EVIDENCE=" + str(args.report))
    if report["status"] != "PASS":
        print("NATIVE_492_ERROR=" + report.get("reason", "unknown")[:350], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
