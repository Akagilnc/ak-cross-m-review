#!/usr/bin/env bash
# Codex reviewer backend for /ak-cross-m-review.
#
# This is the DELIVERATELY-CORRECT codex invocation. It exists because the
# naive/uncorrected codex invocations use the two patterns the
# wiki marks confidence-10 footguns (D1/D2 in the analysis):
#
#   ❌ codex exec "$PROMPT" -C "$WORKDIR" -s read-only
#      - positional-arg prompt (stdin-pipe hang risk; off-convention)
#      - `-C` flag → runs in the wrong workdir (codex-wrong-repo-cwd)
#      - no `--model` → review quality drifts to the CLI default
#
#   ✅ cat <<'PROMPT' | codex exec --ephemeral --model gpt-5.5 - 2>&1
#      - stdin pipe (the `-` means "read prompt from stdin")
#      - `--ephemeral`: do NOT persist a session rollout file. cmr runs
#        N codex in parallel (1+N+1); without it concurrent instances
#        collide on ~/.codex/session → cross-talk (prompt A surfaces in
#        instance B's context). Wiki §额外硬规则 #6 / codex#11435.
#      - `--model gpt-5.5` pinned: review-tier, never dev-tier spark/5.3
#      - NO `-C`: codex runs from the current dir (the repo root)
#      - always 2>&1 so failures are visible
#
# Source of truth:
#   wiki/concepts/cross-model-review.md  §调用规范 / §额外硬规则
#   wiki/concepts/codex-bot-conventions.md  §CLI 侧的正确 pattern / §模型变体
#
# Invocation:
#   <stdin: full review prompt incl. diff> | codex-review.sh <mode> [<label>]
#     mode  : doc | code   (passed to extract_json.py)
#     label : optional diagnostic tag (e.g. "section-2of3")
#
#   CMR_CODEX_MODEL   override review model (default: gpt-5.5)
#   CMR_CODEX_TIMEOUT hard wall-clock seconds before pkill (default: 600)
#   CMR_DRY_RUN=1     print the exact command that WOULD run, do not call
#                     codex, exit 0. Used by --selftest.
#
# Outputs reviewer JSON (reviewer=codex) to stdout. Diagnostics to stderr.
# On timeout / empty output: synthetic empty-findings JSON + exit 1 so the
# orchestrator degrades and flags "本轮缺 codex" instead of silently passing.

set -euo pipefail

# Resolve the shared lib (this script lives at backends/, lib/ is one
# level up).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROTO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXTRACT="$PROTO_ROOT/lib/extract_json.py"

MODE="${1:-code}"
LABEL="${2:-full}"
MODEL="${CMR_CODEX_MODEL:-gpt-5.5}"
TIMEOUT_S="${CMR_CODEX_TIMEOUT:-600}"

# Single source of truth for the codex invocation. Every real call site
# (timeout / gtimeout / background) AND the --selftest validation derive
# from this one array, so adding or changing a flag — e.g. --ephemeral —
# touches ONE place, not five. (bot-flagged DRY: the duplicated command
# string was what made the --ephemeral add error-prone, and let the
# selftest validate a hand-copied mirror instead of the live command.)
# Expand as "${CODEX_CMD[@]}" at call sites; the `2>&1` redirection is
# added per-call (it is shell redirection, not part of the command).
CODEX_CMD=(codex exec --ephemeral --model "$MODEL" -)

