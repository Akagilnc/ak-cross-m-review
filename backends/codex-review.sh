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
#        -c model_reasoning_effort="<high|xhigh>" --model gpt-5.5 - 2>&1
#      - stdin pipe (the `-` means "read prompt from stdin")
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
# On success codex's review (PROSE or JSON) is passed through VERBATIM to
# stdout — the orchestrator reads it with judgment (wiki §「.result 是
# review 文本」). Diagnostics to stderr. On timeout / empty output / a
# non-zero codex exit (auth/quota/crash): synthetic empty-findings JSON +
# exit 1 so the orchestrator degrades and flags "本轮缺 codex". The script
# does NOT parse findings or demand a sentinel-JSON format — that gate
# dropped codex's prose review as a phantom outage (removed here).

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
CODEX_CMD=(codex exec --ephemeral -c model_reasoning_effort="$CMR_CODEX_EFFORT" --model "$MODEL" -)

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
    *"codex exec --ephemeral -c model_reasoning_effort=${CMR_CODEX_EFFORT} --model ${MODEL} -"*) ;;
    *) echo "FAIL: command not canonical stdin-pipe form ('codex exec --ephemeral -c model_reasoning_effort=${CMR_CODEX_EFFORT} --model X -')" >&2; fail=1 ;;
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
  # canonical 8 tokens (codex exec --ephemeral -c model_reasoning_effort=
  # xhigh --model X -), `codex exec` first, stdin `-` last. Explicit
  # index [7] (not negative) keeps this bash-3.2 safe (macOS default).
  if [ "${#CODEX_CMD[@]}" -ne 8 ] \
     || [ "${CODEX_CMD[0]} ${CODEX_CMD[1]}" != "codex exec" ] \
     || [ "${CODEX_CMD[7]}" != "-" ]; then
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

# Past the empty/timeout degrade above, RAW holds codex's output. The
# ONLY remaining outage signal is codex's own exit code: a clean review
# (prose or JSON) exits 0; auth/quota/crash exit non-zero. So degrade
# iff rc≠0 — and otherwise pass the review THROUGH VERBATIM.
#
# We deliberately do NOT parse findings or require a sentinel-JSON shape.
# Codex's strongest review is PROSE; the old extract_json sentinel gate
# treated any prose (no sentinel) as "no findings JSON" and degraded it
# to 本轮缺 codex — indistinguishable from a real outage, so the best
# reviewer was repeatedly dropped over format. The wiki's model is that
# reviewers return review text and the orchestrator (an agent) reads it
# with judgment; this restores that. Grepping the body for auth/quota/429
# is also wrong — a prose review legitimately discusses those as defect
# categories (it self-degraded on this repo once). rc is the clean,
# content-independent outage signal.
if [ "$RC" -ne 0 ]; then
  echo "codex-review: codex exited rc=$RC (auth/quota/crash, not a review) — degrade, flag '本轮缺 codex'" >&2
  printf '{"reviewer":"codex","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi
printf '%s\n' "$RAW"
