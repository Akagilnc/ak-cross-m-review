#!/usr/bin/env bash
# Google Gemini reviewer backend.
#
# Invocation:
#   <stdin: full reviewer prompt incl. the diff to review>
#           | backends/gemini.sh <mode>
#
# Outputs JSON (reviewer payload) to stdout. Diagnostics to stderr.
#
# Uses `gemini -p --approval-mode auto_edit`. auto_edit lets gemini read
# files and grep the codebase (needed for grounded verification), while
# auto-approving edit tools. The reviewer prompt does not instruct writes,
# so in practice gemini only reads.

set -euo pipefail

PROTO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-doc}"

FULL_PROMPT="$(cat)"

if [ -z "$FULL_PROMPT" ]; then
  echo "gemini: error: empty prompt on stdin" >&2
  exit 1
fi

# Gemini CLI exits non-zero on rate-limit (429 MODEL_CAPACITY_EXHAUSTED)
# which we observed in session 7. Retry once with a short delay if the first
# attempt returns empty or errors.
attempt_gemini() {
  # 2>&1 (wiki hard rule "始终 2>&1：出错要看到原因"): gemini's own
  # diagnostics/429 reason must NOT be silenced — extract_json salvages
  # the findings JSON from the combined noise, same model as
  # codex-review.sh. 2>/dev/null here made a degraded round undiagnosable.
  gemini -p "$FULL_PROMPT" --approval-mode auto_edit 2>&1 || true
}

RAW="$(attempt_gemini)"

if [ -z "$RAW" ]; then
  echo "gemini: warn: first attempt empty, retrying after 30s..." >&2
  sleep 30
  RAW="$(attempt_gemini)"
fi

if [ -z "$RAW" ]; then
  echo "gemini: degrade — flag '本轮缺 gemini' (empty output after retry)" >&2
  printf '{"reviewer":"gemini","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi

# RAW carries gemini's diagnostics mixed with the findings JSON (2>&1);
# extract_json salvages the JSON. If it can't (gemini emitted an
# error/banner, not a review — e.g. 429), degrade with the visible flag,
# never silent. Mirrors codex-review.sh's degrade discipline.
set +e
EXTRACTED="$(printf '%s' "$RAW" | python3 "$PROTO_ROOT/lib/extract_json.py" gemini "$MODE")"
EX_RC=$?
set -e
if [ "$EX_RC" -ne 0 ]; then
  echo "gemini: degrade — flag '本轮缺 gemini' (no valid review JSON; gemini's error is in the captured output per 2>&1, extract_json rc=$EX_RC)" >&2
  printf '{"reviewer":"gemini","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi
printf '%s\n' "$EXTRACTED"