# --selftest: validate the REAL invocation array (not a hand-copied
# mirror), assert it is on-convention, never call codex. Regression
# guard for D1/D2 + the --ephemeral parallel-session rule.
if [ "${1:-}" = "--selftest" ]; then
  CMD="${CODEX_CMD[*]} 2>&1"
  fail=0
  case "$CMD" in
    *" -C "*) echo "FAIL: command contains -C (wrong-workdir footgun)" >&2; fail=1 ;;
  esac
  case "$CMD" in
    *"--model "*) ;;
    *) echo "FAIL: command missing --model pin" >&2; fail=1 ;;
  esac
  case "$CMD" in
    *"codex exec --ephemeral --model ${MODEL} -"*) ;;
    *) echo "FAIL: command not stdin-pipe form ('codex exec --ephemeral --model X -')" >&2; fail=1 ;;
  esac
  # --ephemeral mandatory: parallel codex instances collide on
  # ~/.codex/session without it (wiki §额外硬规则 #6 / codex#11435).
  case "$CMD" in
    *"--ephemeral"*) ;;
    *) echo "FAIL: command missing --ephemeral (parallel session-collision guard)" >&2; fail=1 ;;
  esac
  case "$CMD" in
    *"2>&1"*) ;;
    *) echo "FAIL: command missing 2>&1" >&2; fail=1 ;;
  esac
  # Positional-arg form must never appear. With CODEX_CMD now an array,
  # a quote-based string match on "$CMD" is DEAD — array expansion
  # (${CODEX_CMD[*]}) strips the quotes, so a reintroduced positional
  # prompt (CODEX_CMD=(codex exec "$PROMPT" ...)) would slip through.
  # Validate the array STRUCTURE instead (gemini R3 HIGH): exactly the
  # canonical 6 tokens, `codex exec` first, stdin `-` last. Explicit
  # index [5] (not negative) keeps this bash-3.2 safe (macOS default).
  if [ "${#CODEX_CMD[@]}" -ne 6 ] \
     || [ "${CODEX_CMD[0]} ${CODEX_CMD[1]}" != "codex exec" ] \
     || [ "${CODEX_CMD[5]}" != "-" ]; then
    echo "FAIL: codex command array shape off (positional-arg / stray flag / missing stdin '-'; update this guard if a flag was intentionally added)" >&2
    fail=1
  fi
  if [ "$fail" -eq 0 ]; then
    echo "✓ codex-review.sh invocation is on-convention: ${CMD}"
    exit 0
  fi
  exit 1
fi

FULL_PROMPT="$(cat)"
if [ -z "$FULL_PROMPT" ]; then
  echo "codex-review: error: empty prompt on stdin" >&2
  exit 1
fi

if [ "${CMR_DRY_RUN:-0}" = "1" ]; then
  echo "DRY_RUN cmd: printf %s \"\$PROMPT\" | ${CODEX_CMD[*]} 2>&1" >&2
  printf '{"reviewer":"codex","mode":"%s","findings":[]}\n' "$MODE"
  exit 0
fi

echo "codex-review: model=${MODEL} mode=${MODE} label=${LABEL} timeout=${TIMEOUT_S}s" >&2

# Portable hard timeout. The prompt ALWAYS reaches codex via a temp file
# fed to `codex exec --ephemeral --model "$MODEL" -` (the `-` = read stdin). An
# earlier version fed $FULL_PROMPT as a here-string into a `bash -c`
# that read it as an out-of-scope variable → empty prompt whenever GNU
# timeout/gtimeout was present (the default on homebrew macOS), so codex
# silently never ran. Fixed: one stdin path for every branch, real
# timeout (rc 124/137/143) treated as degrade, and the no-coreutils
# fallback kills only THIS codex + its children (never a global
# `pkill -f 'codex exec'`, which would take down sibling parallel codex
# reviewers and unrelated user codex runs).
PROMPT_TMP="$(mktemp)"
trap 'rm -f "$PROMPT_TMP"' EXIT
printf '%s' "$FULL_PROMPT" > "$PROMPT_TMP"

RAW=""
RC=0
if command -v timeout >/dev/null 2>&1; then
  set +e
  RAW="$(timeout "${TIMEOUT_S}s" "${CODEX_CMD[@]}" < "$PROMPT_TMP" 2>&1)"
  RC=$?
  set -e
elif command -v gtimeout >/dev/null 2>&1; then
  set +e
  RAW="$(gtimeout "${TIMEOUT_S}s" "${CODEX_CMD[@]}" < "$PROMPT_TMP" 2>&1)"
  RC=$?
  set -e
