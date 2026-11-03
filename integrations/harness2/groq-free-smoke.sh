#!/usr/bin/env bash
# Explicit, bounded Groq Free acceptance using ORIGINAL pinned Harness2/OpenCode.
set -Eeuo pipefail

readonly UPSTREAM_SHA="1cfe254e8d25b15f37048c3730134686abe60335"
readonly TOOL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly ROOT="$HOME/.local/share/ai-development-toolkit/harness2-$UPSTREAM_SHA"
readonly SRC="$ROOT/source"
readonly BIN="$ROOT/.venv/bin"
readonly OC="$SRC/dependencies/opencode/packages/opencode"
readonly BUN="$SRC/dependencies/tools/node_modules/.bin/bun"
readonly MODEL="groq:openai/gpt-oss-20b"
readonly PROVIDER="h421groq"

fail() { printf 'HARNESS2_GROQ_FREE_REFUSED: %s\n' "$*" >&2; exit 2; }
[[ "$(id -u)" != 0 ]] || fail 'root execution forbidden'
[[ -d "$HOME" && ! -L "$HOME" ]] || fail 'unsafe HOME'
[[ $# -ge 1 ]] || fail 'expected check or smoke'
mode="$1"
shift
case "$mode" in
  check)
    [[ $# == 0 ]] || fail 'check accepts no arguments'
    ;;
  smoke)
    [[ $# == 2 && "$2" == --confirm-groq-free ]] ||
      fail 'smoke requires Windows Python path and --confirm-groq-free'
    readonly WINDOWS_PYTHON="$1"
    [[ "$WINDOWS_PYTHON" == /mnt/* && "$WINDOWS_PYTHON" == *.exe &&
       -x "$WINDOWS_PYTHON" ]] || fail 'an existing Windows Python executable is required'
    command -v wslpath >/dev/null || fail 'wslpath required'
    ;;
  *) fail 'unsupported mode' ;;
esac

bash "$TOOL_DIR/install.sh" status >/dev/null || fail 'pinned Harness2 not installed'
git -C "$SRC" diff --quiet && git -C "$SRC" diff --cached --quiet ||
  fail 'original Harness2 files changed'
[[ -x "$BIN/harness2-check" && -x "$BUN" && -f "$OC/src/index.ts" ]] ||
  fail 'pinned original JobBench/OpenCode runtime not installed'
[[ -d "$SRC/dependencies/job-bench-eval/dataset/main" ]] ||
  fail 'original JobBench dataset not installed'
[[ "$(git -C "$SRC/dependencies/opencode" rev-parse HEAD)" == "23fb5e0516c99ac04a1aa46c193efda2e1b9bb24" ]] ||
  fail 'original OpenCode checkout revision changed'

# The native check validates installation and configuration only. The dummy
# local judge endpoint and dummy key DO NOT run a judge or prove judge readiness.
export HARNESS2_SOLVER_MODEL="$PROVIDER/$MODEL"
export HARNESS2_IMPROVER_MODEL="$HARNESS2_SOLVER_MODEL"
export HARNESS2_JUDGE_MODEL="$MODEL"
export HARNESS2_JUDGE_BASE_URL="http://127.0.0.1:1/v1"
export HARNESS2_JUDGE_API_KEY="h421-readiness-placeholder-not-a-credential"
export HARNESS2_RUNS_DIR="$HOME/.local/share/ai-development-toolkit/h421-free-smoke-runs"

(
  cd -- "$SRC"
  "$BIN/harness2-check" --bench jb
) || fail 'original JobBench preflight failed'

if [[ "$mode" == check ]]; then
  printf 'HARNESS2_GROQ_FREE_CHECK=PASS\nMODEL_EXECUTION=NOT_RUN\n'
  exit 0
fi

command -v python3.12 >/dev/null || fail 'Python 3.12 required in WSL'
command -v timeout >/dev/null || fail 'timeout required for bounded model run'
[[ -f "$TOOL_DIR/groq_free_windows.py" && -f "$TOOL_DIR/groq_free_wsl.py" ]] ||
  fail 'gateway helper scripts missing'
command -v realpath >/dev/null || fail 'realpath required'
readonly WINDOWS_RELAY="$(wslpath -w "$TOOL_DIR/groq_free_windows.py")"
[[ "$WINDOWS_RELAY" == *:/* || "$WINDOWS_RELAY" == *:\\* ]] ||
  fail 'cannot translate the Windows relay source'

# User-only ephemeral key; actual provider and FreeLLMAPI credentials stay in Windows.
export HARNESS2_GROQ_BRIDGE_TOKEN
HARNESS2_GROQ_BRIDGE_TOKEN="$(python3.12 -c 'import secrets; print(secrets.token_urlsafe(32))')"
[[ "${#HARNESS2_GROQ_BRIDGE_TOKEN}" -ge 32 ]] || fail 'token generation failed'

readonly TEMP_ROOT="$HOME/.local/share/ai-development-toolkit"
[[ -d "$TEMP_ROOT" && ! -L "$TEMP_ROOT" ]] || fail 'unsafe user-only storage'
umask 077
run_root="$(mktemp -d "$TEMP_ROOT/h421-groq-free-XXXXXXXX")" || fail 'cannot create isolated workspace'
bridge_pid=""
cleanup() {
  if [[ -n "$bridge_pid" ]]; then
    kill "$bridge_pid" 2>/dev/null || true
    wait "$bridge_pid" 2>/dev/null || true
  fi
  if [[ -n "${run_root:-}" && -d "$run_root" && ! -L "$run_root" &&
        "$run_root" == "$TEMP_ROOT/h421-groq-free-"* ]]; then
    rm -rf -- "$run_root"
  fi
  unset HARNESS2_GROQ_BRIDGE_TOKEN OPENCODE_CONFIG_CONTENT
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

mkdir -m 700 "$run_root/workspace" "$run_root/config" "$run_root/data"
readonly FILE="$run_root/workspace/h421-read-sentinel.txt"
readonly SENTINEL="H421_READ_TOOL_CONFIRMED_47"
printf '%s\n' "$SENTINEL" > "$FILE"
bridge_log="$run_root/bridge-startup.log"
python3.12 -u "$TOOL_DIR/groq_free_wsl.py" "$WINDOWS_PYTHON" "$WINDOWS_RELAY" > "$bridge_log" 2>&1 &
bridge_pid=$!
port=""
for _ in {1..100}; do
  line="$(grep -m 1 '^HARNESS2_GROQ_BRIDGE_READY=[0-9][0-9]*$' "$bridge_log" 2>/dev/null || true)"
  if [[ -n "$line" ]]; then
    port="${line#*=}"
    break
  fi
  kill -0 "$bridge_pid" 2>/dev/null || fail 'local gateway exited during setup'
  sleep 0.1
done
[[ "$port" =~ ^[0-9]{4,5}$ && "$port" -ge 1024 && "$port" -le 65535 ]] ||
  fail 'local gateway readiness timed out'

# Only the one user-authorized free model is shown to OpenCode. All tools except
# read are disabled; all commands execute inside this empty disposable workspace.
export XDG_CONFIG_HOME="$run_root/config"
export XDG_DATA_HOME="$run_root/data"
export OPENCODE_DISABLE_MODELS_FETCH=true
export OPENCODE_DISABLE_AUTOUPDATE=true
export OPENCODE_DISABLE_DEFAULT_PLUGINS=true
export OPENCODE_DISABLE_EXTERNAL_SKILLS=true
export OPENCODE_DISABLE_CLAUDE_CODE=true
export OPENCODE_DISABLE_PROJECT_CONFIG=true
export OPENCODE_DISABLE_LSP_DOWNLOAD=true
export OPENCODE_DISABLE_AUTOCOMPACT=true
export OPENCODE_DISABLE_SHARE=true
export OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX=512
export OPENCODE_PERMISSION='{"external_directory":{"*":"deny"}}'
export OPENCODE_CONFIG_CONTENT
OPENCODE_CONFIG_CONTENT="$(python3.12 - "$port" <<'PY'
import json, os, sys
port = int(sys.argv[1])
config = {
    "$schema": "https://opencode.ai/config.json",
    "autoupdate": False,
    "permission": {"*": "deny", "read": "allow"},
    "provider": {
        "h421groq": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "Groq Free (isolated Harness2 smoke)",
            "options": {
                "baseURL": f"http://127.0.0.1:{port}/v1",
                "apiKey": os.environ["HARNESS2_GROQ_BRIDGE_TOKEN"],
            },
            "models": {
                "groq:openai/gpt-oss-20b": {
                    "name": "Groq Free GPT-OSS 20B",
                    "limit": {"context": 131072, "output": 512},
                }
            },
        }
    },
    "model": "h421groq/groq:openai/gpt-oss-20b",
}
print(json.dumps(config, separators=(",", ":")))
PY
)" || fail 'cannot construct local-only OpenCode configuration'

log="$run_root/opencode.jsonl"
set +e
(
  cd -- "$SRC"
  timeout --kill-after=5s 85s "$BUN" run --cwd "$OC" --conditions=browser \
    src/index.ts --pure run \
    "Use the read tool to read $FILE. Respond only with the exact file content. Do not use any other tool." \
    --dir "$run_root/workspace" --model "$PROVIDER/$MODEL" --format json </dev/null
) > "$log" 2>&1
rc=$?
set -e
[[ "$rc" == 0 ]] || fail "original OpenCode smoke returned $rc"

python3.12 - "$log" "$FILE" "$SENTINEL" <<'PY' || fail 'original OpenCode event acceptance failed'
import json
import sys
from pathlib import Path

log, expected, sentinel = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
events = []
for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue
    if isinstance(event, dict):
        events.append(event)
assert events and not any(e.get("type") == "error" for e in events)
calls = [e["part"] for e in events
         if e.get("type") == "tool_use" and isinstance(e.get("part"), dict)]
assert len(calls) == 1 and calls[0].get("tool") == "read"
state = calls[0].get("state") or {}
assert state.get("status") == "completed"
assert (state.get("input") or {}).get("filePath") == expected
assert sentinel in str(state.get("output", ""))
answers = [(e.get("part") or {}).get("text") for e in events if e.get("type") == "text"]
assert len(answers) == 1 and answers[0].strip() == sentinel
print("HARNESS2_GROQ_FREE_SMOKE=PASS")
print("HARNESS2_GROQ_FREE_TOOL=read")
print("HARNESS2_GROQ_FREE_MODEL=groq:openai/gpt-oss-20b")
print("HARNESS2_GROQ_FREE_UNEXPECTED_TOOLS=0")
print("HARNESS2_GROQ_FREE_ERRORS=0")
print("MODEL_EXECUTION=COMPLETED_FREE_CLOUD_SMOKE")
PY
