#!/usr/bin/env bash
# Google Gemini reviewer backend.
#
# Invocation:
#   <stdin: full dispatch prompt including task prompt + target content + any
#           source-repo hint> | backends/gemini.sh <mode>
#
# Outputs JSON (reviewer payload) to stdout. Diagnostics to stderr.
#
# Uses `gemini -p --approval-mode plan`. plan mode is the gemini-cli
# equivalent of read-only — it analyzes but does not execute anything that
# would modify state. This is critical for running gemini in parallel with
# other reviewers on the same source tree without risk of concurrent writes.

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
  gemini -p "$FULL_PROMPT" --approval-mode plan 2>/dev/null || true
}

RAW="$(attempt_gemini)"

if [ -z "$RAW" ]; then
  echo "gemini: warn: first attempt empty, retrying after 30s..." >&2
  sleep 30
  RAW="$(attempt_gemini)"
fi

if [ -z "$RAW" ]; then
  echo "gemini: error: gemini CLI returned empty output after retry" >&2
  printf '{"reviewer":"gemini","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi

printf '%s' "$RAW" | python3 "$PROTO_ROOT/lib/extract_json.py" gemini "$MODE"
