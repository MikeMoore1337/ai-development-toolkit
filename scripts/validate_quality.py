#!/usr/bin/env python3
"""Offline quality gate for Toolkit links, inventories and declared workflow conflicts.

This is static integrity validation, not semantic review or an agent activation test.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
RULES = Path("docs/QUALITY_RULES.json")
INLINE_LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(\s*(?:<([^>\n]+)>|([^\s)\n]+))(?:\s+['\"][^'\"]+['\"])?\s*\)|!\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s)\n]+))\s*\)")
REFERENCE_DEF = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s*<?([^\s>]+)>?")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
FENCE = re.compile(r"^[ ]{0,3}(" + r"\x60{3,}|~{3,}" + r")([^\r\n]*)$")
INLINE_CODE = re.compile(r"(?<!\x60)(\x60+)(?!\x60)(.*?)\1(?!\x60)")
EXPLICIT_ID = re.compile(r"<(?:a|span)\s+[^>]*id=['\"]([^'\"]+)['\"]", re.I)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    file: str
    line: int
    explanation: str


def location(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def add(items: list[Finding], rule: str, file: str, line: int, why: str) -> None:
    items.append(Finding(rule, "BLOCKER", file, line, why))


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def safe_folder(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Invalid folder path")
    p = Path(relative)
    if p.is_absolute() or any(part in ("..", ".") for part in p.parts):
        raise ValueError("Unsafe folder path")
    dest = root / p
    if not dest.resolve().is_relative_to(root.resolve()):
        raise ValueError("Folder escapes package")
    if any(part.is_symlink() for part in (dest, *[p for p in dest.parents if p != root.parent])):
        raise ValueError("Symlink folder is not allowed")
    return dest


def inventory(root: Path, manifest: dict, findings: list[Finding]) -> tuple[dict[str, Path], dict[str, Path]]:
    skills: dict[str, Path] = {}
    roles: dict[str, Path] = {}
    packs = [
        (".agents/skills", manifest["core_skills"] + manifest.get("extension_skills", []), "skills"),
    ]
    for pack, cfg in manifest.get("extension_packs", {}).items():
        packs.append((cfg["skill_root"], cfg["skills"], "skills:" + pack))
    rolesets = [(".agents/roles", manifest["core_roles"], "roles")]
    for pack, cfg in manifest.get("extension_packs", {}).items():
        if "role_root" in cfg:
            rolesets.append((cfg["role_root"], cfg.get("roles", []), "roles:" + pack))
    for base, names, label in packs + rolesets:
        folder = safe_folder(root, base)
        if not isinstance(names, list) or not all(isinstance(s, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", s) for s in names):
            raise ValueError("Invalid names in " + label)
        if len(names) != len(set(names)):
            add(findings, "INV001", "MANIFEST.json", 1, "Duplicate entries in " + label)
        exists = sorted(p.name if label.startswith("skills") else p.stem
                        for p in folder.iterdir() if p.is_dir() if label.startswith("skills")) if label.startswith("skills") and folder.is_dir() else (
                         sorted(p.stem for p in folder.glob("*.md")) if folder.is_dir() else [])
        if set(exists) != set(names):
            add(findings, "INV001", "MANIFEST.json", 1,
                label + ": missing=" + repr(sorted(set(names) - set(exists))) +
                ", unregistered=" + repr(sorted(set(exists) - set(names))))
        target = skills if label.startswith("skills") else roles
        for name in names:
            if name in target:
                add(findings, "INV001", "MANIFEST.json", 1, "Duplicate across packs: " + name)
                continue
            item = folder / name if label.startswith("skills") else folder / (name + ".md")
            if not item.resolve().is_relative_to(root) or item.is_symlink():
                add(findings, "PATH001", "MANIFEST.json", 1, "Unsafe entry: " + name)
                continue
            if label.startswith("skills") and not (item / "SKILL.md").is_file():
                add(findings, "INV001", "MANIFEST.json", 1, "Missing SKILL.md: " + name)
            if not item.exists():
                add(findings, "INV001", "MANIFEST.json", 1, "Missing entry: " + name)
            target[name] = item
    return skills, roles


def rules_config(root: Path, available: set[str]) -> list[tuple[str, frozenset[str], str]]:
    config = load_json(root / RULES)
    if set(config) != {"schema_version", "exclusive_workflows"} or config["schema_version"] != 1:
        raise ValueError("Unsupported quality rules schema")
    pairs = config["exclusive_workflows"]
    if not isinstance(pairs, list):
        raise ValueError("exclusive_workflows must be a list")
    result = []
    seen: set[str] = set()
    for row in pairs:
        if not isinstance(row, dict) or set(row) != {"rule_id", "skills", "reason"}:
            raise ValueError("Invalid exclusive workflow entry")
        rule_id, names, reason = row["rule_id"], row["skills"], row["reason"]
        if not isinstance(rule_id, str) or not re.fullmatch(r"WF\d{3}", rule_id) or rule_id in seen:
            raise ValueError("Duplicate/invalid workflow rule ID")
        if not isinstance(names, list) or len(names) < 2 or any(not isinstance(x, str) for x in names) or len(set(names)) != len(names):
            raise ValueError("Invalid exclusive workflow skills")
        if any(x not in available for x in names):
            raise ValueError("Workflow rule refers to unknown skills: " + repr(names))
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Empty workflow reason")
        result.append((rule_id, frozenset(names), reason))
        seen.add(rule_id)
    return result


def markdown_lines(text: str):
    """Yield substantive lines, excluding genuine fences and inline code spans."""
    marker, length = "", 0
    for number, line in enumerate(text.splitlines(), 1):
        fence = FENCE.match(line)
        if marker:
            # A closing fence must be the same character, at least as long as
            # the opener, and followed only by whitespace. An info string
            # (e.g. ```python) inside a code sample does not close the fence.
            if (fence and fence.group(1)[0] == marker
                    and len(fence.group(1)) >= length
                    and not fence.group(2).strip()):
                marker, length = "", 0
            continue
        if fence and (fence.group(1)[0] == "~" or "`" not in fence.group(2)):
            marker, length = fence.group(1)[0], len(fence.group(1))
            continue
        yield number, INLINE_CODE.sub("", line)


def anchors(text: str) -> set[str]:
    found: set[str] = set()
    duplicates: dict[str, int] = {}
    for _, line in markdown_lines(text):
        found.update(EXPLICIT_ID.findall(line))
        heading = HEADING.match(line)
        if not heading:
            continue
        title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading.group(1))
        title = re.sub(r"<[^>]*>", "", title)
        slug = re.sub(r"[^\w\- ]", "", title.lower().strip()).replace(" ", "-")
        if not slug:
            continue
        n = duplicates.get(slug, 0)
        found.add(slug + ("-" + str(n) if n else ""))
        duplicates[slug] = n + 1
    return found


def check_link(root: Path, source: Path, line: int, raw: str,
               findings: list[Finding], cache: dict[Path, set[str]]) -> None:
    raw = raw.strip()
    if not raw or raw.startswith(("#",)) and raw == "#":
        return
    if raw.startswith("//"):
        return
    parsed = urlsplit(raw)
    if parsed.scheme.lower() in ("http", "https", "mailto", "tel"):
        return
    if parsed.scheme or parsed.netloc or raw.startswith("/") or "\\" in raw:
        add(findings, "PATH001", location(source, root), line, "Unsafe or unsupported local target: " + raw)
        return
    relative = unquote(parsed.path)
    fragment = unquote(parsed.fragment)
    if "\\" in relative or "\x00" in relative or re.match(r"^[a-zA-Z]:", relative):
        add(findings, "PATH001", location(source, root), line, "Unsafe encoded local target: " + raw)
        return
    unresolved = source.parent / relative if relative else source
    target = unresolved.resolve()
    cursor = unresolved
    linked = False
    while cursor != root.parent:
        if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
            linked = True
            break
        if cursor == cursor.parent:
            break
        cursor = cursor.parent
    if not target.is_relative_to(root):
        add(findings, "PATH001", location(source, root), line, "Link escapes package: " + raw)
    elif linked:
        add(findings, "PATH001", location(source, root), line, "Symlink or junction target: " + raw)
    elif not target.is_file():
        add(findings, "LINK001", location(source, root), line, "Missing local file: " + raw)
    elif fragment:
        if target.suffix.lower() not in (".md", ".markdown"):
            return
        if target not in cache:
            cache[target] = anchors(target.read_text(encoding="utf-8"))
        if fragment not in cache[target]:
            add(findings, "ANCHOR001", location(source, root), line, "Unresolved heading anchor: " + raw)


def markdown_files(root: Path, skills: dict[str, Path], roles: dict[str, Path]) -> list[Path]:
    sources: set[Path] = set(roles.values())
    for folder in skills.values():
        if folder.is_dir():
            sources.update(folder.rglob("*.md"))
    sources.update((root / "docs").rglob("*.md"))
    sources.update((root / "extensions/qa").glob("*.md"))
    for path in (root / "README.md", root / "README.ru.md", root / "AGENTS.md",
                 root / "CONTRIBUTING.md"):
        if path.is_file():
            sources.add(path)
    return sorted(sources)


def check_markdown(root: Path, paths: list[Path], findings: list[Finding]) -> None:
    cache: dict[Path, set[str]] = {}
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            add(findings, "PATH001", location(path, root), 1, "Unsafe Markdown source")
            continue
        for number, line in markdown_lines(path.read_text(encoding="utf-8")):
            links = [m.group(1) or m.group(2) or m.group(3) or m.group(4)
                     for m in INLINE_LINK.finditer(line)]
            ref = REFERENCE_DEF.match(line)
            if ref:
                links.append(ref.group(1))
            for link in links:
                check_link(root, path, number, link, findings, cache)


def inspect(root: Path = ROOT) -> dict:
    root = root.resolve()
    findings: list[Finding] = []
    counts = {"skills": 0, "roles": 0, "profiles": 0, "markdown_files": 0}
    try:
        manifest = load_json(root / "MANIFEST.json")
        skills, roles = inventory(root, manifest, findings)
        counts["skills"], counts["roles"] = len(skills), len(roles)
        profiles = manifest["profiles"]
        if not isinstance(profiles, dict) or not profiles:
            raise ValueError("Missing or invalid profiles")
        counts["profiles"] = len(profiles)
        exclusions = rules_config(root, set(skills))
        for name, chosen in sorted(profiles.items()):
            if not isinstance(name, str) or not isinstance(chosen, list) or not chosen:
                add(findings, "PROFILE001", "MANIFEST.json", 1, "Invalid profile: " + str(name))
                continue
            if any(not isinstance(s, str) for s in chosen) or len(set(chosen)) != len(chosen):
                add(findings, "PROFILE001", "MANIFEST.json", 1, "Invalid or duplicated skills in " + name)
                continue
            unknown = sorted(set(chosen) - set(skills))
            if unknown:
                add(findings, "PROFILE001", "MANIFEST.json", 1, name + ": missing skills " + repr(unknown))
            for rule, combination, reason in exclusions:
                if combination.issubset(chosen):
                    add(findings, rule, "MANIFEST.json", 1, name + ": " + reason)
        paths = markdown_files(root, skills, roles)
        counts["markdown_files"] = len(paths)
        check_markdown(root, paths, findings)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        add(findings, "CONFIG001", ".", 1, type(exc).__name__ + ": " + str(exc))
    ordered = sorted(set(findings), key=lambda x: (x.file, x.line, x.rule_id, x.explanation))
    return {
        "status": "FAIL" if ordered else "PASS",
        "counts": counts,
        "findings": [asdict(f) for f in ordered],
        "summary": {"BLOCKER": len(ordered), "WARNING": 0, "INFO": 0},
        "limitations": "Static links, inventories and declared incompatibilities only; semantic conflicts and agent effectiveness require separate evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json-report", type=Path, help="Write reproducible JSON report to this path")
    args = parser.parse_args()
    report = inspect(args.root)
    data = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json_report:
        try:
            args.json_report.write_text(data, encoding="utf-8")
        except OSError as exc:
            print("Cannot write report: " + str(exc), file=sys.stderr)
            return 1
    print(data, end="")
    return 1 if report["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
