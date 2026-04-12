#!/usr/bin/env bash
# Claude headless reviewer / fixer backend.
#
# Invocation:
#   <stdin: full prompt> | backends/claude-headless.sh <mode> [<role>]
#
#   mode:  doc | code
#   role:  reviewer (default) | fixer
#
# Model selection:
#   reviewer → opus   (needs deep reasoning + judgment for fact-checking)
#   fixer    → sonnet (structured text transform; safety-netted by git
#                      apply --check + user approval + round 2 reviewer)
#
# Override: set GROUNDED_REVIEW_FIXER_MODEL=opus to force opus for fixer
# (use on high-risk docs where round 2 verification is skipped).
#
# Outputs JSON to stdout. Diagnostics to stderr.

set -euo pipefail

PROTO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-doc}"
ROLE="${2:-reviewer}"

# Model selection based on role
if [ "$ROLE" = "fixer" ]; then
  MODEL="${GROUNDED_REVIEW_FIXER_MODEL:-sonnet}"
else
  MODEL="opus"
fi

echo "claude-headless: role=$ROLE model=$MODEL mode=$MODE" >&2

# Collect full prompt from stdin
FULL_PROMPT="$(cat)"

if [ -z "$FULL_PROMPT" ]; then
  echo "claude-headless: error: empty prompt on stdin" >&2
  exit 1
fi

# Claude Code headless session. Tools available:
#   reviewer: Read,Grep,Glob,Bash,WebFetch (needs to grep source + compute math)
#   fixer:    Read,Grep (verify claim_quote + grep for related occurrences)
if [ "$ROLE" = "fixer" ]; then
  TOOLS="Read,Grep"
else
  TOOLS="Read,Grep,Glob,Bash,WebFetch"
fi

START_S=$(date +%s)

RAW="$(
  printf '%s' "$FULL_PROMPT" | claude \
    -p \
    --model "$MODEL" \
    --output-format json \
    --tools "$TOOLS" \
    2>/dev/null || true
)"

END_S=$(date +%s)
ELAPSED=$((END_S - START_S))
echo "claude-headless: completed in ${ELAPSED}s (role=$ROLE model=$MODEL)" >&2

if [ -z "$RAW" ]; then
  echo "claude-headless: error: claude CLI returned empty output" >&2
  printf '{"reviewer":"claude","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi

# Claude Code headless JSON wrapper shape:
#   {"type":"result","subtype":"success","result":"<inner>",...}
INNER="$(printf '%s' "$RAW" | jq -r '.result // empty' 2>/dev/null || true)"

if [ -z "$INNER" ]; then
  echo "claude-headless: warn: could not extract .result field, passing raw" >&2
  printf '%s' "$RAW" | python3 "$PROTO_ROOT/lib/extract_json.py" claude "$MODE"
else
  printf '%s' "$INNER" | python3 "$PROTO_ROOT/lib/extract_json.py" claude "$MODE"
fi
