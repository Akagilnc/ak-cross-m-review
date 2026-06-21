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
#   ✅ cat <<'PROMPT' | codex exec --ephemeral \
#        -c model_reasoning_effort="<high|xhigh>" --model gpt-5.5 \
#        -o <last-message-file> - 2>&1
#      - stdin pipe (the `-` means "read prompt from stdin")
#      - `-o <file>` (--output-last-message): codex writes ONLY its final
#        message (the review: findings + verification + CMR-VERDICT) to
#        this file. We emit THAT, not stdout. `codex exec`'s stdout is the
#        full prompt echo + reasoning trace — 1.5MB on a real diff, ~99%
#        of it noise the orchestrator already has. `-o` is codex's native
#        "last message only" output: a few KB, complete, no parser needed.
#      - `--ephemeral`: do NOT persist a session rollout file. cmr runs
#        N codex in parallel (1+N+1); without it concurrent instances
#        collide on ~/.codex/session → cross-talk (prompt A surfaces in
#        instance B's context). Wiki §额外硬规则 #6 / codex#11435.
#      - `-c model_reasoning_effort=<high|xhigh>`: pin review depth so a
#        clone / other host can't silently inherit a lower config.toml
#        value. Scenario-dependent (CMR_CODEX_EFFORT): ship-pre=xhigh,
#        per-slice=high (wiki §调用规范 reasoning-effort callout)
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
#     mode  : doc | code   (review lens; echoed in the degrade payload)
#     label : optional diagnostic tag (e.g. "section-2of3")
#
#   CMR_CODEX_MODEL   override review model (default: gpt-5.5)
#   CMR_CODEX_TIMEOUT hard wall-clock seconds before pkill (default: 600)
#   CMR_DRY_RUN=1     print the exact command that WOULD run, do not call
#                     codex, exit 0. Used by --selftest.
#
# On success we emit codex's FINAL MESSAGE (the review — prose or JSON,
# from the `-o` file) to stdout; the orchestrator reads it with judgment
# (wiki §「.result 是 review 文本」). Diagnostics to stderr. On timeout /
# non-zero codex exit (auth/quota/crash) / an empty final message:
# synthetic empty-findings JSON + exit 1 so the orchestrator degrades and
# flags "本轮缺 codex". The script does NOT parse findings or demand a
# sentinel-JSON format — that gate dropped codex's prose review as a
# phantom outage (removed in 0.3.9.0). It also does NOT tail-parse the
# verbose stdout — codex's own `-o` gives the clean last message directly.

set -euo pipefail

MODE="${1:-code}"
LABEL="${2:-full}"
MODEL="${CMR_CODEX_MODEL:-gpt-5.5}"
TIMEOUT_S="${CMR_CODEX_TIMEOUT:-600}"
# Reasoning effort is scenario-dependent (wiki §调用规范 effort 表,
# 2026-06-18): ship-pre 5a/5b = `xhigh` (the real gate + cross-slice
# invariants need max depth); per-slice = `high` (cheap high-frequency
# gate, downshifted to save codex credit — but never below `high`, else
# per-slice becomes a rubber stamp). The caller (SKILL.md) sets
# CMR_CODEX_EFFORT=high for per-slice; default xhigh for ship-pre.
CMR_CODEX_EFFORT="${CMR_CODEX_EFFORT:-xhigh}"
case "$CMR_CODEX_EFFORT" in
  high|xhigh) ;;
  *) echo "codex-review: error: CMR_CODEX_EFFORT must be high|xhigh, got '$CMR_CODEX_EFFORT'" >&2; exit 64 ;;
esac

# codex writes ONLY its final message (the review) here via
# `-o`/--output-last-message. We emit this file's contents on success, NOT
# codex's stdout (which is the full prompt echo + reasoning trace, ~1.5MB
# of mostly-noise on a real diff). Created before CODEX_CMD so the array
# can reference it; cleaned on EXIT (the trap is widened when PROMPT_TMP is
# added below).
LASTMSG="$(mktemp)"
trap 'rm -f "$LASTMSG"' EXIT