else
  # No coreutils timeout: background codex, scoped-kill on timeout.
  # A flag file records that the watchdog fired, so a codex that traps
  # TERM and exits 0 *after* the deadline is still treated as a timeout
  # (not a false success). KILL escalation if TERM is ignored.
  TMP_OUT="$(mktemp)"
  TIMED_OUT="$(mktemp)"; rm -f "$TIMED_OUT"
  trap 'rm -f "$PROMPT_TMP" "$TMP_OUT" "$TIMED_OUT"' EXIT
  "${CODEX_CMD[@]}" < "$PROMPT_TMP" >"$TMP_OUT" 2>&1 &
  CODEX_PID=$!
  ( sleep "$TIMEOUT_S"
    if kill -0 "$CODEX_PID" 2>/dev/null; then
      : > "$TIMED_OUT"
      echo "codex-review: timeout ${TIMEOUT_S}s — killing pid $CODEX_PID + children (scoped, not global)" >&2
      pkill -TERM -P "$CODEX_PID" 2>/dev/null || true
      kill  -TERM "$CODEX_PID" 2>/dev/null || true
      sleep 2
      pkill -KILL -P "$CODEX_PID" 2>/dev/null || true
      kill  -KILL "$CODEX_PID" 2>/dev/null || true
    fi ) &
  WATCH_PID=$!
  set +e
  wait "$CODEX_PID"
  RC=$?
  set -e
  kill "$WATCH_PID" 2>/dev/null || true
  RAW="$(cat "$TMP_OUT" 2>/dev/null || true)"
  [ -f "$TIMED_OUT" ] && RC=124   # watchdog fired → force the degrade path
  rm -f "$TMP_OUT" "$TIMED_OUT"
fi

# rc 124 = timeout(1) / our watchdog; 137/143 = SIGKILL/SIGTERM. A
# truncated-but-brace-balanced fragment must NOT parse as real findings
# — any timeout/kill is a degrade regardless of partial stdout.
case "$RC" in
  124|137|143) RAW="" ;;
esac

if [ -z "$RAW" ]; then
  echo "codex-review: error: empty output / timeout (rc=$RC) — degrade, flag '本轮缺 codex'" >&2
  printf '{"reviewer":"codex","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi

# JSON-aware hard-error detection. The previous version grepped the
# whole review body for auth/quota/rate/429 and false-degraded ANY
# valid review that merely discussed rate-limit/quota/auth code (among
# the defect categories codex is explicitly asked to find — it even
# self-degraded on this repo). Instead lean on extract_json.py's
# documented contract: it exits non-zero ONLY when it cannot find real
# findings JSON and fell back to a synthetic empty object — i.e. codex
# emitted an error/banner, not a review. A valid review (including a
# clean zero-finding approve, and one whose findings quote "429" /
# "quota") parses cleanly → exit 0 → never degraded. Zero false
# positives by construction.
set +e
EXTRACTED="$(printf '%s' "$RAW" | python3 "$EXTRACT" codex "$MODE")"
EX_RC=$?
set -e
if [ "$EX_RC" -ne 0 ] || [ "$RC" -ne 0 ]; then
  # EX_RC!=0: extract_json found no real findings JSON (codex emitted an
  # error/banner). RC!=0: codex itself exited non-zero — even when it
  # printed a JSON error body that extract_json salvaged into findings:[]
  # (pass-5) and exited 0. Without the RC guard, an auth/quota-failed
  # codex would count as a valid zero-finding reviewer and could help a
  # single real reviewer look like a converged round. A clean review
  # always exits 0, so this stays zero-false-positive.
  echo "codex-review: not a valid review — degrade, flag '本轮缺 codex' (extract_json rc=$EX_RC, codex exit rc=$RC)" >&2
  printf '{"reviewer":"codex","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi
printf '%s\n' "$EXTRACTED"
