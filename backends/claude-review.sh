#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-code}"
case "$MODE" in
  code|doc) ;;
  *)
    echo "claude-review: invalid MODE (expected code|doc) — degrade, flag '本轮缺 claude'" >&2
    exit 1
    ;;
esac

MODEL="${CMR_CLAUDE_MODEL:-claude-opus-4-8}"
EFFORT="${CMR_CLAUDE_EFFORT:-high}"
OUTPUT_FILE="$(mktemp)"
ERROR_FILE="$(mktemp)"
trap 'rm -f "$OUTPUT_FILE" "$ERROR_FILE"' EXIT

set +e
claude -p \
  --model "$MODEL" \
  --effort "$EFFORT" \
  --output-format text \
  --no-session-persistence \
  > "$OUTPUT_FILE" 2> "$ERROR_FILE"
CLAUDE_RC=$?
set -e

if [ -s "$ERROR_FILE" ]; then
  cat "$ERROR_FILE" >&2
fi
if [ "$CLAUDE_RC" -ne 0 ]; then
  echo "claude-review: degrade — flag '本轮缺 claude' (claude exit rc=$CLAUDE_RC)" >&2
  exit 1
fi
if [ ! -s "$OUTPUT_FILE" ]; then
  echo "claude-review: degrade — flag '本轮缺 claude' (empty output, claude rc=0)" >&2
  exit 1
fi

cat "$OUTPUT_FILE"
