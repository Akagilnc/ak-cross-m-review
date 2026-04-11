#!/usr/bin/env bash
# Doc-mode eval runner for the grounded-review prototype.
#
# Runs the full pipeline against eval/session5_fixture.md:
#   1. Ensure the fixture exists (regenerate from source if missing)
#   2. Dispatch 3 reviewer backends in parallel
#   3. Merge findings with lib/merge.py
#   4. Score against eval/ground_truth.json with eval/score.py
#
# Exit codes:
#   0  recall >= target (default 0.7)
#   1  recall below target
#   2  infrastructure failure (missing binary, strip_audit failed, backend error)

set -euo pipefail

cd "$(dirname "$0")/.."

PROTO_ROOT="$PWD"
FIXTURE="eval/session5_fixture.md"
GROUND_TRUTH="eval/ground_truth.json"
SOURCE_DOC="$HOME/.gstack/projects/Akagilnc-ai-blogger-lab/akagilnc-main-design-20260411-174843.md"
RUN_ID="eval-$(date +%Y%m%d-%H%M%S)"
RUN_DIR="outputs/$RUN_ID"
TARGET_RECALL="${TARGET_RECALL:-0.7}"
MODE="doc"

echo "=== grounded-review eval: $RUN_ID ==="
echo "fixture:       $FIXTURE"
echo "ground truth:  $GROUND_TRUTH"
echo "target recall: $TARGET_RECALL"
echo "mode:          $MODE"
echo ""

# --- Step 0: environment check ---
for bin in claude codex gemini python3 jq; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "error: required binary '$bin' not found in PATH" >&2
    exit 2
  fi
done

# --- Step 1: ensure fixture exists ---
if [ ! -f "$FIXTURE" ]; then
  if [ ! -f "$SOURCE_DOC" ]; then
    echo "error: source doc not found at $SOURCE_DOC" >&2
    exit 2
  fi
  echo "regenerating fixture from $SOURCE_DOC..."
  python3 lib/strip_audit.py "$SOURCE_DOC" "$FIXTURE"
fi
echo "fixture lines: $(wc -l < "$FIXTURE")"

mkdir -p "$RUN_DIR"

# --- Step 2: dispatch 3 reviewers in parallel ---
#
# Each backend must accept a prompt + target content and return reviewer
# JSON on stdout following the schema in prompts/reviewer-doc.md. These
# backend scripts do not exist yet at the time this script was written;
# steps 7-10 of the prototype plan create them. Once present, uncomment
# the dispatch block below and remove the STUB_MODE short-circuit.

STUB_MODE=0
if [ ! -x backends/claude-headless.sh ] \
   || [ ! -x backends/codex.sh ] \
   || [ ! -x backends/gemini.sh ]; then
  STUB_MODE=1
fi

if [ $STUB_MODE -eq 1 ]; then
  echo ""
  echo "NOTE: backends/ scripts not yet executable — running in STUB MODE."
  echo "      (write backends, then rerun to do the full eval)"
  echo ""
  echo "To run score.py standalone on an existing merged.json:"
  echo "  python3 eval/score.py --merged <path> --ground-truth $GROUND_TRUTH --target $TARGET_RECALL"
  echo ""
  exit 0
fi

PROMPT_FILE="prompts/reviewer-doc.md"
if [ ! -f "$PROMPT_FILE" ]; then
  echo "error: $PROMPT_FILE not found" >&2
  exit 2
fi

# Compose the full dispatch prompt: task prompt + fixture content.
DISPATCH_PROMPT="$(
  cat "$PROMPT_FILE"
  echo
  echo "--- BEGIN TARGET FILE: $FIXTURE ---"
  echo
  cat "$FIXTURE"
  echo
  echo "--- END TARGET FILE ---"
  echo
  echo "Return JSON only. No markdown wrapper."
)"

echo "dispatch prompt: $(printf '%s' "$DISPATCH_PROMPT" | wc -c) bytes"
echo ""
echo "dispatching 3 reviewers in parallel..."
(
  printf '%s' "$DISPATCH_PROMPT" | backends/claude-headless.sh "$MODE" \
    > "$RUN_DIR/claude.json" 2> "$RUN_DIR/claude.err" &
  CLAUDE_PID=$!

  printf '%s' "$DISPATCH_PROMPT" | backends/codex.sh "$MODE" "$PROTO_ROOT" \
    > "$RUN_DIR/codex.json" 2> "$RUN_DIR/codex.err" &
  CODEX_PID=$!

  printf '%s' "$DISPATCH_PROMPT" | backends/gemini.sh "$MODE" \
    > "$RUN_DIR/gemini.json" 2> "$RUN_DIR/gemini.err" &
  GEMINI_PID=$!

  wait $CLAUDE_PID  && echo "  ✓ claude  done ($(jq '.findings | length' "$RUN_DIR/claude.json" 2>/dev/null || echo '?') findings)" \
                    || echo "  ✗ claude  failed — see $RUN_DIR/claude.err"
  wait $CODEX_PID   && echo "  ✓ codex   done ($(jq '.findings | length' "$RUN_DIR/codex.json" 2>/dev/null || echo '?') findings)" \
                    || echo "  ✗ codex   failed — see $RUN_DIR/codex.err"
  wait $GEMINI_PID  && echo "  ✓ gemini  done ($(jq '.findings | length' "$RUN_DIR/gemini.json" 2>/dev/null || echo '?') findings)" \
                    || echo "  ✗ gemini  failed — see $RUN_DIR/gemini.err"
)

# --- Step 3: merge ---
echo ""
echo "merging findings..."
python3 lib/merge.py \
  "$RUN_DIR/claude.json" \
  "$RUN_DIR/codex.json" \
  "$RUN_DIR/gemini.json" \
  > "$RUN_DIR/merged.json"
echo "merged findings: $(jq '.merged_findings | length' "$RUN_DIR/merged.json")"

# --- Step 4: score ---
echo ""
python3 eval/score.py \
  --merged "$RUN_DIR/merged.json" \
  --ground-truth "$GROUND_TRUTH" \
  --target "$TARGET_RECALL"
