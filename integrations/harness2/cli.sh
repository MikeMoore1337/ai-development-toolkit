#!/usr/bin/env bash
# Explicit, non-model calls into ORIGINAL pinned Harness2 CLI. No new runner.
set -Eeuo pipefail

readonly UPSTREAM_SHA="1cfe254e8d25b15f37048c3730134686abe60335"
readonly TOOL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly ROOT="$HOME/.local/share/ai-development-toolkit/harness2-$UPSTREAM_SHA"
readonly SRC="$ROOT/source"
readonly BIN="$ROOT/.venv/bin"

fail() { printf 'HARNESS2_REFUSED: %s\n' "$*" >&2; exit 2; }
usage() {
  cat <<'HELP'
Usage:
  bash integrations/harness2/cli.sh status
  bash integrations/harness2/cli.sh setup-preview lab|jb|wb [office|web|code]
  bash integrations/harness2/cli.sh setup lab|jb|wb --confirm-network-downloads
  bash integrations/harness2/cli.sh check lab|jb|wb [office|web|code]
  bash integrations/harness2/cli.sh run-preview lab|jb|wb [office|web|code]
  bash integrations/harness2/cli.sh report lab|jb|wb [office|web|code]
  bash integrations/harness2/cli.sh artifacts

Only original upstream executable files are called. This script NEVER starts
model-backed runs, judges, Codex CLI, Claude CLI, or a second optimization engine.
The setup command downloads upstream dependencies and benchmark data only after
an explicit --confirm-network-downloads; inspect third-party licenses first.
HELP
}

[[ $# -ge 1 ]] || { usage; exit 2; }
case "$1" in -h|--help|help) [[ $# == 1 ]] || fail 'unexpected arguments'; usage; exit 0 ;; esac
[[ "$(uname -s)" == Linux ]] || fail 'Linux or Ubuntu/WSL2 required'
[[ -n "${HOME:-}" && -d "$HOME" && ! -L "$HOME" ]] || fail 'unsafe HOME'
bash "$TOOL_DIR/install.sh" status >/dev/null || fail 'pinned upstream not installed'
[[ -d "$SRC" && ! -L "$SRC" && -d "$ROOT/.venv" && ! -L "$ROOT/.venv" ]] || fail 'unsafe installation'
git -C "$SRC" diff --quiet || fail 'tracked upstream changes present'
git -C "$SRC" diff --cached --quiet || fail 'staged upstream changes present'
for exe in harness2-setup harness2-check harness2 harness2-judge harness2-report; do
  [[ -x "$BIN/$exe" && ! -L "$BIN/$exe" ]] || fail "missing native executable: $exe"
done
cd -- "$SRC"

action="$1"
shift
case "$action" in
  status)
    [[ $# == 0 ]] || fail 'status takes no parameters'
    printf 'HARNESS2_CLI=READY\nUPSTREAM_SHA=%s\nMODEL_EXECUTION=DISABLED\n' "$UPSTREAM_SHA"
    ;;
  artifacts)
    [[ $# == 0 ]] || fail 'artifacts takes no parameters'
    # Use the upstream's actual configured runs root, including HARNESS2_RUNS_DIR.
    # Never read model logs, credentials or raw outputs; enumerate report filenames.
    runs_root="$("$BIN/python" -c 'from harness2 import config; print(config.RUNS)')"
    [[ "$runs_root" == "$HOME/"* ]] || fail 'upstream runs root must be inside user home'
    [[ "$runs_root" != "$HOME" && "$runs_root" != "$SRC" ]] || fail 'unsafe runs root'
    if [[ -n "${HARNESS2_RUNS_DIR:-}" && -L "$HARNESS2_RUNS_DIR" ]]; then
      fail 'linked custom runs root'
    fi
    [[ ! -L "$runs_root" ]] || fail 'linked upstream runs root'
    printf 'HARNESS2_RUNS_ROOT=%s\n' "$runs_root"
    [[ -d "$runs_root" ]] || { printf 'HARNESS2_ARTIFACTS=NOT_PRESENT\n'; exit 0; }
    # Only report filenames. Do not traverse symlinks to private files.
    find -P "$runs_root" -type f -name 'judged.json' -print | sort
    ;;
  setup)
    [[ $# == 2 && "$2" == --confirm-network-downloads ]] || fail 'setup requires BENCH --confirm-network-downloads'
    case "$1" in lab|jb|wb) ;; *) fail 'unsupported upstream benchmark' ;; esac
    command -v uv >/dev/null || fail 'uv missing'
    command -v npm >/dev/null || fail 'npm missing'
    # The native setup installs benchmark dependencies, not a model.
    exec "$BIN/harness2-setup" "$1"
    ;;
  setup-preview|check|run-preview|report)
    [[ $# -ge 1 && $# -le 2 ]] || fail 'expected BENCH [WB subset]'
    bench="$1"
    case "$bench" in lab|jb|wb) ;; *) fail 'unsupported upstream benchmark' ;; esac
    flags=(--bench "$bench")
    setupflags=()
    if [[ $# == 2 ]]; then
      [[ "$bench" == wb ]] || fail 'subset is available only for wb'
      case "$2" in office|web|code) ;; *) fail 'invalid wb subset' ;; esac
      flags+=(--subset "$2")
      setupflags+=(--subset "$2")
    fi
    case "$action" in
      setup-preview) exec "$BIN/harness2-setup" "$bench" "${setupflags[@]}" --dry-run ;;
      check) exec "$BIN/harness2-check" "${flags[@]}" ;;
      run-preview) exec "$BIN/harness2" "${flags[@]}" --k 1 --mode parallel --max-tasks 1 --dry-run ;;
      report) exec "$BIN/harness2-report" "${flags[@]}" --k 1 --mode parallel ;;
    esac
    ;;
  *) fail "unknown action: $action" ;;
esac
