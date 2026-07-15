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

FULL_PROMPT="$(cat)"
GROK_PROMPT="REVIEW ONLY — HARD CONSTRAINT. Do NOT modify, create, rename, or delete any file in the reviewed repo, and do NOT fix findings yourself. You MAY run read-only inspection and verification commands. Your ONLY output is your grounded prose review.

$FULL_PROMPT"
printf '%s' "$GROK_PROMPT" > "$PROMPT_FILE"

set +e
grok --no-memory --no-subagents \
  --prompt-file "$PROMPT_FILE" \
  --model "$MODEL" \
  --reasoning-effort "$EFFORT" \
  > "$OUTPUT_FILE" 2> "$ERROR_FILE"
GROK_RC=$?
set -e

if [ -s "$ERROR_FILE" ]; then
  cat "$ERROR_FILE" >&2
fi
if [ "$GROK_RC" -ne 0 ]; then
  echo "grok-review: degrade — flag '本轮缺 grok' (grok exit rc=$GROK_RC)" >&2
  exit 1
fi
if [ ! -s "$OUTPUT_FILE" ]; then
  echo "grok-review: degrade — flag '本轮缺 grok' (empty output, grok rc=0)" >&2
  exit 1
fi

cat "$OUTPUT_FILE"
