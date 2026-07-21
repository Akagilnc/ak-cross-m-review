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

# #1091 — container/CI hardening for grok panel legs (reproduced in
# ming-orchestrator-coder:latest with auth.json mounted):
# Baseline (`--prompt-file` only): exit 0 + empty/opening-line stdout, no tools.
# Hardened: agent tool-loop runs (e.g. bash echo PANEL_LEG_OK succeeds).
# - --no-auto-update: skip background updater (docs.x.ai headless / Docker)
# - ensure HOME + ~/.grok/sessions exist and are writable
# - --always-approve + --permission-mode bypassPermissions: allow the agent
#   tool-loop without interactive permission stalls (the load-bearing fix)
GROK_HOME="${HOME:-/home/agent}"
if ! mkdir -p "${GROK_HOME}/.grok/sessions" 2>/dev/null \
  || [ ! -d "${GROK_HOME}/.grok/sessions" ] \
  || [ ! -w "${GROK_HOME}/.grok/sessions" ]; then
  echo "grok-review: degrade — flag '本轮缺 grok' (session dir unusable: ${GROK_HOME}/.grok/sessions)" >&2
  exit 1
fi

set +e
RUST_LOG=off grok \
  --no-auto-update \
  --no-memory \
  --no-subagents \
  --always-approve \
  --permission-mode bypassPermissions \
  --model "$MODEL" \
  --reasoning-effort "$EFFORT" \
  --output-format plain \
  --prompt-file "$PROMPT_FILE" \
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
