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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="One manifest profile; default all")
    parser.add_argument("--audit-duplicates", action="store_true",
                        help="Include exact-source and high-overlap diagnostics")
    args = parser.parse_args()
    try:
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        report = measure(ROOT, manifest, args.profile)
        if args.audit_duplicates:
            report["source_overlap_audit"] = audit_exact_sources(ROOT, manifest)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
