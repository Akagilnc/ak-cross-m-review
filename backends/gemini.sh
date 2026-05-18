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

# Gemini CLI exits non-zero on rate-limit (429 MODEL_CAPACITY_EXHAUSTED).
# Capture gemini's OWN exit code (G_RC): a non-zero exit that still
# printed a salvageable JSON-ish error body must degrade, NOT slip
# through as a silent zero-finding approve. 2>&1 (wiki hard rule keeps
# the 429 reason visible). attempt_gemini runs in THIS shell (not a
# command substitution) so RAW + G_RC propagate.
attempt_gemini() {  # sets globals RAW, G_RC
  set +e
  RAW="$(gemini -p "$FULL_PROMPT" --approval-mode auto_edit 2>&1)"
  G_RC=$?
  set -e
}

RAW=""; G_RC=0
attempt_gemini

if [ -z "$RAW" ] || [ "$G_RC" -ne 0 ]; then
  echo "gemini: warn: attempt 1 empty/rc=$G_RC, retrying..." >&2
  sleep "${GEMINI_RETRY_SLEEP:-30}"
  attempt_gemini
fi

if [ -z "$RAW" ]; then
  echo "gemini: degrade — flag '本轮缺 gemini' (empty output after retry, rc=$G_RC)" >&2
  printf '{"reviewer":"gemini","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi

# extract_json takes ONLY the sentinel-wrapped findings (Pass 0); JSON
# echoed from the schema or quoted from the diff is structurally
# ignored. Degrade — visibly, never silent — if EITHER extract_json
# found no contracted findings (EX_RC) OR gemini itself exited non-zero
# (G_RC: a 429 that still printed a salvageable error body). This is the
# FULL codex-review.sh degrade gate. Round-1 ported only the EX_RC half
# (incomplete — a rate-limited gemini slipped through as a clean
# zero-finding approve); the G_RC half is restored here.
set +e
EXTRACTED="$(printf '%s' "$RAW" | python3 "$PROTO_ROOT/lib/extract_json.py" gemini "$MODE")"
EX_RC=$?
set -e
if [ "$EX_RC" -ne 0 ] || [ "$G_RC" -ne 0 ]; then
  echo "gemini: degrade — flag '本轮缺 gemini' (extract_json rc=$EX_RC, gemini exit rc=$G_RC; gemini's error is in the captured output per 2>&1)" >&2
  printf '{"reviewer":"gemini","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi
printf '%s\n' "$EXTRACTED"
