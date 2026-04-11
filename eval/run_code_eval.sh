#!/usr/bin/env bash
# Code-mode eval runner for the grounded-review prototype.
#
# Runs the full 3-reviewer pipeline against eval/code_fixture.ts and scores
# against eval/code_ground_truth.json (5 planted bugs).
#
# Success bar: recall >= 4/5 (80%).

set -euo pipefail

cd "$(dirname "$0")/.."
PROTO_ROOT="$PWD"

FIXTURE="eval/code_fixture.ts"
GROUND_TRUTH="eval/code_ground_truth.json"
RUN_ID="eval-code-$(date +%Y%m%d-%H%M%S)"
RUN_DIR="outputs/$RUN_ID"
TARGET_RECALL="${TARGET_RECALL:-0.8}"
MODE="code"

echo "=== grounded-review CODE eval: $RUN_ID ==="
echo "fixture:       $FIXTURE"
echo "ground truth:  $GROUND_TRUTH"
echo "target recall: $TARGET_RECALL"
echo "mode:          $MODE"
echo ""

# --- Step 0: binaries ---
for bin in claude codex gemini python3 jq; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "error: required binary '$bin' not found in PATH" >&2
    exit 2
  fi
done

[ -f "$FIXTURE" ] || { echo "error: fixture not found: $FIXTURE" >&2; exit 2; }
[ -f "$GROUND_TRUTH" ] || { echo "error: ground truth not found: $GROUND_TRUTH" >&2; exit 2; }

mkdir -p "$RUN_DIR"

# --- Step 1: compose dispatch prompt ---
PROMPT="prompts/reviewer-code.md"
DISPATCH_PROMPT="$(
  cat "$PROMPT"
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

# --- Step 2: dispatch 3 reviewers in parallel ---
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
echo "stats: $(jq -c '.stats' "$RUN_DIR/merged.json")"

# --- Step 4: score ---
echo ""
python3 eval/score.py \
  --merged "$RUN_DIR/merged.json" \
  --ground-truth "$GROUND_TRUTH" \
  --target "$TARGET_RECALL"
