#!/usr/bin/env bash
# Gemini reviewer backend — calls `agy` (Antigravity CLI 1.0.0), the
# in-kind replacement for the `gemini` CLI that Google stopped serving
# 2026-06-18. agy 1.0.0 is locked to Gemini 3.5 Flash (no --model
# flag) — the wiki's explicit exception to the strongest-review-model
# rule, traded off to keep 3-vendor cross-family coverage.
#
# Invocation:
#   <stdin: full reviewer prompt incl. the diff to review>
#           | backends/gemini.sh <mode>
#
# Outputs JSON (reviewer payload) to stdout. Diagnostics to stderr.
#
# Env:
#   AGY_PRINT_TIMEOUT        agy's own --print-timeout (default 15m;
#                            agy's built-in default is 5m which is short
#                            for large review diffs).
#   GEMINI_RETRY_WARM_SLEEP  inter-attempt sleep between auth-race
#                            retries (default 0; production needs none
#                            — the per-attempt keychain warm is the
#                            actual mitigation. Tests can set this to 0
#                            explicitly; non-zero is for debugging).
#
# Hard rules (wiki §并行启动 / §agy auth callout):
#   ALWAYS `agy -p --sandbox` (read OK, terminal/write restricted, uses
#   existing OAuth scope). NEVER `--dangerously-skip-permissions` (it
#   re-consents a high scope and breaks headless auth on next run).
#   ALWAYS 2>&1 (so agy's own diagnostics — 429, auth race, etc. — are
#   captured into the output rather than silenced).
#   agy keychain auth-race recipe: warm "Antigravity Safe Storage" each
#   attempt + retry up to 4 attempts total; 4 failed → §降级链 flag
#   "本轮缺 gemini (auth race after retry×3)", do not block.

set -euo pipefail

PROTO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-doc}"
PRINT_TIMEOUT="${AGY_PRINT_TIMEOUT:-15m}"

FULL_PROMPT="$(cat)"

if [ -z "$FULL_PROMPT" ]; then
  echo "gemini: error: empty prompt on stdin" >&2
  exit 1
fi

if ! command -v agy >/dev/null 2>&1; then
  echo "gemini: degrade — flag '本轮缺 gemini' (agy not installed; the post-EOL replacement for the dead gemini CLI)" >&2
  printf '{"reviewer":"gemini","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi

# Read-only contract (wiki §调用规范, line 185). agy (Antigravity) is an
# agentic CLI: `--sandbox` alone does NOT stop it editing files in the
# workspace or running commands. Observed first-run failure: an agy
# review rewrote tracked files (gemini.sh, a test) and ran pytest instead
# of just reviewing. The prompt ITSELF must forbid this. Prepend an
# explicit read-only instruction to every agy prompt; --sandbox is
# defense-in-depth, not the primary guard.
AGY_PROMPT="REVIEW ONLY — HARD CONSTRAINT. Do NOT modify, create, rename,
or delete ANY file. Do NOT run any shell command, test, build, git, or
edit operation. You are a read-only reviewer: your ONLY output is review
findings in the required sentinel-wrapped JSON. Touching the filesystem
or running commands is a contract violation, not help.

$FULL_PROMPT"

# agy keychain auth-race: per-attempt keychain warm + retry. The
# `security find-generic-password` warms the macOS Keychain item path
# so agy's 1s keyringAuth doesn't time out; redirect both streams and
# `|| true` so a missing `security` binary (non-macOS CI) is harmless.
# Capture agy's OWN exit code (G_RC) — a non-zero exit that still
# printed a salvageable JSON error body must STILL degrade, never slip
# through as a silent zero-finding approve.
RAW=""; G_RC=0
for attempt in 1 2 3 4; do
  security find-generic-password -s "Antigravity Safe Storage" \
    >/dev/null 2>&1 || true

  set +e
  RAW="$(cd "$PROTO_ROOT" && agy -p --sandbox --print-timeout "$PRINT_TIMEOUT" 2>&1 <<<"$AGY_PROMPT")"
  G_RC=$?
  set -e

  if [ "$G_RC" -ne 0 ] && echo "$RAW" | grep -qE "Authentication required|authentication timed out"; then
    if [ "$attempt" -lt 4 ]; then
      echo "gemini: warn: agy auth-race on attempt $attempt/4, retrying..." >&2
      [ "${GEMINI_RETRY_WARM_SLEEP:-0}" != "0" ] && sleep "${GEMINI_RETRY_WARM_SLEEP}"
      continue
    fi
    echo "gemini: degrade — flag '本轮缺 gemini (auth race after retry×3)'" >&2
    printf '{"reviewer":"gemini","mode":"%s","findings":[]}\n' "$MODE"
    exit 1
  fi
  break
done

if [ -z "$RAW" ]; then
  echo "gemini: degrade — flag '本轮缺 gemini' (empty output, agy rc=$G_RC)" >&2
  printf '{"reviewer":"gemini","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi

# extract_json takes ONLY the sentinel-wrapped findings (Pass 0); JSON
# echoed from the schema or quoted from the diff is structurally
# ignored. Degrade — visibly, never silent — if EITHER extract_json
# found no contracted findings (EX_RC) OR agy itself exited non-zero
# (G_RC: a non-auth-race failure that still printed a salvageable
# error body). This is the FULL codex-review.sh-style degrade gate.
set +e
EXTRACTED="$(printf '%s' "$RAW" | python3 "$PROTO_ROOT/lib/extract_json.py" gemini "$MODE")"
EX_RC=$?
set -e
if [ "$EX_RC" -ne 0 ] || [ "$G_RC" -ne 0 ]; then
  echo "gemini: degrade — flag '本轮缺 gemini' (extract_json rc=$EX_RC, agy exit rc=$G_RC; agy's stderr is in the captured output per 2>&1)" >&2
  printf '{"reviewer":"gemini","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi
printf '%s\n' "$EXTRACTED"
