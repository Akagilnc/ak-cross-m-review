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
OUTPUT_FILE="$(mktemp)"
ERROR_FILE="$(mktemp)"
REVIEW_FILE="$(mktemp)"
trap 'rm -f "$OUTPUT_FILE" "$ERROR_FILE" "$REVIEW_FILE"' EXIT

if ! command -v jq >/dev/null 2>&1; then
  echo "claude-review: degrade — flag '本轮缺 claude' (jq unavailable for Claude event stream)" >&2
  exit 1
fi

set +e
claude -p \
  --model "$MODEL" \
  --permission-mode acceptEdits \
  --allowedTools Bash \
  --output-format stream-json \
  --verbose \
  --include-partial-messages \
  --no-session-persistence \
  > "$OUTPUT_FILE" 2> "$ERROR_FILE"
CLAUDE_RC=$?
set -e

if [ -s "$ERROR_FILE" ]; then
  cat "$ERROR_FILE" >&2
fi
if [ "$CLAUDE_RC" -ne 0 ]; then
  if [ -s "$OUTPUT_FILE" ]; then
    cat "$OUTPUT_FILE" >&2
  fi
  echo "claude-review: degrade — flag '本轮缺 claude' (claude exit rc=$CLAUDE_RC)" >&2
  exit 1
fi
if [ ! -s "$OUTPUT_FILE" ]; then
  echo "claude-review: degrade — flag '本轮缺 claude' (empty output, claude rc=0)" >&2
  exit 1
fi

set +e
jq -s -r -j '
  [ .[] | select(.type == "result") ] as $results
  | if ($results | length) != 1 then
      error("expected exactly one result event")
    elif .[-1].type != "result" then
      error("result event is not terminal")
    elif .[-1].subtype != "success" or (.[-1].is_error // false) then
      error("terminal result reports failure")
    else
      [
        .[]
        | select(
            .type == "stream_event"
            and .event.delta.type? == "text_delta"
          )
        | .event.delta.text
      ] as $text
      | if ($text | length) == 0 then
          error("no text deltas")
        else
          $text[]
        end
    end
' "$OUTPUT_FILE" > "$REVIEW_FILE" 2>> "$ERROR_FILE"
PARSE_RC=$?
set -e

if [ "$PARSE_RC" -ne 0 ]; then
  cat "$OUTPUT_FILE" >&2
  cat "$ERROR_FILE" >&2
  echo "claude-review: degrade — flag '本轮缺 claude' (invalid Claude event stream)" >&2
  exit 1
fi
if [ ! -s "$REVIEW_FILE" ]; then
  echo "claude-review: degrade — flag '本轮缺 claude' (empty streamed review)" >&2
  exit 1
fi

cat "$REVIEW_FILE"
