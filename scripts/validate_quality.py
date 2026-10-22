#!/usr/bin/env python3
"""Offline quality gate for Toolkit links, inventories and declared workflow conflicts.

This is static integrity validation, not semantic review or an agent activation test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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


# Generated environments can contain Markdown from untracked dependencies.
# Only scan repository sources, not caches, VCS internals or temporary artifacts.
IGNORED_MARKDOWN_DIRS = frozenset({
    ".git", ".venv", "venv", "node_modules", ".tox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "__pycache__", ".hermes-compat",
    ".artifacts",
})


def markdown_files(root: Path) -> list[Path]:
    """Find every repository Markdown file, including templates and recipes."""
    sources: list[Path] = []

    def raise_walk_error(exc: OSError) -> None:
        raise exc

    for parent, dirs, files in os.walk(root, topdown=True, followlinks=False,
                                       onerror=raise_walk_error):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_MARKDOWN_DIRS)
        for name in sorted(files):
            if name.lower().endswith(".md"):
                sources.append(Path(parent) / name)
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



# Optional owner-reviewed evidence documents; this check never performs AI trials.
EVIDENCE_LEVELS = ("source_validated", "packaged", "installed",
                   "discovered", "activated", "effective")
EVIDENCE_STATUSES = frozenset(("PASS", "FAIL", "NOT_MEASURED", "NOT_APPLICABLE"))
FULL_REVISION = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def check_evidence(root: Path, skill_ids: set[str], findings: list[Finding]) -> None:
    """Reject unsupported quality claims and unpinned/unsafe evidence artifacts."""
    folder = root / "quality" / "evidence"
    if not folder.exists() and not folder.is_symlink():
        return  # Existing skills need no new declarations.
    if not folder.is_dir() or folder.is_symlink():
        add(findings, "EVIDENCE001", "quality/evidence", 1, "Unsafe evidence directory")
        return
    client_ids: set[str] = set()
    registry = root / "compatibility" / "clients.json"
    if registry.is_file():
        try:
            clients = load_json(registry)["clients"]
            client_ids = {item["client_id"] for item in clients}
        except (KeyError, TypeError, ValueError, OSError):
            add(findings, "EVIDENCE001", "compatibility/clients.json", 1,
                "Cannot verify client identifiers")
            return
    for source in sorted(folder.iterdir()):
        path = location(source, root)
        if source.is_symlink() or not source.is_file() or source.suffix != ".json":
            add(findings, "EVIDENCE001", path, 1, "Expected an ordinary JSON evidence file")
            continue
        try:
            record = load_json(source)
            if set(record) != {"schema_version", "skill_id", "source_revision", "levels"}:
                raise ValueError("Unexpected evidence fields")
            skill = record["skill_id"]
            if record["schema_version"] != 1 or skill != source.stem or skill not in skill_ids:
                raise ValueError("Unknown skill or evidence schema")
            revision = record["source_revision"]
            if not isinstance(revision, str) or not FULL_REVISION.fullmatch(revision):
                raise ValueError("Evidence must pin a full source revision")
            levels = record["levels"]
            if not isinstance(levels, dict) or set(levels) != set(EVIDENCE_LEVELS):
                raise ValueError("Expected all six evidence levels")
            previous_pass = False
            for level in EVIDENCE_LEVELS:
                entry = levels[level]
                if not isinstance(entry, dict) or entry.get("status") not in EVIDENCE_STATUSES:
                    raise ValueError(level + ": unknown/missing status")
                status = entry["status"]
                if status == "PASS":
                    if level != EVIDENCE_LEVELS[0] and not previous_pass:
                        raise ValueError(level + ": prerequisite level lacks explicit PASS")
                    if not isinstance(entry.get("method"), str) or not entry["method"].strip():
                        raise ValueError(level + ": PASS requires a method")
                    artifacts = entry.get("artifacts")
                    if not isinstance(artifacts, list) or not artifacts:
                        raise ValueError(level + ": PASS requires pinned artifacts")
                    for artifact in artifacts:
                        if not isinstance(artifact, dict) or set(artifact) != {"path", "sha256"}:
                            raise ValueError(level + ": malformed artifact")
                        relative, expected = artifact["path"], artifact["sha256"]
                        if (not isinstance(relative, str) or not relative or "\\" in relative
                                or relative.startswith("/") or "//" in relative
                                or any(part in ("..", ".") for part in relative.split("/"))
                                or not isinstance(expected, str) or not SHA256.fullmatch(expected)):
                            raise ValueError(level + ": unsafe artifact path/hash")
                        target = root.joinpath(*relative.split("/"))
                        if not target.resolve().is_relative_to(root.resolve()) or not target.is_file():
                            raise ValueError(level + ": missing/escaping artifact")
                        cursor = target
                        while cursor != root.parent:
                            if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
                                raise ValueError(level + ": linked artifact")
                            if cursor == cursor.parent:
                                break
                            cursor = cursor.parent
                        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                            raise ValueError(level + ": artifact digest mismatch")
                    if level in EVIDENCE_LEVELS[2:]:
                        for field in ("environment", "reviewed_by", "observed_at"):
                            if not isinstance(entry.get(field), str) or not entry[field].strip():
                                raise ValueError(level + ": runtime PASS requires " + field)
                        if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", entry["observed_at"]):
                            raise ValueError(level + ": observed_at must be UTC ISO-8601")
                    if level in EVIDENCE_LEVELS[3:]:
                        if not client_ids or entry.get("client_id") not in client_ids:
                            raise ValueError(level + ": unsupported/unknown client")
                    if level == "effective" and not isinstance(entry.get("comparison"), dict):
                        raise ValueError("effective: baseline-vs-candidate comparison required")
                elif status == "FAIL":
                    if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
                        raise ValueError(level + ": FAIL requires a reason")
                elif status == "NOT_APPLICABLE":
                    if level in EVIDENCE_LEVELS[:2] or not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
                        raise ValueError(level + ": unsupported NOT_APPLICABLE")
                elif set(entry) != {"status"}:
                    raise ValueError(level + ": NOT_MEASURED cannot claim observations")
                previous_pass = status == "PASS"
        except (KeyError, TypeError, ValueError, OSError, UnicodeError) as exc:
            add(findings, "EVIDENCE001", path, 1, str(exc))



def check_current_docs(root: Path, manifest: dict, findings: list[Finding]) -> None:
    """Check maintained current-state references; never rewrite historic audits."""
    # Synthetic inventory/link fixtures have no maintained README or version.
    if not (root / "README.md").is_file() and not (root / "README.ru.md").is_file():
        return
    packs = manifest.get("extension_packs", {})
    sizes = {key: len(value["skills"]) for key, value in packs.items()}
    core = len(manifest["core_skills"]) + len(manifest.get("extension_skills", []))
    skills = core + sum(sizes.values())
    roles = len(manifest["core_roles"]) + sum(len(p.get("roles", [])) for p in packs.values())
    profiles = set(manifest["profiles"])
    version = manifest.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        add(findings, "DOC004", "MANIFEST.json", 1, "Invalid published baseline")
        return

    def count_match(path: str, body: str, pattern: str, expected: int) -> None:
        found = re.search(pattern, body, re.M)
        if not found or int(found.group(1)) != expected:
            add(findings, "DOC001", path, 1, "Count mismatch: " + pattern)

    def table_check(path: str, body: str) -> None:
        table = []
        def finish() -> None:
            if len(table) >= 2 and re.fullmatch(r"[\s|:-]+", table[1][1]):
                width = table[1][1].count("|") - 1
                for number, line in table:
                    if line.count("|") - 1 != width:
                        add(findings, "DOC002", path, number, "Incorrect table cell count")
        for number, line in markdown_lines(body):
            if line.lstrip().startswith("|") and line.rstrip().endswith("|"):
                table.append((number, line))
            else:
                finish()
                table = []
        finish()

    for path in ("README.md", "README.ru.md"):
        file = root / path
        if not file.is_file():
            continue
        body = file.read_text(encoding="utf-8")
        table_check(path, body)
        for name, n in (("skills", skills), ("roles", roles), ("profiles", len(profiles))):
            count_match(path, body, r"img\.shields\.io/badge/" + name + r"-(\d+)-", n)
        for pattern, n in (
            (r"\|\s*\*\*(?:Core skills|Core)\*\*\s*\|\s*(\d+)", core),
            (r"\|\s*\*\*Frontend / Backend / Fullstack\*\*\s*\|\s*(\d+)",
             sum(sizes.get(x, 0) for x in ("frontend", "backend", "fullstack"))),
            (r"\|\s*\*\*QA Engineering Pack\*\*\s*\|\s*(\d+)", sizes.get("qa", 0)),
        ):
            count_match(path, body, pattern, n)
        heading = "## Choose your workflow" if path == "README.md" else "## Какой профиль выбрать"
        section = body.split(heading, 1)
        if len(section) != 2:
            add(findings, "DOC003", path, 1, "Missing profile selection table")
        else:
            for line in section[1].split("\n## ", 1)[0].splitlines():
                selected = re.match(r"^\|\s*[^|]+\|\s*" + chr(96) + r"([^" + chr(96) + r"]+)" + chr(96) + r"\s*\|", line)
                if selected and selected.group(1) not in profiles:
                    add(findings, "DOC003", path, 1, "Unknown profile: " + selected.group(1))
        start = "## Quick start" if path == "README.md" else "## Быстрый старт"
        quick = body.split(start, 1)
        if len(quick) != 2:
            add(findings, "DOC005", path, 1, "Missing Quick Start")
        else:
            q = quick[1].split("\n## ", 1)[0]
            for cmd in ("skill_manager.py catalog", "skill_manager.py install",
                        "skill_manager.py status", "--apply"):
                if cmd not in q:
                    add(findings, "DOC005", path, 1, "Recommended command missing: " + cmd)
            if "install.py --list-profiles" in q:
                add(findings, "DOC005", path, 1, "Legacy installer recommended")
        candidate_marker = ("**Next release candidate:**" if path == "README.md"
                            else "**Кандидат следующего релиза:**")
        if candidate_marker in body:
            expected = ("**NOT PUBLISHED**" if path == "README.md"
                        else "**НЕ ОПУБЛИКОВАН**")
            if (f"`v{version}`" not in body or expected not in body
                    or "CHANGELOG.md" not in body or
                    "/releases/tag/v5.5.1" not in body):
                add(findings, "DOC004", path, 1, "Unpublished release candidate metadata differs")
        else:
            released = re.search(r"/releases/tag/v(\d+\.\d+\.\d+)", body)
            if not released or released.group(1) != version or "CHANGELOG.md" not in body:
                add(findings, "DOC004", path, 1, "Published release differs from baseline")

    path = "docs/AGENT_SKILLS_SPEC.md"
    if (root / path).is_file():
        body = (root / path).read_text(encoding="utf-8")
        found = re.search(r"(\d+) in the checked revision:\s*(\d+) core/generic,\s*"
                          r"(\d+) QA,\s*(\d+) Make Feature,\s*(\d+) Frontend,\s*"
                          r"(\d+) Backend,\s*(\d+) Fullstack and\s*(\d+) Product,\s*(\d+) Management,\s*(\d+) Analysis,\s*(\d+) Design,\s*(\d+) AI,\s*(\d+) SEO,\s*(\d+) Reliability,\s*(\d+) Performance,\s*(\d+) Security(?: and|,)\s*(\d+) DevOps"
                          r"(?: and\s*(\d+) Accessibility)?(?: and\s*(\d+) Operations)?(?: and\s*(\d+) Data Engineering)?", body)
        expected = [skills, core] + [sizes.get(x, 0) for x in
                                     ("qa", "make-feature", "frontend", "backend", "fullstack", "product", "management", "analysis", "design", "ai", "seo", "reliability", "performance", "security", "devops", "accessibility", "operations", "data")]
        if not found or [int(x) if x is not None else 0 for x in found.groups()] != expected:
            add(findings, "DOC001", path, 1, "Official validator count mismatch")

    path = "docs/UNIVERSAL_ENGINEERING.md"
    if (root / path).is_file():
        body = (root / path).read_text(encoding="utf-8")
        for label, key in (("Frontend", "frontend"), ("Backend", "backend"),
                           ("Fullstack", "fullstack"), ("QA (existing)", "qa")):
            count_match(path, body, r"^\|\s*" + re.escape(label) +
                        r"\s*\|[^|\n]*\|[^|\n]*\|\s*(\d+)\s*\|", sizes.get(key, 0))

    path = "docs/SKILLS_CATALOG.md"
    if (root / path).is_file():
        body = (root / path).read_text(encoding="utf-8")
        count_match(path, body, r"These (\d+) skills live under", core)
        section = body.split("## Profiles", 1)
        pattern = r"^\|\s*" + chr(96) + r"([^" + chr(96) + r"]+)" + chr(96) + r"\s*\|"
        actual = set(re.findall(pattern, section[1], re.M)) if len(section) == 2 else set()
        if actual != profiles:
            add(findings, "DOC003", path, 1, "Catalog and manifest profiles differ")

    path = "CHANGELOG.md"
    if (root / path).is_file():
        headings = re.findall(r"^##\s+(.+)$", (root / path).read_text(encoding="utf-8"), re.M)
        candidate = ("**v5.5.1 published-tag metadata erratum" in
                     (root / path).read_text(encoding="utf-8"))
        expected_status = "candidate" if candidate else "released"
        if (len(headings) < 2 or headings[0] != "Unreleased (main after v" + version + ")"
                or not re.fullmatch(re.escape(version) +
                                    r" \(" + expected_status + r", \d{4}-\d{2}-\d{2}\)",
                                    headings[1])):
            add(findings, "DOC004", path, 1, "Released/Unreleased section mismatch")
    path = "docs/RELEASE_PROCESS.md"
    if (root / path).is_file():
        body = (root / path).read_text(encoding="utf-8")
        if "## Published v5.5.0 and v5.5.1 archive errata" in body:
            if (f"`{version}` (candidate, NOT PUBLISHED)" not in body
                    or "/releases/tag/v5.5.1" not in body
                    or body.count("TAG_MANIFEST_VERSION_MISMATCH") < 2
                    or '$taggedManifest.version' not in body
                    or '$manifest.version' not in body):
                add(findings, "DOC004", path, 1, "Release candidate identity or pre-tag guard mismatch")
        elif ("currently " + chr(96) + version + chr(96) not in body or
                "/releases/tag/v" + version not in body or "Unreleased" not in body):
            add(findings, "DOC004", path, 1, "Release process baseline mismatch")


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
        paths = markdown_files(root)
        counts["markdown_files"] = len(paths)
        check_markdown(root, paths, findings)
        check_current_docs(root, manifest, findings)
        check_evidence(root, set(skills), findings)
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
