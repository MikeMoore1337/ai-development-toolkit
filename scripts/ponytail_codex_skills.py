#!/usr/bin/env python3
"""Opt-in, offline installation of unchanged Ponytail skills for Codex Desktop.

This installs skills only. It never starts Codex, configures a plugin, or runs hooks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party" / "ponytail-v5.3.2" / "skills"
PIN = "16352ac229eb08a9598dcae48fe9f2b342567d86"
BLOBS = {
    "ponytail": "d64edd32265ba21cbf5270158f04e97d96925f27",
    "ponytail-review": "a50e3ac6ded6fccc9edae34ce37877bbce11e3fa",
    "ponytail-audit": "ff9a95480700600fe2664d2d0906a4d750b2da0b",
    "ponytail-debt": "3124f520a65d2a4fa75a2f5db6225c38ebdb8620",
    "ponytail-gain": "1edff0e461fad6b671733ea6796aea9e417e266b",
    "ponytail-help": "34fccb3ff542b3b8d4d131e6120a1812c9c4617a",
}
MARKER = ".adt-ponytail-v5.3.2.json"


class Hold(RuntimeError):
    """Refuse an unsafe or ambiguous filesystem state."""


def linked(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def canonical(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def verify_upstream(source: Path) -> dict[str, bytes]:
    if not source.is_dir() or linked(source) or linked(source.parent):
        raise Hold("missing or linked upstream skills directory")
    if sorted(p.name for p in source.iterdir()) != sorted(BLOBS):
        raise Hold("upstream skill inventory differs from pinned original")
    payload = {}
    for name, expected in BLOBS.items():
        directory, file = source / name, source / name / "SKILL.md"
        if not directory.is_dir() or linked(directory) or not file.is_file() or linked(file):
            raise Hold(f"upstream skill missing or linked: {name}")
        if sorted(p.name for p in directory.iterdir()) != ["SKILL.md"]:
            raise Hold(f"unexpected upstream contents: {name}")
        body = canonical(file.read_bytes())
        digest = hashlib.sha1(b"blob " + str(len(body)).encode("ascii") + b"\0" + body).hexdigest()
        if digest != expected:
            raise Hold(f"upstream Git blob SHA mismatch: {name}")
        payload[name] = body
    return payload


def ensure_destination(root: Path, *, create: bool) -> None:
    if any(linked(path) for path in (root, *root.parents)):
        raise Hold("destination is a symlink or junction")
    if root.exists() and not root.is_dir():
        raise Hold("destination is not a directory")
    if create:
        root.mkdir(parents=True, exist_ok=True)
        if linked(root):
            raise Hold("destination became a link")


def ownership(root: Path) -> bool:
    marker = root / MARKER
    if linked(marker):
        raise Hold("managed marker is a link")
    if not marker.exists():
        return False
    try:
        record = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Hold("managed marker cannot be read") from error
    if record != {"source": "DietrichGebert/ponytail", "commit": PIN, "skills": sorted(BLOBS)}:
        raise Hold("unknown installation marker; refusing to alter files")
    return True


def check_skills(root: Path, payload: dict[str, bytes]) -> bool:
    for name, body in payload.items():
        directory, file = root / name, root / name / "SKILL.md"
        if linked(directory) or linked(file):
            raise Hold(f"linked installed skill: {name}")
        if not directory.exists():
            return False
        if not directory.is_dir() or sorted(p.name for p in directory.iterdir()) != ["SKILL.md"]:
            raise Hold(f"unexpected installed files: {name}")
        if not file.is_file() or canonical(file.read_bytes()) != body:
            raise Hold(f"installed skill changed: {name}")
    return True


def remove_unchanged(directory: Path, body: bytes) -> None:
    file = directory / "SKILL.md"
    try:
        if (not linked(directory) and not linked(file) and directory.is_dir()
                and sorted(p.name for p in directory.iterdir()) == ["SKILL.md"]
                and file.is_file() and canonical(file.read_bytes()) == body):
            file.unlink()
            directory.rmdir()
    except OSError:
        pass


def execute(action: str, *, source: Path = SOURCE, destination: Path | None = None,
            codex_root: Path | None = None) -> str:
    # Default Codex user skills location; no writes to any project checkout.
    root = destination if destination is not None else Path.home() / ".agents" / "skills"
    codex = codex_root if codex_root is not None else Path.home() / ".codex" / "skills"
    payload = verify_upstream(source)
    ensure_destination(root, create=False)
    if root.is_dir() and any(path.name.startswith(".adt-ponytail-stage-") for path in root.iterdir()):
        raise Hold("unfinished staging directory; inspect before recovery")
    managed = ownership(root)
    if managed:
        if not check_skills(root, payload):
            raise Hold("managed installation is incomplete")
    else:
        existing = [name for name in BLOBS if (root / name).exists() or linked(root / name)]
        if existing:
            raise Hold("unowned skill collision: " + ", ".join(existing))
    if action == "status":
        return "INSTALLED" if managed else "NOT_INSTALLED"
    if action == "install":
        if managed:
            return "ALREADY_INSTALLED"
        # A second old Codex skill root can cause duplicate discovery. Fail closed.
        if codex != root:
            for name in BLOBS:
                if (codex / name).exists() or linked(codex / name):
                    raise Hold(f"possible duplicate in legacy Codex skills: {name}")
        ensure_destination(root, create=True)
        staged = Path(tempfile.mkdtemp(prefix=".adt-ponytail-stage-", dir=root))
        installed = []
        try:
            for name, body in payload.items():
                (staged / name).mkdir()
                (staged / name / "SKILL.md").write_bytes(body)
            for name in BLOBS:
                if (root / name).exists() or linked(root / name):
                    raise Hold(f"collision during install: {name}")
                os.rename(staged / name, root / name)
                installed.append(root / name)
            marker_body = json.dumps({"source": "DietrichGebert/ponytail", "commit": PIN,
                                      "skills": sorted(BLOBS)}, sort_keys=True) + "\n"
            with (root / MARKER).open("x", encoding="utf-8") as out:
                out.write(marker_body)
        except BaseException:
            for directory in reversed(installed):
                remove_unchanged(directory, payload[directory.name])
            raise
        finally:
            if not linked(staged) and staged.is_dir():
                for name, body in payload.items():
                    remove_unchanged(staged / name, body)
                try:
                    staged.rmdir()
                except OSError:
                    pass
        return "INSTALLED"
    if action == "uninstall":
        if not managed:
            raise Hold("no managed installation to uninstall")
        for name in BLOBS:
            (root / name / "SKILL.md").unlink()
            (root / name).rmdir()
        (root / MARKER).unlink()
        return "UNINSTALLED"
    raise ValueError(f"unknown action {action}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true", help="Read-only status")
    group.add_argument("--install", action="store_true", help="Opt-in skill-only installation")
    group.add_argument("--uninstall", action="store_true", help="Remove only the managed installation")
    args = parser.parse_args()
    action = "install" if args.install else "uninstall" if args.uninstall else "status"
    try:
        result = execute(action)
    except (Hold, OSError) as exc:
        print(f"PONYTAIL_HOST=HOLD ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 2
    print(f"PONYTAIL_HOST={result}")
    print("CLIENT_DISCOVERY=NOT_VERIFIED")
    print("CODEX_NATIVE_PLUGIN_HOOKS=NOT_MANAGED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
