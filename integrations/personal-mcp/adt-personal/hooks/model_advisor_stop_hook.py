#!/usr/bin/env python3
"""Opt-in Codex Desktop Stop-hook reminder for the existing Model Advisor.

Pure stdlib and source-only. It does not call an MCP tool, launch a model, read
the Codex transcript, open local files, send network traffic, or persist data.
The user must separately install and trust a Codex lifecycle hook definition.
"""
from __future__ import annotations

import json
import re
import sys

MAX_EVENT_BYTES = 65536
MAX_MESSAGE_CHARS = 16000

# Fixed, bounded lexical signals are heuristic only, never a finding verifier.
CONFIRMED = re.compile(
    r"(?i)\b(?:blocked|confirmed|critical|severe|unsafe|reproduced|"
    r"release.blocker|defects?|vulnerabilit(?:y|ies)|fail(?:ed|ure))\b"
    r"|подтвержд|воспроизвед|дефект|уязвим|критич|ошибк|блокиру",
)
NEGATIVE_ONLY = re.compile(
    r"(?i)\b(?:no confirmed (?:issues|defects|risks)|no (?:defects|issues) found|"
    r"all checks pass|ready for release)\b"
    r"|нет подтвержденных (?:рисков|дефектов)|не обнаружено (?:ошибок|дефектов)",
)
ALREADY_ADVISED = re.compile(
    r"(?i)second.opinion (?:may|could)|independent model review|"
    r"available expert once|выбери(?:те)? (?:1|вариант)|"
    r"независим(?:ая|ую|ой) (?:модельн|провер|экспертиз)",
)
RISK_GROUPS = (
    re.compile(r"(?i)secur|vulnerab|authz|reparse|symlink|hardlink|git hook|"
               r"origin spoof|безопасност|уязвим|подмен|перенаправлен"),
    re.compile(r"(?i)rollback|recovery|journal|atomic|reset --hard|"
               r"data loss|state corrupt|fsync|откат|восстановлен|"
               r"журнал|атомарн|потер[яьи] данн|перезапис"),
    re.compile(r"(?i)concurr|toctou|race condition|stale.lock|os.lock|"
               r"deadlock|schedul|гонк|блокиров|расписан|таймер"),
)


def check_stop(event: object) -> dict[str, object]:
    """Decide only whether to request a bounded current-model continuation."""
    if not isinstance(event, dict):
        return {}
    if event.get("hook_event_name") != "Stop" or event.get("stop_hook_active") is True:
        return {}
    message = event.get("last_assistant_message")
    if not isinstance(message, str) or len(message) > MAX_MESSAGE_CHARS:
        return {}
    if not CONFIRMED.search(message) or ALREADY_ADVISED.search(message):
        return {}
    if NEGATIVE_ONLY.search(message) and not re.search(
        r"(?i)\bBLOCKED\b|подтвержденн(?:ые|ых) риск|confirmed (?:risk|defect)",
        message,
    ):
        return {}
    if sum(bool(group.search(message)) for group in RISK_GROUPS) < 2:
        return {}

    if re.search("[\u0400-\u04ff]", message):
        reason = (
            "ADT Model Advisor (опциональный Stop hook): перед завершением "
            "отдельно отметь, что найденные существенные риски могут "
            "заслуживать независимой экспертизы. Без перечисления "
            "неподтверждённых моделей предложи: (1) продолжить текущей "
            "моделью или (2) проверить реальные возможности Codex Desktop "
            "и только затем запросить отдельное разрешение на консультацию. "
            "Если пользователь уже отказался от совета по этой задаче, "
            "не повторяй предложение. Не запускай другие модели, не делай "
            "MCP-делегирование и не меняй техническое заключение."
        )
    else:
        reason = (
            "ADT Model Advisor (optional Stop hook): before finishing, "
            "briefly note that the confirmed material risks may benefit "
            "from independent review. Do not name unverified models; "
            "offer (1) continue on the primary model or (2) check actual "
            "Codex Desktop capabilities and request separate consent before "
            "any consultation. Do not repeat an earlier refusal, invoke "
            "another model, delegate through MCP, or alter the findings."
        )
    # This is a Codex Stop continuation on the *current* model, not a
    # second-model request. It can consume additional subscription quota.
    return {"decision": "block", "reason": reason}


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(MAX_EVENT_BYTES + 1)
        if len(raw) > MAX_EVENT_BYTES:
            output = {}
        else:
            output = check_stop(json.loads(raw.decode("utf-8")))
    except (ValueError, UnicodeError, OSError, TypeError):
        output = {}
    sys.stdout.write(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
