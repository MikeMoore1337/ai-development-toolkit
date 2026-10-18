"""Create a feature context and check local Markdown links; never certify content."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


def workspace(project, slug):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("slug must use lowercase letters, digits and hyphens")
    root = Path(project).resolve()
    if not root.is_dir():
        raise ValueError("project directory must already exist")
    folder = root / ".make-feature" / slug
    if not folder.resolve().is_relative_to(root):
        raise ValueError("feature directory must stay inside project")
    return root, folder


def initialize(project, slug, request_file):
    root, folder = workspace(project, slug)
    request = Path(request_file).read_bytes()
    if not request.decode("utf-8").strip():
        raise ValueError("nonempty UTF-8 request required")
    # Exclusive directory creation also rejects an existing or partial context.
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "01-request.md").write_bytes(request)
    (folder / "manifest.json").write_text(json.dumps({
        "schema": 1, "slug": slug,
        "request_sha256": hashlib.sha256(request).hexdigest()
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "00-index.md").write_text(
        "# Контекст функции\n\n"
        "Исходный запрос: [01-request.md](01-request.md)\n\n"
        "Цель: ещё не восстановлена из запроса.\n"
        "Текущий этап: замысел, не принят.\n"
        "Режим, предел, разрешения: сверить по запросу и среде.\n"
        "Реальные процессы/агенты: запуск не записан.\n\n"
        "| Этап | Статус | Актуальный документ | Основание перехода |\n"
        "|---|---|---|---|\n"
        "| Замысел | pending | ещё не создан | критерии не приняты |\n\n"
        "Принятые решения: нет.\n"
        "Открыто: восстановить цель и критерии.\n"
        "Следующий шаг: прочитать запрос и правила; выбрать режим и сохранить C*/решение в 02-solution.md.\n",
        encoding="utf-8")
    return {"workspace": str(folder), "created": ["00-index.md", "01-request.md", "manifest.json"]}


def link_data(text):
    # Code examples are not actual document dependencies.
    clean = re.sub(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$", "", text)
    clean = re.sub(r"(`+)(?!`).*?(?<!`)\1(?!`)", "", clean, flags=re.S)
    targets = []
    for match in re.finditer(r"\[[^\]\n]*\]\(", clean):
        i = match.end()
        target, depth = [], 0
        if i < len(clean) and clean[i] == "<":
            end = clean.find(">", i + 1)
            if end == -1:
                continue
            target, i = [clean[i:end+1]], end + 1
        else:
            while i < len(clean):
                c = clean[i]
                if c == "\\" and i + 1 < len(clean):
                    target.append(clean[i+1]); i += 2; continue
                if c.isspace() or (c == ")" and depth == 0):
                    break
                if c == "(": depth += 1
                if c == ")": depth -= 1
                target.append(c); i += 1
        # Destination parentheses are balanced; the outer close and optional title remain.
        if target and depth == 0 and re.match(r'''(?:\s+(?:"[^"\n]*"|'[^'\n]*'|\([^\n]*?\)))?\s*\)''', clean[i:]):
            targets.append("".join(target))
    definitions = re.findall(r"(?m)^[ \t]{0,3}\[([^\]\n]+)\]:[ \t]*(<[^>]+>|[^\s]+)", clean)
    targets.extend(target for _, target in definitions)
    normalize = lambda label: " ".join(label.split()).casefold()
    defined = {normalize(label) for label, _ in definitions}
    references = re.findall(r"\[([^\]\n]+)\]\[([^\]\n]*)\]", clean)
    missing = sorted({normalize(label or text) for text, label in references
                      if normalize(label or text) not in defined})
    return targets, missing


def links(text):
    return link_data(text)[0]


def check(project, slug):
    root, folder = workspace(project, slug)
    data = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    errors = []
    request = folder / "01-request.md"
    if request.is_symlink() or not request.is_file():
        errors.append("source request must be a regular preserved file")
    elif hashlib.sha256(request.read_bytes()).hexdigest() != data["request_sha256"]:
        errors.append("source request changed")
    if not (folder / "00-index.md").is_file():
        errors.append("index missing")
    scanned = 0
    for document in sorted(folder.rglob("*.md")):
        # Archived source material is preserved, not loaded as active context.
        if "archive" in document.relative_to(folder).parts or document == request:
            continue
        if document.is_symlink() or not document.resolve().is_relative_to(root):
            errors.append(f"document outside project: {document.relative_to(folder)}")
            continue
        scanned += 1
        targets, missing = link_data(document.read_text(encoding="utf-8"))
        errors.extend(f"undefined reference: {document.relative_to(folder)} -> {label}" for label in missing)
        for target in targets:
            target = target.strip("<>")
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            path = unquote(target.split("#", 1)[0])
            resolved = (document.parent / path).resolve()
            if not resolved.is_relative_to(root):
                errors.append(f"link outside project: {document.relative_to(folder)} -> {target}")
            elif not resolved.exists():
                errors.append(f"broken link: {document.relative_to(folder)} -> {target}")
    return {"structurally_valid": not errors, "content_accepted": False,
            "active_documents_checked": scanned, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "check"))
    parser.add_argument("--project", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--request-file")
    args = parser.parse_args()
    try:
        if args.command == "init":
            if not args.request_file:
                raise ValueError("init requires --request-file")
            result = initialize(args.project, args.slug, args.request_file)
        else:
            result = check(args.project, args.slug)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("structurally_valid", True) else 1
    except (OSError, ValueError, KeyError, TypeError) as ex:
        print(json.dumps({"error": str(ex)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
