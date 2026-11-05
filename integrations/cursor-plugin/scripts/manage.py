#!/usr/bin/env python3
"""Opt-in, reversible local Cursor plugin installer (standard library only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

PLUGIN = Path(__file__).resolve().parents[1]
PAYLOAD = ("mcp.json", ".cursor-plugin", "skills", "rules", "commands", "README.md",
           "README.ru.md", "scripts/launch_mcp.py")
MARKER = ".adt-managed.json"


def default_target() -> Path:
    return Path.home() / ".cursor" / "plugins" / "local" / "ai-development-toolkit"


def default_state() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ADT-Cursor"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "adt-cursor"


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def reject_links(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError("Symlink/junction path rejected: " + str(part))


def source_files(source: Path) -> dict[str, Path]:
    found = {}
    for item in PAYLOAD:
        node = source / item
        if not node.exists():
            raise FileNotFoundError(str(node))
        paths = sorted(node.rglob("*")) if node.is_dir() else [node]
        for p in paths:
            if p.is_dir():
                continue
            reject_links(p)
            if not p.is_file():
                raise ValueError("Not a regular file: " + str(p))
            found[p.relative_to(source).as_posix()] = p
    return found


def inspection(target: Path) -> tuple[str, dict]:
    if not target.exists() and not target.is_symlink():
        return "NOT_INSTALLED", {}
    reject_links(target)
    marker = target / MARKER
    if not marker.is_file():
        return "UNMANAGED_CONFLICT", {}
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        files = data["files"]
        if data.get("schema") != 1 or not isinstance(files, dict):
            return "INVALID_MARKER", {}
        if any(not isinstance(k, str) or not isinstance(v, str) or
               Path(k).is_absolute() or ".." in Path(k).parts for k, v in files.items()):
            return "INVALID_MARKER", {}
        actual = {p.relative_to(target).as_posix(): digest(p)
                  for p in target.rglob("*") if p.is_file() and p != marker}
        if actual != files or any(p.is_symlink() for p in target.rglob("*")):
            return "DRIFT", data
    except (OSError, ValueError, KeyError, TypeError):
        return "INVALID_MARKER", {}
    return "MANAGED_CLEAN", data


def write_json(path: Path, obj: dict) -> None:
    temp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        temp.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()


def perform_install(source: Path, target: Path, state_dir: Path) -> dict:
    reject_links(target)
    reject_links(state_dir)
    state, _ = inspection(target)
    if state not in ("NOT_INSTALLED", "MANAGED_CLEAN"):
        raise ValueError("Refusing to overwrite " + state)
    files = source_files(source)
    planned = {relative: digest(p) for relative, p in files.items()}
    if state == "MANAGED_CLEAN":
        marker = json.loads((target / MARKER).read_text(encoding="utf-8"))
        if marker["files"] == planned:
            return {"status": "ALREADY_CURRENT", "files": len(files)}
    target.parent.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    staging = target.parent / (".adt-cursor-stage-" + uuid.uuid4().hex)
    backup = None
    try:
        staging.mkdir()
        for rel, source_file in files.items():
            destination = staging / Path(rel)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination, follow_symlinks=False)
        version = json.loads((source / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        write_json(staging / MARKER, {"schema": 1, "version": version, "files": planned})
        if target.exists():
            backup_dir = state_dir / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / ("cursor-" + uuid.uuid4().hex)
            target.rename(backup)
        try:
            staging.rename(target)
            write_json(state_dir / "state.json", {"schema": 1, "backup": str(backup) if backup else None})
        except Exception:
            if target.exists():
                shutil.rmtree(target)
            if backup is not None:
                backup.rename(target)
            raise
        return {"status": "UPDATED" if backup else "INSTALLED", "version": version,
                "files": len(files), "rollback_available": True}
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def perform_rollback(target: Path, state_dir: Path) -> dict:
    state, _ = inspection(target)
    if state != "MANAGED_CLEAN":
        raise ValueError("Rollback refused: " + state)
    meta = state_dir / "state.json"
    if not meta.is_file():
        raise ValueError("State record missing")
    data = json.loads(meta.read_text(encoding="utf-8"))
    backup = Path(data["backup"]) if data.get("backup") else None
    if backup is not None:
        backups_dir = (state_dir / "backups").resolve()
        if not backup.resolve().is_relative_to(backups_dir) or inspection(backup)[0] != "MANAGED_CLEAN":
            raise ValueError("Rollback backup invalid or outside managed directory")
    temporary = target.parent / (".adt-cursor-reverting-" + uuid.uuid4().hex)
    target.rename(temporary)
    try:
        if backup is not None:
            backup.rename(target)
        write_json(meta, {"schema": 1, "backup": None})
    except Exception:
        if target.exists():
            target.rename(backup)
        temporary.rename(target)
        raise
    shutil.rmtree(temporary)
    return {"status": "RESTORED_PREVIOUS" if backup else "UNINSTALLED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "update", "status", "doctor", "rollback"])
    parser.add_argument("--apply", action="store_true", help="Explicitly approve filesystem changes")
    parser.add_argument("--source", type=Path, default=PLUGIN)
    parser.add_argument("--target", type=Path, default=default_target())
    parser.add_argument("--state-dir", type=Path, default=default_state())
    args = parser.parse_args()
    try:
        source, target, state_dir = args.source.resolve(), args.target.absolute(), args.state_dir.absolute()
        if target.name != "ai-development-toolkit":
            raise ValueError("Target basename must be ai-development-toolkit")
        reject_links(target)
        status, info = inspection(target)
        if args.action in ("install", "update"):
            desired = source_files(source)
            result = {"status": "PREVIEW", "target_status": status, "target": str(target),
                      "version": json.loads((source / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"],
                      "payload_files": len(desired), "applied": False}
            if status not in ("NOT_INSTALLED", "MANAGED_CLEAN"):
                raise ValueError("Refusing to overwrite " + status)
            if args.apply:
                result = perform_install(source, target, state_dir)
                result["applied"] = True
        elif args.action == "rollback":
            result = {"status": "ROLLBACK_PREVIEW", "target_status": status, "applied": False}
            if args.apply:
                result = perform_rollback(target, state_dir)
                result["applied"] = True
        else:
            result = {"status": status, "version": info.get("version"), "applied": False}
            if args.action == "doctor":
                if status == "MANAGED_CLEAN":
                    proc = subprocess.run([sys.executable, str(target / "scripts" / "launch_mcp.py"), "--doctor"],
                                          capture_output=True, text=True, timeout=20, check=False)
                    result["mcp"] = json.loads(proc.stdout) if proc.returncode == 0 else {
                        "status": "BLOCKED", "reason": proc.stderr.strip()[:350]}
                else:
                    result["mcp"] = {"status": "NOT_CHECKED"}
                result["cursor_skill_discovery"] = "NOT_VERIFIED"
                result["cursor_mcp_invocation"] = "NOT_VERIFIED"
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
