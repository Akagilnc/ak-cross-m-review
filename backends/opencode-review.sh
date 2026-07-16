#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-code}"
case "$MODE" in
  code|doc) ;;
  *)
    echo "opencode-review: invalid MODE (expected code|doc) — degrade, flag '本轮缺 opencode'" >&2
    exit 1
    ;;
esac

MODEL="${CMR_OPENCODE_MODEL:-opencode-go/glm-5.2}"
VARIANT_FLAG=()
[ -n "${CMR_OPENCODE_VARIANT:-}" ] \
  && VARIANT_FLAG=(--variant "$CMR_OPENCODE_VARIANT")
REVIEW_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PROMPT_FILE="$(mktemp)"
OUTPUT_FILE="$(mktemp)"
ERROR_FILE="$(mktemp)"
trap 'rm -f "$PROMPT_FILE" "$OUTPUT_FILE" "$ERROR_FILE"' EXIT

cat > "$PROMPT_FILE"

cd "$REVIEW_ROOT"
set +e
opencode run \
  --pure \
  --format default \
  --model "$MODEL" \
  "${VARIANT_FLAG[@]+"${VARIANT_FLAG[@]}"}" \
  --file "$PROMPT_FILE" \
  --dir "$REVIEW_ROOT" \
  "Review the attached packet and return only the grounded prose review." \
  > "$OUTPUT_FILE" 2> "$ERROR_FILE"
OPENCODE_RC=$?
set -e

if [ -s "$ERROR_FILE" ]; then
  cat "$ERROR_FILE" >&2
fi
if [ "$OPENCODE_RC" -ne 0 ]; then
  echo "opencode-review: degrade — flag '本轮缺 opencode' (opencode exit rc=$OPENCODE_RC)" >&2
  exit 1
fi
if [ ! -s "$OUTPUT_FILE" ]; then
  echo "opencode-review: degrade — flag '本轮缺 opencode' (empty output, opencode rc=0)" >&2
  exit 1
fi

cat "$OUTPUT_FILE"
