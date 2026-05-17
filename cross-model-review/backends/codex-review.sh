#!/usr/bin/env bash
# Codex reviewer backend for /cross-model-review.
#
# This is the DELIVERATELY-CORRECT codex invocation. It exists because the
# grounded-review prototype's backends/codex.sh uses the two patterns the
# wiki marks confidence-10 footguns (D1/D2 in the analysis):
#
#   ❌ codex exec "$PROMPT" -C "$WORKDIR" -s read-only
#      - positional-arg prompt (stdin-pipe hang risk; off-convention)
#      - `-C` flag → runs in the wrong workdir (codex-wrong-repo-cwd)
#      - no `--model` → review quality drifts to the CLI default
#
#   ✅ cat <<'PROMPT' | codex exec --model gpt-5.5 - 2>&1
#      - stdin pipe (the `-` means "read prompt from stdin")
#      - `--model gpt-5.5` pinned: review-tier, never dev-tier spark/5.3
#      - NO `-C`: codex runs from the current dir (the repo root)
#      - always 2>&1 so failures are visible
#
# Source of truth:
#   wiki/concepts/cross-model-review.md  §调用规范 / §额外硬规则
#   wiki/concepts/codex-bot-conventions.md  §CLI 侧的正确 pattern / §模型变体
#
# Invocation:
#   <stdin: full review prompt incl. diff> | codex-review.sh <mode> [<label>]
#     mode  : doc | code   (passed to extract_json.py)
#     label : optional diagnostic tag (e.g. "section-2of3")
#
#   CMR_CODEX_MODEL   override review model (default: gpt-5.5)
#   CMR_CODEX_TIMEOUT hard wall-clock seconds before pkill (default: 600)
#   CMR_DRY_RUN=1     print the exact command that WOULD run, do not call
#                     codex, exit 0. Used by --selftest.
#
# Outputs reviewer JSON (reviewer=codex) to stdout. Diagnostics to stderr.
# On timeout / empty output: synthetic empty-findings JSON + exit 1 so the
# orchestrator degrades and flags "本轮缺 codex" instead of silently passing.

set -euo pipefail

# Resolve the shared proto lib (this script lives at
# cross-model-review/backends/, lib/ is two levels up).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROTO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EXTRACT="$PROTO_ROOT/lib/extract_json.py"

MODE="${1:-code}"
LABEL="${2:-full}"
MODEL="${CMR_CODEX_MODEL:-gpt-5.5}"
TIMEOUT_S="${CMR_CODEX_TIMEOUT:-600}"

# --selftest: build the command, assert it is on-convention, never call
# codex. This is the regression guard for D1/D2.
if [ "${1:-}" = "--selftest" ]; then
  CMD="codex exec --model ${MODEL} - 2>&1"
  fail=0
  case "$CMD" in
    *" -C "*) echo "FAIL: command contains -C (wrong-workdir footgun)" >&2; fail=1 ;;
  esac
  case "$CMD" in
    *"--model "*) ;;
    *) echo "FAIL: command missing --model pin" >&2; fail=1 ;;
  esac
  case "$CMD" in
    *"codex exec --model ${MODEL} -"*) ;;
    *) echo "FAIL: command not stdin-pipe form ('codex exec --model X -')" >&2; fail=1 ;;
  esac
  case "$CMD" in
    *"2>&1"*) ;;
    *) echo "FAIL: command missing 2>&1" >&2; fail=1 ;;
  esac
  # Positional-arg form must never appear.
  case "$CMD" in
    *'codex exec "'*) echo "FAIL: positional-arg prompt form present" >&2; fail=1 ;;
  esac
  if [ "$fail" -eq 0 ]; then
    echo "✓ codex-review.sh invocation is on-convention: ${CMD}"
    exit 0
  fi
  exit 1
fi

FULL_PROMPT="$(cat)"
if [ -z "$FULL_PROMPT" ]; then
  echo "codex-review: error: empty prompt on stdin" >&2
  exit 1
fi

if [ "${CMR_DRY_RUN:-0}" = "1" ]; then
  echo "DRY_RUN cmd: printf %s \"\$PROMPT\" | codex exec --model ${MODEL} - 2>&1" >&2
  printf '{"reviewer":"codex","mode":"%s","findings":[]}\n' "$MODE"
  exit 0
fi

echo "codex-review: model=${MODEL} mode=${MODE} label=${LABEL} timeout=${TIMEOUT_S}s" >&2

# Portable hard timeout. The prompt ALWAYS reaches codex via a temp file
# fed to `codex exec --model "$MODEL" -` (the `-` = read stdin). An
# earlier version fed $FULL_PROMPT as a here-string into a `bash -c`
# that read it as an out-of-scope variable → empty prompt whenever GNU
# timeout/gtimeout was present (the default on homebrew macOS), so codex
# silently never ran. Fixed: one stdin path for every branch, real
# timeout (rc 124/137/143) treated as degrade, and the no-coreutils
# fallback kills only THIS codex + its children (never a global
# `pkill -f 'codex exec'`, which would take down sibling parallel codex
# reviewers and unrelated user codex runs).
PROMPT_TMP="$(mktemp)"
trap 'rm -f "$PROMPT_TMP"' EXIT
printf '%s' "$FULL_PROMPT" > "$PROMPT_TMP"

RAW=""
RC=0
if command -v timeout >/dev/null 2>&1; then
  set +e
  RAW="$(timeout "${TIMEOUT_S}s" codex exec --model "$MODEL" - < "$PROMPT_TMP" 2>&1)"
  RC=$?
  set -e
elif command -v gtimeout >/dev/null 2>&1; then
  set +e
  RAW="$(gtimeout "${TIMEOUT_S}s" codex exec --model "$MODEL" - < "$PROMPT_TMP" 2>&1)"
  RC=$?
  set -e
else
  # No coreutils timeout: background codex, scoped-kill on timeout.
  TMP_OUT="$(mktemp)"
  codex exec --model "$MODEL" - < "$PROMPT_TMP" >"$TMP_OUT" 2>&1 &
  CODEX_PID=$!
  ( sleep "$TIMEOUT_S"
    if kill -0 "$CODEX_PID" 2>/dev/null; then
      echo "codex-review: timeout ${TIMEOUT_S}s — killing pid $CODEX_PID + children (scoped, not global)" >&2
      pkill -TERM -P "$CODEX_PID" 2>/dev/null || true
      kill -TERM "$CODEX_PID" 2>/dev/null || true
    fi ) &
  WATCH_PID=$!
  set +e
  wait "$CODEX_PID"
  RC=$?
  set -e
  kill "$WATCH_PID" 2>/dev/null || true
  RAW="$(cat "$TMP_OUT" 2>/dev/null || true)"
  rm -f "$TMP_OUT"
fi

# rc 124 = timeout(1) killed it; 137/143 = SIGKILL/SIGTERM (our kill).
# A truncated-but-brace-balanced fragment must NOT parse as real
# findings — any timeout/kill is a degrade regardless of partial stdout.
case "$RC" in
  124|137|143) RAW="" ;;
esac

if [ -z "$RAW" ]; then
  echo "codex-review: error: empty output / timeout (rc=$RC) — degrade, flag '本轮缺 codex'" >&2
  printf '{"reviewer":"codex","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi

printf '%s' "$RAW" | python3 "$EXTRACT" codex "$MODE"
