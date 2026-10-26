#!/usr/bin/env python3
"""Generate an opt-in local Cordis MCP bundle; never install it into Harness.

All paths are absolute and taken from this trusted checkout and the selected
Python interpreter. Preview is read-only; --apply writes only a new output
directory outside the Toolkit source. No subprocesses, APIs or client calls.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
TOOLKIT = SOURCE.parents[1]
SERVER = TOOLKIT / "scripts" / "toolkit_mcp.py"
FILES = ("package.json", "locale/en.json", "locale/ru.json", "icon.svg")


class BundleError(ValueError):
    """Unsafe or unsupported output configuration."""


def _safe_output(output: Path) -> Path:
    output = output.expanduser().absolute()
    if not output.name or output == output.parent:
        raise BundleError("Output must be a new directory")
    for part in (output, *output.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise BundleError("Symlink or junction output path refused")
    if output.exists():
        raise BundleError("Output already exists; refusing overwrite")
    if not output.parent.is_dir():
        raise BundleError("Output parent must already exist")
    if output.is_relative_to(TOOLKIT):
        raise BundleError("Refusing to store generated bundle inside Toolkit")
    return output


def plan(output: Path, *, python: Path | None = None) -> dict:
    if sys.version_info < (3, 12):
        raise BundleError("Python 3.12+ required")
    target = _safe_output(output)
    executable = (python or Path(sys.executable)).expanduser().absolute()
    if not executable.is_file():
        raise BundleError("Python executable must be an existing file")
    if not SERVER.is_file():
        raise BundleError("Existing Toolkit MCP server not found")
    return {
        "status": "PLAN_ONLY",
        "destination": str(target),
        "python": str(executable),
        "mcp_server": str(SERVER),
        "server_name": "adt",
        "files": ["package.json", "cordis.patch.yml", "locale/en.json", "locale/ru.json", "icon.svg"],
        "writes_toolkit": False,
        "changes_harness_profile": False,
        "runs_models_or_paid_api": False,
    }


def _patch(python: str, server: str) -> str:
    # JSON strings and arrays are also YAML scalar/flow syntax. No shell parsing.
    return (
        "- insert:\n"
        "    - id: adt-mcp\n"
        "      name: '@deepseek-ai/dsh-mcp-client'\n"
        "      config:\n"
        "        serverName: adt\n"
        "        transport: stdio\n"
        "        command: " + json.dumps(python, ensure_ascii=False) + "\n"
        "        args: " + json.dumps([server, "serve"], ensure_ascii=False) + "\n"
        "        failOnStartupError: true\n"
    )


def build(output: Path, *, python: Path | None = None, apply: bool = False) -> dict:
    report = plan(output, python=python)
    if not apply:
        return report
    target = Path(report["destination"])
    staged = Path(tempfile.mkdtemp(prefix=".adt-dsh-", dir=target.parent))
    try:
        for relative in FILES:
            destination = staged / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / relative, destination)
        (staged / "cordis.patch.yml").write_text(
            _patch(report["python"], report["mcp_server"]), encoding="utf-8"
        )
        if target.exists() or target.is_symlink():
            raise BundleError("Output appeared during generation")
        os.rename(staged, target)
    finally:
        if staged.exists():
            shutil.rmtree(staged)
    return {**report, "status": "BUNDLE_CREATED", "applied": True}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New directory outside the Toolkit checkout")
    parser.add_argument("--python", type=Path, help="Explicit existing Python interpreter; default is current Python")
    parser.add_argument("--apply", action="store_true", help="Create local bundle; never installs it into dsh")
    args = parser.parse_args(argv)
    try:
        report = build(args.output, python=args.python, apply=args.apply)
    except (BundleError, OSError) as exc:
        print("ERROR: " + str(exc)[:300], file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
