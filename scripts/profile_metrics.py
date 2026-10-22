#!/usr/bin/env python3
"""Deterministic file size/overlap report; file bytes are NOT model token counts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def skill_paths(root: Path, manifest: dict) -> dict[str, Path]:
    found = {}
    for name in manifest["core_skills"] + manifest.get("extension_skills", []):
        if name in found:
            raise ValueError(f"Duplicate source skill: {name}")
        found[name] = root / ".agents" / "skills" / name
    for pack in manifest.get("extension_packs", {}).values():
        for name in pack["skills"]:
            if name in found:
                raise ValueError(f"Duplicate source skill: {name}")
            found[name] = root / pack["skill_root"] / name
    return found


def measure(root: Path, manifest: dict, profile: str | None = None) -> dict:
    profiles = manifest["profiles"]
    if profile is not None and profile not in profiles:
        raise ValueError(f"Unknown profile: {profile}")
    available = skill_paths(root, manifest)
    report = {}
    for name in sorted([profile] if profile else profiles):
        skills = profiles[name]
        if len(set(skills)) != len(skills):
            raise ValueError(f"Duplicate entries in profile: {name}")
        total = skill_bytes = refs = 0
        for skill in skills:
            if skill not in available:
                raise ValueError(f"Unknown skill in {name}: {skill}")
            folder = available[skill]
            if not folder.is_dir() or folder.is_symlink() or folder.is_junction():
                raise ValueError(f"Missing/linked skill folder: {skill}")
            if not (folder / "SKILL.md").is_file():
                raise ValueError(f"Missing SKILL.md for {skill}")
            for file in sorted(folder.rglob("*")):
                if file.is_symlink() or file.is_junction():
                    raise ValueError(f"Linked skill content: {file}")
                if not file.is_file():
                    continue
                size = file.stat().st_size
                total += size
                if file.name == "SKILL.md" and file.parent == folder:
                    skill_bytes += size
                if "references" in file.relative_to(folder).parts[:-1]:
                    refs += 1
        overlap = {other: len(set(skills) & set(other_skills))
                   for other, other_skills in sorted(profiles.items())
                   if other != name and set(skills) & set(other_skills)}
        report[name] = {
            "skill_count": len(skills),
            "installed_file_bytes": total,
            "skill_md_bytes": skill_bytes,
            "reference_file_count": refs,
            "toolkit_required_runtime_dependencies": 0,
            "overlap_skill_counts": overlap,
        }
    return {"measurement": "source file bytes; NOT model tokens", "profiles": report}



def audit_exact_sources(root: Path, manifest: dict) -> dict:
    """Detect exact source equality and near-identical profile memberships.

    Hashes cover only SKILL.md and references; byte identity is not semantic
    duplication and is never a measured token or runtime saving.
    """
    import hashlib

    groups: dict[str, list[str]] = {}
    inspected = 0
    for name, folder in sorted(skill_paths(root, manifest).items()):
        if not folder.is_dir() or folder.is_symlink() or folder.is_junction():
            raise ValueError(f"Missing/linked skill folder: {name}")
        for file in sorted(folder.rglob("*")):
            if file.is_symlink() or file.is_junction():
                raise ValueError(f"Linked skill content: {file}")
            if not file.is_file():
                continue
            relative = file.relative_to(folder).as_posix()
            if relative != "SKILL.md" and not relative.startswith("references/"):
                continue
            digest = hashlib.sha256()
            with file.open("rb") as handle:
                for block in iter(lambda: handle.read(65536), b""):
                    digest.update(block)
            groups.setdefault(digest.hexdigest(), []).append(name + "/" + relative)
            inspected += 1

    identical = [
        {"sha256": digest, "paths": sorted(paths)}
        for digest, paths in sorted(groups.items())
        if len(paths) > 1
    ]
    profiles = sorted(manifest["profiles"].items())
    high_overlap = []
    for i, (first, skills_a) in enumerate(profiles):
        a = set(skills_a)
        for second, skills_b in profiles[i + 1:]:
            b = set(skills_b)
            common = len(a & b)
            union = len(a | b)
            if union and 4 * common >= 3 * union:
                high_overlap.append({
                    "profiles": [first, second],
                    "shared_skills": common,
                    "union_skills": union,
                    "jaccard": round(common / union, 4),
                })
    high_overlap.sort(key=lambda x: (-x["jaccard"], x["profiles"]))
    return {
        "classification": "OFFLINE_EXACT_SOURCE_AND_PROFILE_MEMBERSHIP_AUDIT",
        "source_files_hashed": inspected,
        "byte_identical_groups": identical,
        "high_profile_overlap_at_least_75_percent": high_overlap,
        "model_tokens_saved": "NOT_MEASURED",
        "runtime_effect": "NOT_TESTED",
        "limitations": [
            "Exact SHA256 equality cannot detect paraphrased instructions.",
            "Profile membership overlap is not proof of duplicate behavior.",
            "File bytes and references are not observed model-context tokens.",
        ],
    }



MAX_DIRECTIVE_SOURCE_BYTES = 256 * 1024
MAX_DIRECTIVE_SOURCES = 500
MAX_DIRECTIVE_LINES = 1500
MAX_OVERLAP_RESULTS = 100


def audit_directives(root: Path, manifest: dict) -> dict:
    """Offline lexical duplicate candidates, not semantic equivalence."""
    import hashlib
    import re

    token_pattern = re.compile(r"[^\W_]+", re.UNICODE)
    list_prefix = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
    passages: list[dict] = []
    sources = 0
    for skill, folder in sorted(skill_paths(root, manifest).items()):
        if not folder.is_dir() or folder.is_symlink() or folder.is_junction():
            raise ValueError(f"Missing/linked skill folder: {skill}")
        for file in sorted(folder.rglob("*")):
            if file.is_symlink() or file.is_junction():
                raise ValueError(f"Linked skill source: {skill}")
            if not file.is_file():
                continue
            rel = file.relative_to(folder).as_posix()
            if rel != "SKILL.md" and not (
                rel.startswith("references/") and file.suffix.lower() == ".md"
            ):
                continue
            sources += 1
            if sources > MAX_DIRECTIVE_SOURCES or file.stat().st_size > MAX_DIRECTIVE_SOURCE_BYTES:
                raise ValueError("Directive scan input exceeds a safe bound")
            try:
                contents = file.read_text(encoding="utf-8")
            except UnicodeError as exc:
                raise ValueError("Non-UTF8 source requires manual review") from exc
            frontmatter = contents.startswith("---\n")
            fence = False
            for number, line in enumerate(contents.splitlines(), 1):
                line_text = line.strip()
                if frontmatter:
                    if number > 1 and line_text == "---":
                        frontmatter = False
                    continue
                if line_text.startswith((chr(96) * 3, "~~~")):
                    fence = not fence
                    continue
                if fence or not line_text or line_text.startswith(("#", "|", ">", "![", "<!--")):
                    continue
                tokens = tuple(token_pattern.findall(list_prefix.sub("", line_text).casefold()))
                if not 12 <= len(tokens) <= 160:
                    continue
                if len(passages) >= MAX_DIRECTIVE_LINES:
                    raise ValueError("Directive scan line count exceeds a safe bound")
                canonical = " ".join(tokens)
                passages.append({
                    "source": f"{skill}/{rel}", "line": number,
                    "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                    "terms": frozenset(tokens), "size": len(tokens),
                })
    groups: dict[str, list[dict]] = {}
    for item in passages:
        groups.setdefault(item["sha256"], []).append({
            "source": item["source"], "line": item["line"]
        })
    exact = [
        {"sha256": key, "locations": sorted(locations, key=lambda x: (x["source"], x["line"]))}
        for key, locations in sorted(groups.items())
        if len({x["source"].split("/", 1)[0] for x in locations}) > 1
    ]
    exact.sort(key=lambda x: (x["locations"][0]["source"], x["sha256"]))
    near = []
    for index, left in enumerate(passages):
        for right in passages[index + 1:]:
            if left["source"].split("/", 1)[0] == right["source"].split("/", 1)[0]:
                continue
            if left["sha256"] == right["sha256"]:
                continue
            if 5 * min(left["size"], right["size"]) < 4 * max(left["size"], right["size"]):
                continue
            common = len(left["terms"] & right["terms"])
            union = len(left["terms"] | right["terms"])
            if common < 10 or common * 20 < union * 17:
                continue
            near.append({
                "left": {"source": left["source"], "line": left["line"],
                         "sha256": left["sha256"]},
                "right": {"source": right["source"], "line": right["line"],
                          "sha256": right["sha256"]},
                "lexical_jaccard": round(common / union, 4), "review_only": True,
            })
    near.sort(key=lambda x: (-x["lexical_jaccard"], x["left"]["source"],
                             x["left"]["line"], x["right"]["source"], x["right"]["line"]))
    return {
        "classification": "OFFLINE_LEXICAL_OVERLAP_CANDIDATES",
        "sources_scanned": sources,
        "directive_lines_examined": len(passages),
        "normalized_exact_groups": exact[:MAX_OVERLAP_RESULTS],
        "exact_groups_truncated": len(exact) > MAX_OVERLAP_RESULTS,
        "near_lexical_candidates": near[:MAX_OVERLAP_RESULTS],
        "near_candidates_truncated": len(near) > MAX_OVERLAP_RESULTS,
        "threshold": 0.85, "semantic_equivalence": "NOT_VERIFIED",
        "model_tokens_saved": "NOT_MEASURED", "runtime_effect": "NOT_TESTED",
        "limitations": [
            "Source lines with 12..160 normalized words only; no semantic model",
            "Common tokens, negation and word order may yield false matches",
            "Skill references are source files, not evidence of runtime loading",
            "Review candidates manually; never rewrite protected or licensed skills",
        ],
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="One manifest profile; default all")
    parser.add_argument("--audit-duplicates", action="store_true",
                        help="Include exact-source and high-overlap diagnostics")
    parser.add_argument("--audit-directives", action="store_true",
                        help="Include bounded lexical directive candidates")
    args = parser.parse_args()
    try:
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        report = measure(ROOT, manifest, args.profile)
        if args.audit_duplicates:
            report["source_overlap_audit"] = audit_exact_sources(ROOT, manifest)
        if args.audit_directives:
            report["directive_overlap_audit"] = audit_directives(ROOT, manifest)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
