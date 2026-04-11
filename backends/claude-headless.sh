#!/usr/bin/env bash
# Claude Opus headless reviewer backend.
#
# Invocation:
#   <stdin: full dispatch prompt including task prompt + target content + any
#           source-repo hint> | backends/claude-headless.sh <mode>
#
# Outputs JSON (reviewer payload) to stdout. Diagnostics to stderr.
#
# Uses `claude -p --model opus --output-format json` so each invocation
# creates a fresh Claude Code session with zero context contamination from
# the calling session. Tools available are explicitly enumerated to control
# what the reviewer can use.

set -euo pipefail

PROTO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-doc}"

# Collect full prompt from stdin
FULL_PROMPT="$(cat)"

if [ -z "$FULL_PROMPT" ]; then
  echo "claude-headless: error: empty prompt on stdin" >&2
  exit 1
fi

# Claude Code headless with Opus and the toolset needed for grounded review.
# WebFetch allows first-party doc verification (npmjs, MDN, GitHub README).
# Bash allows spawning python3 with scipy for math verification.
RAW="$(
  printf '%s' "$FULL_PROMPT" | claude \
    -p \
    --model opus \
    --output-format json \
    --tools "Read,Grep,Glob,Bash,WebFetch" \
    2>/dev/null || true
)"

if [ -z "$RAW" ]; then
  echo "claude-headless: error: claude CLI returned empty output" >&2
  # Emit empty findings so the merge step still proceeds
  printf '{"reviewer":"claude","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi

# Claude Code headless JSON wrapper shape (observed 2026-04-11):
#   {"type":"result","subtype":"success","is_error":false,"result":"<inner>",...}
# The inner .result field is a string containing the model's textual output,
# which we hope is our requested JSON.
INNER="$(printf '%s' "$RAW" | jq -r '.result // empty' 2>/dev/null || true)"

if [ -z "$INNER" ]; then
  # Wrapper parse failed. Fall through with raw output — extract_json.py
  # will do its best.
  echo "claude-headless: warn: could not extract .result field, passing raw" >&2
  printf '%s' "$RAW" | python3 "$PROTO_ROOT/lib/extract_json.py" claude "$MODE"
else
  printf '%s' "$INNER" | python3 "$PROTO_ROOT/lib/extract_json.py" claude "$MODE"
fi
