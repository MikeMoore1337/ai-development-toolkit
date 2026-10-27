#!/usr/bin/env bash
# Optional source-only installation of the ORIGINAL google-research/harness2.
# This script never runs model-backed benchmarks, Codex CLI or Claude CLI.
set -Eeuo pipefail

readonly UPSTREAM_URL="https://github.com/google-research/harness2.git"
readonly UPSTREAM_SHA="1cfe254e8d25b15f37048c3730134686abe60335"
readonly UPSTREAM_VERSION="0.1.0"

die() { printf 'harness2: %s\n' "$*" >&2; exit 2; }

usage() {
  cat <<'EOF'
Usage: bash install.sh install|status|remove [--confirm]
Install the pinned, unmodified Harness2 upstream in the current Linux user's home.
Requires Linux, Python 3.12, Git and access to public PyPI/GitHub.
This installer never invokes model providers, Codex CLI, or Claude CLI.
Model-backed upstream benchmark execution is a separate opt-in outside this script.
EOF
}

[[ "${EUID:-$(id -u)}" -ne 0 ]] || die "refusing to run as root"
[[ -n "${HOME:-}" && -d "$HOME" && ! -L "$HOME" ]] || die "unsafe HOME"
readonly BASE="$HOME/.local/share/ai-development-toolkit"
readonly DEST="$BASE/harness2-$UPSTREAM_SHA"
readonly MARKER="$DEST/.adt-original-harness2"

check_installed() {
  [[ -d "$DEST" && ! -L "$DEST" && -d "$DEST/source" && ! -L "$DEST/source" ]] || die "not installed or unsafe checkout"
  [[ -f "$MARKER" && ! -L "$MARKER" ]] || die "missing install marker"
  [[ "$(cat "$MARKER")" == "$UPSTREAM_SHA" ]] || die "marker differs from pinned SHA"
  command -v git >/dev/null 2>&1 || die "git is required"
  [[ "$(git -C "$DEST/source" rev-parse HEAD 2>/dev/null)" == "$UPSTREAM_SHA" ]] || die "checkout is not pinned"
  [[ "$(git -C "$DEST/source" remote get-url origin 2>/dev/null)" == "$UPSTREAM_URL" ]] || die "unexpected origin"
  [[ -x "$DEST/.venv/bin/python" && -x "$DEST/.venv/bin/harness2-check" ]] || die "upstream installation incomplete"
  "$DEST/.venv/bin/python" -c 'import importlib.metadata; assert importlib.metadata.version("harness2") == "0.1.0"' || die "upstream package version mismatch"
  printf 'HARNESS2_STATUS=INSTALLED\nUPSTREAM_SHA=%s\nSOURCE=%s\n' "$UPSTREAM_SHA" "$DEST/source"
}

[[ $# -ge 1 ]] || { usage; exit 2; }
case "$1" in
  -h|--help|help)
    [[ $# -eq 1 ]] || die "unexpected arguments"
    usage
    ;;
  status)
    [[ $# -eq 1 ]] || die "unexpected arguments"
    check_installed
    ;;
  install)
    [[ $# -eq 1 ]] || die "unexpected arguments"
    [[ "$(uname -s)" == Linux ]] || die "use Linux or Ubuntu on WSL2"
    command -v git >/dev/null 2>&1 || die "git is required"
    command -v python3.12 >/dev/null 2>&1 || die "python3.12 is required"
    python3.12 -c 'import sys; assert sys.version_info[:2] == (3, 12)' || die "Python 3.12 required"
    if [[ -e "$DEST" || -L "$DEST" ]]; then
      check_installed
      printf 'HARNESS2_INSTALL=ALREADY_PRESENT\n'
      exit 0
    fi
    mkdir -p -- "$BASE"
    [[ -d "$BASE" && ! -L "$BASE" ]] || die "unsafe installation parent"
    mkdir -- "$DEST"
    # No submodules, no fork, no patched source. Pin a full Git commit.
    git clone --no-checkout -- "$UPSTREAM_URL" "$DEST/source"
    git -C "$DEST/source" checkout --detach "$UPSTREAM_SHA"
    [[ "$(git -C "$DEST/source" rev-parse HEAD)" == "$UPSTREAM_SHA" ]] || die "upstream SHA mismatch"
    python3.12 -m venv "$DEST/.venv"
    "$DEST/.venv/bin/python" -m pip install --disable-pip-version-check -e "$DEST/source[render]"
    printf '%s\n' "$UPSTREAM_SHA" > "$MARKER"
    check_installed
    printf 'HARNESS2_INSTALL=COMPLETE\n'
    ;;
  remove)
    [[ $# -eq 2 && "$2" == --confirm ]] || die "explicit remove --confirm required"
    check_installed
    [[ "$DEST" == "$HOME/.local/share/ai-development-toolkit/harness2-$UPSTREAM_SHA" ]] || die "unsafe removal target"
    rm -rf -- "$DEST"
    printf 'HARNESS2_REMOVE=COMPLETE\n'
    ;;
  *)
    die "unknown command (see --help)"
    ;;
esac