# Single source of truth for the codex invocation. Every real call site
# (timeout / gtimeout / background) AND the --selftest validation derive
# from this one array, so adding or changing a flag — e.g. --ephemeral —
# touches ONE place, not five. (bot-flagged DRY: the duplicated command
# string was what made the --ephemeral add error-prone, and let the
# selftest validate a hand-copied mirror instead of the live command.)
# Expand as "${CODEX_CMD[@]}" at call sites; the `2>&1` redirection is
# added per-call (it is shell redirection, not part of the command).
# `-c model_reasoning_effort=…` pins codex review depth (high|xhigh per
# scenario, see CMR_CODEX_EFFORT above) — codex inherits ~/.codex/
# config.toml's global value otherwise, so pinning it in the command
# prevents a clone / other machine from silently dropping to a lower tier
# (wiki §调用规范 reasoning-effort callout).
CODEX_CMD=(codex exec --ephemeral -c model_reasoning_effort="$CMR_CODEX_EFFORT" --model "$MODEL" -o "$LASTMSG" -)

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
  # On-convention canonical form. This pins BOTH the stdin-pipe shape AND
  # `-c model_reasoning_effort=<effort>` (the reasoning-depth pin so a
  # clone / other host can't inherit a lower config.toml value, wiki
  # §调用规范). The effort is scenario-dependent (high|xhigh, validated at
  # the top into CMR_CODEX_EFFORT), so the pattern matches the live value
  # — a missing/altered pin fails this single check (a separate guard
  # would only double-report, online R2: gemini).
  case "$CMD" in
    *"codex exec --ephemeral -c model_reasoning_effort=${CMR_CODEX_EFFORT} --model ${MODEL} -o "*) ;;
    *) echo "FAIL: command not canonical form ('codex exec --ephemeral -c model_reasoning_effort=${CMR_CODEX_EFFORT} --model X -o <file> -')" >&2; fail=1 ;;
  esac
  # -o/--output-last-message mandatory: it is how we get codex's clean
  # final review instead of the 1.5MB stdout echo (no -o → we'd have
  # nothing to emit on the success path).
  case "$CMD" in
    *" -o "*) ;;
    *) echo "FAIL: command missing -o/--output-last-message (last-message extraction)" >&2; fail=1 ;;
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
  # canonical 10 tokens (codex exec --ephemeral -c model_reasoning_effort=
  # xhigh --model X -o <file> -), `codex exec` first, `-o` at [7], stdin
  # `-` last at [9]. Explicit indices (not negative) keep this bash-3.2
  # safe (macOS default).
  if [ "${#CODEX_CMD[@]}" -ne 10 ] \
     || [ "${CODEX_CMD[0]} ${CODEX_CMD[1]}" != "codex exec" ] \
     || [ "${CODEX_CMD[7]}" != "-o" ] \
     || [ "${CODEX_CMD[9]}" != "-" ]; then
    echo "FAIL: codex command array shape off (positional-arg / stray flag / missing -o / missing stdin '-'; update this guard if a flag was intentionally added)" >&2
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
# fed to `codex exec --ephemeral -c model_reasoning_effort="$CMR_CODEX_EFFORT"
# --model "$MODEL" -` (the `-` = read stdin; via the CODEX_CMD array). An
# earlier version fed $FULL_PROMPT as a here-string into a `bash -c`
# that read it as an out-of-scope variable → empty prompt whenever GNU
# timeout/gtimeout was present (the default on homebrew macOS), so codex
# silently never ran. Fixed: one stdin path for every branch, real
# timeout (rc 124/137/143) treated as degrade, and the no-coreutils
# fallback kills only THIS codex + its children (never a global
# `pkill -f 'codex exec'`, which would take down sibling parallel codex
# reviewers and unrelated user codex runs).
PROMPT_TMP="$(mktemp)"
trap 'rm -f "$PROMPT_TMP" "$LASTMSG"' EXIT
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
  trap 'rm -f "$PROMPT_TMP" "$LASTMSG" "$TMP_OUT" "$TIMED_OUT"' EXIT
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

# Outage signals, in order. We emit codex's FINAL MESSAGE (the `-o`
# file) on success — NOT $RAW (the full stdout echo+trace, kept only so a
# failure's diagnostics aren't lost). Three true-outage cases degrade:
#
#  1. timeout/kill (rc 124 = timeout(1)/watchdog; 137/143 = SIGKILL/TERM)
#     — a partial -o file from a killed codex must NEVER count as a review.
#  2. codex exited non-zero (auth/quota/crash). rc is the clean,
#     content-independent outage signal; we do NOT grep the body for
#     auth/quota/429 — a real prose review legitimately discusses those as
#     defect categories (it self-degraded on this repo once).
#  3. rc=0 but the -o final-message file is empty — codex produced only a
#     trace, or `-o` is unsupported. An empty review must not slip through
#     as a silent zero-finding approve.
#
# We do NOT parse findings or require a sentinel-JSON shape (that gate
# dropped codex's prose as a phantom outage, removed 0.3.9.0), and we do
# NOT tail-parse stdout — codex's own `-o` gives the clean last message.
case "$RC" in
  124|137|143)
    echo "codex-review: timeout/kill (rc=$RC) — degrade, flag '本轮缺 codex'" >&2
    printf '{"reviewer":"codex","mode":"%s","findings":[]}\n' "$MODE"
    exit 1
    ;;
esac
if [ "$RC" -ne 0 ]; then
  echo "codex-review: codex exited rc=$RC (auth/quota/crash, not a review) — degrade, flag '本轮缺 codex'" >&2
  printf '{"reviewer":"codex","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi

REVIEW="$(cat "$LASTMSG" 2>/dev/null || true)"
if [ -z "$REVIEW" ]; then
  echo "codex-review: codex exited 0 but wrote no final message (empty -o file; only a trace, or -o unsupported) — degrade, flag '本轮缺 codex'" >&2
  printf '{"reviewer":"codex","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi
printf '%s\n' "$REVIEW"
