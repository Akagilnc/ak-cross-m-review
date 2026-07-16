#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-code}"
case "$MODE" in
  code|doc) ;;
  *)
    echo "grok-review: invalid MODE (expected code|doc) — degrade, flag '本轮缺 grok'" >&2
    exit 1
    ;;
esac

MODEL="${CMR_GROK_MODEL:-grok-4.5}"
EFFORT="${CMR_GROK_EFFORT:-high}"
PROMPT_FILE="$(mktemp)"
OUTPUT_FILE="$(mktemp)"
ERROR_FILE="$(mktemp)"
trap 'rm -f "$PROMPT_FILE" "$OUTPUT_FILE" "$ERROR_FILE"' EXIT

cat > "$PROMPT_FILE"

set +e
RUST_LOG=off grok --no-memory --no-subagents \
  --prompt-file "$PROMPT_FILE" \
  --model "$MODEL" \
  --reasoning-effort "$EFFORT" \
  --output-format plain \
  > "$OUTPUT_FILE" 2> "$ERROR_FILE"
GROK_RC=$?
set -e

if [ -s "$ERROR_FILE" ]; then
  cat "$ERROR_FILE" >&2
fi
if [ "$GROK_RC" -ne 0 ]; then
  if [ -s "$OUTPUT_FILE" ]; then
    cat "$OUTPUT_FILE" >&2
  fi
  echo "grok-review: degrade — flag '本轮缺 grok' (grok exit rc=$GROK_RC)" >&2
  exit 1
fi
if [ ! -s "$OUTPUT_FILE" ]; then
  echo "grok-review: degrade — flag '本轮缺 grok' (empty output, grok rc=0)" >&2
  exit 1
fi

cat "$OUTPUT_FILE"
