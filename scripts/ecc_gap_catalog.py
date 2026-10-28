#!/usr/bin/env python3
"""Read-only, exhaustive ECC source-vs-Toolkit component inventory (#435).

This is an audit report generator, NOT an installer, scanner, skill manager, or
runtime compatibility attestation. It does not execute ECC instructions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import re
import subprocess

KINDS = ("skills", "agents", "commands", "rules")
STATUSES = {"ALREADY_PRESENT", "ADOPT_AS_IS_CANDIDATE", "HOLD_CONFLICT",
            "HOLD_UNSUPPORTED", "HOLD_REVIEW"}
MAX_DESCRIPTION = 350


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args],
                            text=True, capture_output=True, check=True,
                            encoding="utf-8", timeout=35)
    return result.stdout.strip()


def source_paths(repo: Path) -> list[str]:
    paths = git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
    return sorted(p for p in paths if p.startswith(tuple(k + "/" for k in KINDS)))


def read_text(repo: Path, name: str) -> str:
    path = repo / name
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 512_000:
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeError:
        return ""


def frontmatter(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if not text.startswith("---\n"):
        return result
    end = text.find("\n---\n", 4)
    if end < 0:
        return result
    lines = text[4:end].splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^(name|description|license|trigger):\\s*(.*)$", line)
        if not match:
            continue
        key, value = match.groups()
        if value in {">-", ">", "|", "|-"}:
            following = []
            for continuation in lines[index + 1:]:
                if not continuation.startswith((" ", "\\t")):
                    break
                if continuation.strip():
                    following.append(continuation.strip())
            value = " ".join(following)
        result[key] = value.strip(" \\t'\\\"")
    return result


def describe(text: str, kind: str, path: str) -> tuple[str, str, str]:
    fields = frontmatter(text)
    headline = next((m.group(1) for m in re.finditer(
        r"^#\s+(.+)$", text, re.M)), "")
    description = fields.get("description") or headline or Path(path).stem
    description = re.sub(r"\s+", " ", description)[:MAX_DESCRIPTION]
    trigger = fields.get("trigger", "NOT_DECLARED")
    if trigger == "NOT_DECLARED":
        match = re.search(r"\bUse when\b[^.\n]{0,160}", description, re.I)
        if match:
            trigger = match.group(0)
    return description, trigger, fields.get("license", "ROOT_MIT_CLAIM_ONLY")


def group_paths(paths: list[str]) -> dict[tuple[str, str], list[str]]:
    out: dict[tuple[str, str], list[str]] = {}
    for path in paths:
        root, remainder = path.split("/", 1)
        if root == "skills":
            component = remainder.split("/", 1)[0]
        else:
            component = remainder
        out.setdefault((root, component), []).append(path)
    return out


def toolkit_analogues(root: Path) -> dict[str, list[str]]:
    registry = json.loads((root / "provenance" / "skills.json").read_text(encoding="utf-8"))
    result: dict[str, list[str]] = {}
    for item in registry["components"]:
        if item.get("kind") not in {"skill", "role", "profile"}:
            continue
        path = item.get("path", "")
        slug = Path(path.rstrip("/")).name.lower()
        if slug:
            result.setdefault(slug, []).append(path)
    return result


def decision_index(root: Path) -> dict[str, dict]:
    file = root / "integrations" / "ecc" / "catalog_review.json"
    data = json.loads(file.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("invalid catalogue decision schema")
    results = {}
    for item in data["decisions"]:
        path = item["path"]
        if path in results or item["status"] not in STATUSES or not item.get("reason"):
            raise ValueError("invalid/duplicate audited catalogue decision: " + path)
        results[path] = item
    return results


def load_install(root: Path) -> tuple[dict, dict]:
    base = root / "manifests"
    components = json.loads((base / "install-components.json").read_text(encoding="utf-8"))["components"]
    modules = json.loads((base / "install-modules.json").read_text(encoding="utf-8"))["modules"]
    return {v["id"]: v for v in components}, {v["id"]: v for v in modules}


def build(ecc: Path, toolkit: Path, sha: str) -> list[dict]:
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("pin must be exact 40-character lowercase SHA")
    if git(ecc, "rev-parse", "HEAD") != sha:
        raise ValueError("ECC source HEAD differs from the approved immutable pin")
    paths = source_paths(ecc)
    if not paths:
        raise ValueError("upstream ECC content roots are missing")
    groups = group_paths(paths)
    if not all(any(x[0] == k for x in groups) for k in KINDS):
        raise ValueError("one of the four upstream ECC content roots is absent")
    analogues = toolkit_analogues(toolkit)
    decisions = decision_index(toolkit)
    components, modules = load_install(ecc)
    unexpected = set(decisions) - {f"{k}/{v}" for k, v in groups}
    if unexpected:
        raise ValueError("reviewed paths are absent from pinned upstream: " + repr(sorted(unexpected)))
    rows = []
    for (kind, component), files in sorted(groups.items()):
        path = f"{kind}/{component}"
        primary = (path + "/SKILL.md" if kind == "skills" and
                   path + "/SKILL.md" in files else
                   next((f for f in files if f.endswith(".md")), files[0]))
        text = read_text(ecc, primary)
        description, trigger, declared_license = describe(text, kind, primary)
        short = component.removesuffix(".md").split("/")[-1]
        exact_analogue = sorted(set(analogues.get(short.lower(), [])))
        upstream_component = components.get("skill:" + short if kind == "skills"
                                            else "agent:" + short if kind == "agents"
                                            else "")
        module_ids = upstream_component.get("modules", []) if upstream_component else []
        dependency_ids = sorted({dep for m in module_ids for dep in modules.get(m, {}).get("dependencies", [])})
        targets = sorted({target for m in module_ids for target in modules.get(m, {}).get("targets", [])})
        chosen = decisions.get(path)
        if chosen:
            status = chosen["status"]
            reason = chosen["reason"]
            analogue = chosen.get("analogue") or (exact_analogue[0] if exact_analogue else "NOT_VERIFIED")
            if status == "ALREADY_PRESENT" and (analogue == "NOT_VERIFIED" or
                                                not (toolkit / analogue).exists()):
                raise ValueError("covered decision lacks real Toolkit evidence: " + path)
            if status == "ADOPT_AS_IS_CANDIDATE" and not upstream_component:
                raise ValueError("adoption without official ECC component: " + path)
        elif kind == "skills" and "continuous-learning" == short:
            status, reason = "HOLD_UNSUPPORTED", "Legacy v1 learning must not replace existing review gates"
            analogue = exact_analogue[0] if exact_analogue else "NOT_VERIFIED"
        elif exact_analogue:
            status, reason = "HOLD_REVIEW", "Matching slug only; semantic coverage not yet attested"
            analogue = exact_analogue[0]
        elif kind == "skills" and not upstream_component:
            status, reason = "HOLD_REVIEW", "Not registered in upstream selective component manifest"
            analogue = "NOT_VERIFIED"
        elif kind in {"agents", "commands", "rules"}:
            status, reason = "HOLD_CONFLICT", "Global agent, command or rule requires precedence and conflict review"
            analogue = "NOT_VERIFIED"
        else:
            status, reason = "HOLD_REVIEW", "No independently verified Toolkit functionality gap"
            analogue = "NOT_VERIFIED"
        fingerprint = hashlib.sha256()
        for filename in sorted(files):
            if (ecc / filename).is_symlink():
                raise ValueError("upstream tracked symlink requires independent review: " + filename)
            fingerprint.update(filename.encode("utf-8") + b"\0")
            fingerprint.update((ecc / filename).read_bytes())
        rows.append({
            "kind": kind.rstrip("s"), "name": short, "upstream_path": path,
            "primary_file": primary, "upstream_revision": sha,
            "sha256_component": fingerprint.hexdigest(), "source_files": len(files),
            "description": description, "trigger": trigger,
            "license": declared_license,
            "component_id": upstream_component["id"] if upstream_component else "NOT_REGISTERED",
            "upstream_modules": ",".join(module_ids) or "NOT_REGISTERED",
            "dependencies": ",".join(dependency_ids) or "NOT_DECLARED",
            "host_targets": ",".join(targets) or "NOT_VERIFIED",
            "toolkit_analogue": analogue, "status": status, "reason": reason,
            "benefit": chosen.get("benefit", "NOT_ASSESSED") if chosen else "NOT_ASSESSED",
            "test_case": chosen.get("test_case", "MANUAL_REVIEW_REQUIRED") if chosen else "MANUAL_REVIEW_REQUIRED",
            "owner_gate": "EXPLICIT_OPT_IN_REQUIRED", "live_client": "NOT_VERIFIED",
        })
    assert len(rows) == len(groups)
    assert len({r["upstream_path"] for r in rows}) == len(rows)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ecc-root", type=Path, required=True)
    parser.add_argument("--toolkit-root", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows = build(args.ecc_root.resolve(), args.toolkit_root.resolve(), args.source_revision)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with (args.output_dir / "ecc-gap-full.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (args.output_dir / "ecc-gap-full.json").write_text(
        json.dumps({"schema_version": 1, "source_revision": args.source_revision,
                    "coverage": "ALL_TRACKED_COMPONENTS_OF_FOUR_ROOTS",
                    "rows": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    by_type = Counter(row["kind"] for row in rows)
    by_status = Counter(row["status"] for row in rows)
    summary = {"source_revision": args.source_revision, "component_count": len(rows),
               "kinds": dict(sorted(by_type.items())), "statuses": dict(sorted(by_status.items())),
               "coverage": "ALL_TRACKED_COMPONENTS_OF_FOUR_ROOTS",
               "live_client": "NOT_VERIFIED", "autoinstall": False}
    (args.output_dir / "ecc-gap-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("ECC_GAP_FULL_MATRIX=PASS")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
