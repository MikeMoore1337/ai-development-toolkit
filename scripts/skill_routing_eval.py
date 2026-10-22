#!/usr/bin/env python3
"""Offline lexical skill-routing diagnostic. NOT real AI-client activation."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sys

from profile_metrics import skill_paths
from validate_pack import parse_metadata

ROOT = Path(__file__).resolve().parents[1]
WORD = re.compile(r"[a-zа-яё0-9]+")
CYRILLIC = re.compile(r"[а-яё]", re.I)
ALIAS_FILE = ROOT / "fixtures/skill_routing_aliases.json"


class RoutingInputError(ValueError):
    """Invalid source inventory or curated routing cases."""


def terms(text: str) -> list[str]:
    words = WORD.findall(text.lower())
    result = []
    for word in words:
        if len(word) > 5 and word.endswith("ies"):
            word = word[:-3] + "y"
        elif len(word) > 5 and word.endswith("ing"):
            word = word[:-3]
        elif len(word) > 4 and word.endswith("ed"):
            word = word[:-2]
        elif len(word) > 4 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        if len(word) > 2:
            result.append(word)
    return result


def read_catalog(root: Path) -> dict[str, str]:
    """Load only declared skill descriptions; never execute bundled scripts."""
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    catalog: dict[str, str] = {}
    for name, folder in sorted(skill_paths(root, manifest).items()):
        file = folder / "SKILL.md"
        if folder.is_symlink() or file.is_symlink() or not file.is_file():
            raise RoutingInputError(f"Missing/linked SKILL.md: {name}")
        if not file.resolve().is_relative_to(root.resolve()):
            raise RoutingInputError(f"Escaping SKILL.md: {name}")
        meta = parse_metadata(file.read_text(encoding="utf-8"))
        if meta.get("name") != name or not isinstance(meta.get("description"), str):
            raise RoutingInputError(f"Invalid metadata: {name}")
        catalog[name] = meta["description"]
    if not catalog:
        raise RoutingInputError("Empty declared skill catalog")
    return catalog


def read_aliases(path: Path, catalog: dict[str, str]) -> dict[str, list[str]]:
    """Curated lexical hints; never a claim of semantic model understanding."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"schema_version", "aliases"}:
        raise RoutingInputError("Invalid alias registry structure")
    if data["schema_version"] != 1 or not isinstance(data["aliases"], dict):
        raise RoutingInputError("Invalid alias registry version")
    result: dict[str, list[str]] = {}
    for skill, phrases in sorted(data["aliases"].items()):
        if skill not in catalog:
            raise RoutingInputError("Unknown skill alias: " + str(skill))
        if not isinstance(phrases, list) or not phrases or len(phrases) > 16:
            raise RoutingInputError("Invalid alias list for " + skill)
        if any(not isinstance(text, str) or not text.strip() or len(text) > 160
               for text in phrases) or len(set(phrases)) != len(phrases):
            raise RoutingInputError("Invalid or duplicate alias for " + skill)
        result[skill] = phrases
    return result


def prompt_language(text: str) -> str:
    """Surface-script heuristic; mixed RU/technical English is treated as RU."""
    return "ru" if CYRILLIC.search(text) else "en"


def alias_stem(token: str) -> str:
    """Conservative Cyrillic-prefix heuristic, used only for optional aliases."""
    if CYRILLIC.search(token) and len(token) > 5:
        return token[:5]
    return token


def vectors(catalog: dict[str, str]) -> tuple[dict[str, Counter], dict[str, float]]:
    docs: dict[str, Counter] = {}
    df: Counter = Counter()
    for name, description in sorted(catalog.items()):
        # A "Not for ..." clause describes exclusions, not positive triggers.
        # It must not pull ordinary SQL/API fixes into data-engineering.
        positive_description = re.split(r"\bnot for\b", description, maxsplit=1, flags=re.I)[0]
        weighted = Counter(terms(positive_description))
        for token in terms(name.replace("-", " ")):
            weighted[token] += 3
        docs[name] = weighted
        df.update(weighted.keys())
    n = len(docs)
    idf = {token: 1.0 + math.log((n + 1) / (frequency + 1))
           for token, frequency in df.items()}
    return docs, idf


def ranking(prompt: str, catalog: dict[str, str],
            docs: dict[str, Counter], idf: dict[str, float],
            aliases: dict[str, list[str]] | None = None) -> list[str]:
    query = set(terms(prompt))
    query_normalized = " ".join(terms(prompt))
    language = prompt_language(prompt)
    query_alias_terms = {alias_stem(token) if language == "ru" else token
                         for token in query}
    scores = []
    for name, vector in docs.items():
        overlap = sum(vector[t] * idf[t] for t in query & vector.keys())
        norm = math.sqrt(sum(v * v for v in vector.values()))
        score = overlap / norm if norm else 0.0
        name_phrase = " ".join(terms(name.replace("-", " ")))
        if name_phrase and name_phrase in query_normalized:
            score += 2.0
        if aliases:
            for phrase in aliases.get(name, []):
                # Match curated examples within their own language. Cyrillic
                # inflections get conservative prefix normalization; this is
                # not semantic understanding and is tested separately.
                if prompt_language(phrase) != language:
                    continue
                token_set = {alias_stem(token) if language == "ru" else token
                             for token in terms(phrase)}
                overlap_alias = len(query_alias_terms & token_set)
                if overlap_alias >= 2:
                    score += (3.0 * (overlap_alias - 1)
                              * overlap_alias / len(token_set))
        scores.append((score, name))
    return [name for _, name in sorted(scores, key=lambda pair: (-pair[0], pair[1]))]


