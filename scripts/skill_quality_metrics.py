#!/usr/bin/env python3
"""Offline, read-only per-skill source measurements. Never executes skill code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Existing CLI modules use absolute sibling imports; support both direct invocation
# and unittest discovery from the repository root.
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
from profile_metrics import skill_paths
from validate_pack import parse_metadata, validate_skill
from validate_quality import check_markdown
from verify_client_compatibility import load_registry

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
METHOD = "offline-source-metrics-v1"
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
CODE_SUFFIXES = frozenset({".py", ".js", ".ts", ".sh", ".ps1", ".go", ".bat", ".cmd", ".exe"})
EMPIRICAL_FIELDS = (
    "task_acceptance_rate", "introduced_regressions", "unsafe_actions",
    "model_token_usage", "execution_duration", "skill_activation_observed",
    "baseline_vs_candidate_delta",
)


class MetricsError(ValueError):
    """Invalid input, baseline, or unsafe inventory."""


def metric(value, unit: str, method: str, status: str = "PASS") -> dict:
    return {"value": value, "unit": unit, "method": method, "status": status}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def revision_of(root: Path) -> str | None:
    try:
        p = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                           capture_output=True, text=True, check=False, timeout=5)
        value = p.stdout.strip()
        return value if p.returncode == 0 and SHA.fullmatch(value) else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def safe_path(root: Path, target: Path) -> bool:
    """Lexical and resolved containment; reject symlinks and Windows junctions."""
    root = root.absolute()
    target = target.absolute()
    if not target.is_relative_to(root):
        return False
    try:
        if not target.resolve().is_relative_to(root.resolve()):
            return False
        for path in (target, *target.parents):
            if path == root.parent:
                break
            if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                return False
    except (OSError, RuntimeError):
        return False
    return True


def inventory(root: Path) -> dict[str, Path]:
    file = root / "MANIFEST.json"
    if not safe_path(root, file):
        raise MetricsError("Unsafe MANIFEST.json path")
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise MetricsError("MANIFEST.json must contain an object")
        if not isinstance(data.get("core_skills"), list) or not isinstance(data.get("extension_skills", []), list):
            raise MetricsError("Malformed core skills")
        packs = data.get("extension_packs", {})
        if not isinstance(packs, dict):
            raise MetricsError("Malformed extension_packs")
        for name, pack in packs.items():
            if not isinstance(name, str) or not isinstance(pack, dict) or not isinstance(pack.get("skills"), list):
                raise MetricsError("Malformed extension pack")
            base = pack.get("skill_root")
            if not isinstance(base, str) or not base or "\\" in base or Path(base).is_absolute() or ".." in Path(base).parts:
                raise MetricsError("Unsafe extension pack root")
        for names in [data["core_skills"], data.get("extension_skills", [])] + [p["skills"] for p in packs.values()]:
            if any(not isinstance(x, str) or not NAME.fullmatch(x) for x in names):
                raise MetricsError("Invalid manifest skill name")
        result = skill_paths(root, data)
        if not result:
            raise MetricsError("Empty skill inventory")
        for name, folder in result.items():
            if not folder.absolute().is_relative_to(root.absolute()):
                raise MetricsError("Skill path escapes package: " + name)
        return result
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise MetricsError("Cannot parse manifest: " + str(exc)) from exc


def _files(root: Path, folder: Path) -> tuple[list[Path], list[dict]]:
    findings: list[dict] = []
    files: list[Path] = []
    if not safe_path(root, folder):
        return files, [{"severity": "FAIL", "rule_id": "PATH", "path": folder.relative_to(root).as_posix(),
                        "reason": "Linked or escaping skill directory"}]
    if not folder.is_dir():
        return files, [{"severity": "FAIL", "rule_id": "INVENTORY", "path": folder.relative_to(root).as_posix(),
                        "reason": "Skill directory missing"}]
    for parent, dirs, names in os.walk(folder, topdown=True, followlinks=False):
        p = Path(parent)
        for name in sorted(dirs):
            child = p / name
            if not safe_path(root, child):
                findings.append({"severity": "FAIL", "rule_id": "PATH",
                                 "path": child.relative_to(root).as_posix(), "reason": "Linked or escaping directory"})
                dirs.remove(name)
        dirs.sort()
        for name in sorted(names):
            child = p / name
            rel = child.relative_to(root).as_posix()
            if not safe_path(root, child):
                findings.append({"severity": "FAIL", "rule_id": "PATH",
                                 "path": rel, "reason": "Linked or escaping file"})
            elif not child.is_file():
                findings.append({"severity": "FAIL", "rule_id": "RESOURCE",
                                 "path": rel, "reason": "Non-regular resource"})
            else:
                files.append(child)
    return sorted(files), findings


def measure_skill(root: Path, skill_id: str, folder: Path, revision: str | None, clients: list[dict]) -> dict:
    files, findings = _files(root, folder)
    paths = {p.relative_to(folder).as_posix(): p for p in files}
    main = paths.get("SKILL.md")
    if main is None:
        findings.append({"severity": "FAIL", "rule_id": "SKILL", "path": (folder / "SKILL.md").relative_to(root).as_posix(),
                         "reason": "Missing SKILL.md"})
    else:
        for error in validate_skill(folder):
            findings.append({"severity": "FAIL", "rule_id": "FRONTMATTER", "path": main.relative_to(root).as_posix(),
                             "reason": str(error).replace(str(root) + os.sep, "")})
    raw = b""
    text = ""
    header = None
    metadata_bytes = 0
    if main is not None:
        try:
            raw = main.read_bytes()
            text = raw.decode("utf-8")
            match = re.match(r"\A---\r?\n.*?\r?\n---(?:\r?\n|\Z)", text, re.S)
            if match:
                metadata_bytes = len(match.group(0).encode("utf-8"))
            try:
                header = parse_metadata(text)
            except (ValueError, RuntimeError):
                pass  # validate_skill supplies the actionable error
        except UnicodeError:
            findings.append({"severity": "FAIL", "rule_id": "ENCODING",
                             "path": main.relative_to(root).as_posix(), "reason": "SKILL.md is not UTF-8"})
    sources = [p for p in files if p.suffix.lower() in (".md", ".markdown")]
    if sources:
        link_findings = []
        try:
            check_markdown(root, sources, link_findings)
            for f in link_findings:
                findings.append({"severity": "FAIL", "rule_id": f.rule_id, "path": f.file,
                                 "line": f.line, "reason": f.explanation})
        except (OSError, UnicodeError, ValueError) as exc:
            findings.append({"severity": "FAIL", "rule_id": "LINK_SCAN", "path": folder.relative_to(root).as_posix(),
                             "reason": str(exc)})
    entries = []
    for relative, file in sorted(paths.items()):
        try:
            data = file.read_bytes()
        except OSError as exc:
            findings.append({"severity": "FAIL", "rule_id": "READ",
                             "path": file.relative_to(root).as_posix(), "reason": str(exc)})
            continue
        parts = Path(relative).parts
        kind = ("main" if relative == "SKILL.md" else
                "reference" if "references" in parts[:-1] else
                "executable_source" if file.suffix.lower() in CODE_SUFFIXES else "resource")
        entries.append({"path": relative, "kind": kind, "bytes": len(data), "sha256": digest(data)})
    sums = {e["path"]: e["bytes"] for e in entries}
    total = sum(sums.values())
    main_bytes = sums.get("SKILL.md")
    refs = [e for e in entries if e["kind"] == "reference"]
    extra = len(entries) - (1 if main_bytes is not None else 0)
    footprint = {
        "skill_md_bytes": metric(main_bytes, "bytes", "UTF-8 source file byte length", "PASS" if main is not None else "NOT_MEASURED"),
        "skill_md_lines": metric(len(text.splitlines()) if main is not None else None, "lines", "str.splitlines()", "PASS" if main is not None else "NOT_MEASURED"),
        "skill_md_words": metric(len(text.split()) if main is not None else None, "whitespace_delimited_words", "len(str.split())", "PASS" if main is not None else "NOT_MEASURED"),
        "metadata_bytes": metric(metadata_bytes if header is not None else None, "bytes", "UTF-8 YAML frontmatter including delimiters", "PASS" if header is not None else "NOT_MEASURED"),
        "reference_files": metric(len(refs), "files", "files under any references/ directory"),
        "reference_bytes": metric(sum(e["bytes"] for e in refs), "bytes", "sum of reference file bytes"),
        "auxiliary_files": metric(extra, "files", "all regular files except root SKILL.md"),
        "total_directory_bytes": metric(total, "bytes", "sum of scanned regular file bytes"),
        "main_file_share": metric(round(main_bytes / total, 6) if main_bytes is not None and total else None,
                                  "fraction", "SKILL.md bytes / total directory bytes",
                                  "PASS" if main_bytes is not None and total else "NOT_APPLICABLE"),
        "model_tokens": metric(None, "tokens", "no model tokenizer invoked", "NOT_MEASURED"),
    }
    frontmatter = digest(json_bytes(header)) if isinstance(header, dict) else None
    portability = {
        "static_paths": {"status": "FAIL" if any(f["severity"] == "FAIL" and f["rule_id"] in ("PATH", "LINK001", "ANCHOR001") for f in findings) else "PASS",
                         "method": "offline path/symlink/Markdown link checks"},
        "client_contracts": [{
            "client_id": c["client_id"], "layouts": c["supported_skill_layouts"],
            "filesystem_test_status": c["filesystem_test_status"],
            "source_contract_status": c["source_contract_status"],
            "live_activation": "NOT_MEASURED",
        } for c in clients],
        "required_external_tools": {"status": "NOT_MEASURED", "value": None,
                                    "method": "no complete dependency parser or runtime probes"},
        "platform_specific_behavior": {"status": "NOT_MEASURED", "value": None,
                                       "method": "static source cannot prove cross-platform execution"},
    }
    ordered = sorted(findings, key=lambda f: (f["path"], f["rule_id"], f.get("line", 0), f["reason"]))
    failed = bool(ordered)
    return {
        "skill_id": skill_id, "skill_path": folder.relative_to(root).as_posix(),
        "schema_version": SCHEMA_VERSION, "source_revision": revision, "measurement_method": METHOD,
        "structural_validation": {
            "status": "FAIL" if failed else "PASS",
            "local_frontmatter": "FAIL" if any(f["rule_id"] in ("FRONTMATTER", "SKILL", "ENCODING") for f in ordered) else "PASS",
            "local_links_and_inventory": "FAIL" if any(f["rule_id"] not in ("FRONTMATTER", "ENCODING") for f in ordered) else "PASS",
            "official_skills_ref": "NOT_MEASURED",
            "note": "The official skills-ref runs independently in CI; no success inferred here.",
        },
        "portability": portability,
        "context_footprint": footprint,
        "evidence_levels": {
            "source_validated": {"status": "FAIL" if failed else "PASS",
                                 "method": "Toolkit local static checks; official skills-ref separate"},
            **{level: {"status": "NOT_MEASURED", "method": "No stage-specific evidence in offline source metrics"}
               for level in ("packaged", "installed", "discovered", "activated", "effective")},
        },
        "reproducibility": {"status": "NOT_MEASURED",
                            "repeat_measurement": "NOT_MEASURED",
                            "scope": "deterministic local static bytes and parsed Markdown; not AI behavior",
                            "content_fingerprint_sha256": digest(json_bytes(entries)),
                            "revision_pinned": revision is not None,
                            "windows_linux_ci": "NOT_MEASURED"},
        "regression_indicators": [],
        "empirical_effectiveness": {
            field: metric(None, "unknown", "requires real independently reviewed agent trials: Issue #11", "NOT_MEASURED")
            for field in EMPIRICAL_FIELDS
        },
        "frontmatter_sha256": frontmatter, "file_inventory": entries, "findings": ordered,
    }


def collect(root: Path = ROOT, skill: str | None = None,
            revision: str | None = None) -> dict:
    # Resolve Windows 8.3 short-name aliases before the shared Markdown scanner;
    # it compares resolved paths with the supplied repository root.
    root = root.resolve()
    if not root.is_dir():
        raise MetricsError("Repository root does not exist")
    if revision is not None and not SHA.fullmatch(revision):
        raise MetricsError("source_revision must be a full 40-hex commit SHA")
    names = inventory(root)
    if skill is not None and skill not in names:
        raise MetricsError("Unknown skill ID: " + skill)
    pinned = revision if revision is not None else revision_of(root)
    try:
        registry = load_registry(root / "compatibility" / "clients.json")
        clients = registry["clients"]
    except (OSError, ValueError, TypeError, KeyError):
        clients = []  # standalone fixtures do not require a client registry
    selected = [skill] if skill is not None else sorted(names)
    records = [measure_skill(root, name, names[name], pinned, clients) for name in selected]
    return {
        "schema_version": SCHEMA_VERSION, "measurement_method": METHOD,
        "source_revision": pinned, "scope": "single" if skill else "all",
        "skill_count": len(records),
        "structural_pass": sum(r["structural_validation"]["status"] == "PASS" for r in records),
        "status": "FAIL" if any(r["structural_validation"]["status"] == "FAIL" for r in records) else "PASS",
        "skills": records,
        "limitations": "Static source measurements, not observed agent discovery, activation, success, token use or cross-platform behavior.",
    }


def _validate_report(value: object) -> dict[str, dict]:
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION or value.get("measurement_method") != METHOD:
        raise MetricsError("Unknown or unsupported baseline report schema/method")
    rev = value.get("source_revision")
    if not isinstance(rev, str) or not SHA.fullmatch(rev):
        raise MetricsError("Historical baseline must identify a full commit SHA")
    records = value.get("skills")
    if not isinstance(records, list) or not records:
        raise MetricsError("Baseline has no skills")
    indexed = {}
    for r in records:
        if not isinstance(r, dict) or r.get("schema_version") != SCHEMA_VERSION or r.get("source_revision") != rev:
            raise MetricsError("Invalid or mixed-revision baseline record")
        name = r.get("skill_id")
        if not isinstance(name, str) or not NAME.fullmatch(name) or name in indexed:
            raise MetricsError("Duplicate/unsafe skill ID in baseline")
        if not isinstance(r.get("file_inventory"), list) or not isinstance(r.get("context_footprint"), dict):
            raise MetricsError("Incomplete baseline")
        for item in r["file_inventory"]:
            if not isinstance(item, dict) or set(item) != {"path", "kind", "bytes", "sha256"}:
                raise MetricsError("Malformed baseline file inventory")
            path = item["path"]
            if not isinstance(path, str) or not path or "\\" in path or Path(path).is_absolute() or ".." in Path(path).parts:
                raise MetricsError("Unsafe baseline filename")
            if (not isinstance(item["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", item["sha256"])
                    or type(item["bytes"]) is not int or item["bytes"] < 0):
                raise MetricsError("Invalid baseline file hash/size")
        indexed[name] = r
    return indexed


def compare(baseline: dict, candidate: dict) -> dict:
    before, after = _validate_report(baseline), _validate_report(candidate)
    if baseline["scope"] != "all" or candidate["scope"] != "all":
        raise MetricsError("Revision comparison requires full-inventory reports")
    if not isinstance(candidate.get("source_revision"), str) or not SHA.fullmatch(candidate["source_revision"]):
        raise MetricsError("Candidate must have a pinned commit SHA")
    changes = []
    for name in sorted(before.keys() | after.keys()):
        old, new = before.get(name), after.get(name)
        indicators = []
        if old is None:
            indicators.append({"status": "WARNING", "kind": "skill_added"})
        elif new is None:
            indicators.append({"status": "WARNING", "kind": "skill_removed"})
        else:
            b = {f["path"]: f for f in old["file_inventory"]}
            c = {f["path"]: f for f in new["file_inventory"]}
            for file in sorted(b.keys() | c.keys()):
                prior, current = b.get(file), c.get(file)
                if prior is None:
                    indicators.append({"status": "WARNING", "kind": "file_added", "file": file})
                elif current is None:
                    indicators.append({"status": "WARNING", "kind": "file_removed", "file": file})
                elif current["sha256"] != prior["sha256"]:
                    kind = ("skill_instructions_changed" if file == "SKILL.md" else
                            "executable_source_changed" if current["kind"] == "executable_source" else
                            "file_changed")
                    indicators.append({"status": "WARNING", "kind": kind, "file": file})
            if old["frontmatter_sha256"] != new["frontmatter_sha256"]:
                indicators.append({"status": "WARNING", "kind": "frontmatter_changed"})
            if old["skill_path"] != new["skill_path"]:
                indicators.append({"status": "WARNING", "kind": "skill_path_changed"})
            if old["portability"] != new["portability"]:
                indicators.append({"status": "WARNING", "kind": "portability_contract_changed"})
            if old["structural_validation"]["status"] != "FAIL" and new["structural_validation"]["status"] == "FAIL":
                indicators.append({"status": "FAIL", "kind": "new_structural_failure"})
            size_before = old["context_footprint"]["skill_md_bytes"]["value"]
            size_after = new["context_footprint"]["skill_md_bytes"]["value"]
            if size_before is not None and size_after is not None and size_before != size_after:
                indicators.append({"status": "PASS", "kind": "instruction_size_delta",
                                   "unit": "bytes", "delta": size_after - size_before})
        if indicators:
            changes.append({"skill_id": name, "indicators": indicators})
    return {"schema_version": SCHEMA_VERSION, "measurement_method": METHOD,
            "baseline_revision": baseline["source_revision"], "candidate_revision": candidate["source_revision"],
            "status": "FAIL" if any(i["status"] == "FAIL" for c in changes for i in c["indicators"]) else "PASS",
            "changed_skills": len(changes), "changes": changes,
            "note": "WARNING indicates review, not a statistical probability or a CI failure."}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--skill", help="One manifest skill ID")
    p.add_argument("--revision", help="Explicit 40-character Git commit SHA")
    p.add_argument("--baseline", type=Path, help="Pinned JSON report to compare against")
    p.add_argument("--json-report", type=Path, help="Write deterministic JSON report")
    p.add_argument("--check-repeat", action="store_true", help="Confirm identical serialised report on a second measurement")
    p.add_argument("--summary", action="store_true", help="Print compact counts instead of the JSON report")
    args = p.parse_args()
    try:
        report = collect(args.root, args.skill, args.revision)
        if args.check_repeat:
            if json_bytes(report) != json_bytes(collect(args.root, args.skill, args.revision)):
                raise MetricsError("Static metrics changed between repeat measurements")
            for entry in report["skills"]:
                entry["reproducibility"]["status"] = "PASS"
                entry["reproducibility"]["repeat_measurement"] = "PASS"
        if args.baseline is not None:
            base = json.loads(args.baseline.read_text(encoding="utf-8"))
            report["comparison"] = compare(base, report)
        output = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.json_report:
            args.json_report.write_text(output, encoding="utf-8")
        if args.summary:
            print(f"Skills={report['skill_count']} structural_pass={report['structural_pass']} "
                  f"status={report['status']} repeat={'PASS' if args.check_repeat else 'NOT_MEASURED'}")
        elif not args.json_report:
            print(output, end="")
        return 1 if report["status"] == "FAIL" or report.get("comparison", {}).get("status") == "FAIL" else 0
    except (MetricsError, ValueError, OSError, UnicodeError, TypeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