def load_cases(file: Path, catalog: dict[str, str]) -> list[dict]:
    data = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"schema_version", "cases"}:
        raise RoutingInputError("Expected schema_version and cases")
    if data["schema_version"] != 1 or not isinstance(data["cases"], list) or not data["cases"]:
        raise RoutingInputError("Invalid routing cases")
    seen = set()
    for case in data["cases"]:
        if not isinstance(case, dict) or set(case) != {"id", "target", "positive", "negative"}:
            raise RoutingInputError("Invalid case keys")
        if not isinstance(case["id"], str) or not case["id"] or case["id"] in seen:
            raise RoutingInputError("Invalid or duplicated case ID")
        seen.add(case["id"])
        if case["target"] not in catalog:
            raise RoutingInputError(f"Unlisted skill: {case['target']}")
        for kind in ("positive", "negative"):
            prompts = case[kind]
            if not isinstance(prompts, list) or not prompts:
                raise RoutingInputError(f"Missing {kind}: {case['id']}")
            for item in prompts:
                if not isinstance(item, str) or not item.strip() or len(item) > 1000:
                    raise RoutingInputError(f"Invalid prompt: {case['id']}")
    return data["cases"]


def evaluate(catalog: dict[str, str], cases: list[dict], top_k: int = 3,
             aliases: dict[str, list[str]] | None = None) -> dict:
    if not 1 <= top_k <= len(catalog):
        raise RoutingInputError("top_k out of bounds")
    docs, idf = vectors(catalog)
    observations = []
    for case in cases:
        for polarity, prompts in (("positive", case["positive"]), ("negative", case["negative"])):
            for prompt in prompts:
                order = ranking(prompt, catalog, docs, idf, aliases)
                position = order.index(case["target"]) + 1
                accepted = position <= top_k if polarity == "positive" else position != 1
                observations.append({
                    "case": case["id"], "target": case["target"],
                    "kind": polarity, "language": prompt_language(prompt),
                    "prompt": prompt, "rank": position,
                    "top3": order[:3], "pass": accepted,
                })
    failures = [row for row in observations if not row["pass"]]
    covered = {item["target"] for item in cases}
    languages = {}
    for language in ("en", "ru"):
        positives = {row["target"] for row in observations
                     if row["kind"] == "positive" and row["language"] == language}
        negatives = {row["target"] for row in observations
                     if row["kind"] == "negative" and row["language"] == language}
        languages[language] = {
            "tested_targets": sorted(positives & negatives),
            "tested_target_count": len(positives & negatives),
            "positive_prompts": sum(row["language"] == language and row["kind"] == "positive"
                                    for row in observations),
            "negative_prompts": sum(row["language"] == language and row["kind"] == "negative"
                                    for row in observations),
        }
    return {
        "method": "lexical-description-curated-alias-ranking-v3" if aliases else "lexical-description-ranking-v1",
        "language_classification": "script_heuristic_not_semantic_detection",
        "client_skill_selection": "NOT_OBSERVED",
        "client_effectiveness": "NOT_TESTED",
        "coverage": {
            "catalog_total": len(catalog),
            "curated_targets": len(covered),
            "uncovered_targets": sorted(set(catalog) - covered),
            "languages": languages,
            "interpretation": "curated lexical coverage only; no observed client activation",
        },
        "classification": "offline_source_diagnostic",
        "actual_skill_discovery": "NOT_MEASURED",
        "actual_skill_activation": "NOT_MEASURED",
        "model_effectiveness": "NOT_MEASURED",
        "skill_count": len(catalog),
        "prompt_count": len(observations),
        "passed": len(observations) - len(failures),
        "failed": len(failures),
        "observations": observations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--cases", type=Path, default=ROOT / "fixtures/skill_routing_cases.json")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--aliases", type=Path, default=ALIAS_FILE)
    parser.add_argument("--strict", action="store_true", help="Fail for mismatched curated prompts")
    args = parser.parse_args(argv)
    try:
        catalog = read_catalog(args.root.resolve())
        cases = load_cases(args.cases, catalog)
        aliases = read_aliases(args.aliases, catalog)
        report = evaluate(catalog, cases, top_k=args.top_k, aliases=aliases)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 1 if args.strict and report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
