#!/usr/bin/env bash
# Gemini reviewer backend — calls `agy` (Antigravity CLI), the in-kind
# replacement for the `gemini` CLI that Google stopped serving
# 2026-06-18. agy defaults to Gemini 3.5 Flash (High) — the recorded 2026-06-18
# exception to the strongest-review-model rule, traded off to keep an
# optional Google-family reviewer.
#
# Invocation:
#   <stdin: pinned review task; reviewer reads the clone>
#           | backends/gemini.sh <mode>
#
# Success: review prose passes through verbatim on stdout. On degrade,
# stdout is empty, exit is nonzero, and diagnostics including the
# "本轮缺 gemini" flag go to stderr.
#
# Env:
#   AGY_PRINT_TIMEOUT        agy's own --print-timeout (default 15m;
#                            agy's built-in default is 5m which is short
#                            for large review diffs).
#   AGY_MODEL                model for the primary review call
#                            (default: Gemini 3.5 Flash (High)).
#   AGY_FALLBACK_MODEL       second agy quota pool tried once only after a
#                            confirmed quota/429 failure (default: Claude
#                            Sonnet 4.6 (Thinking)); empty disables it.
#
# Hard rules (recorded 2026-06; origin: wiki §并行启动 / §agy auth callout):
#   Invocation form uses an explicit model plus `--print ''`, with the
#   packet on stdin (no ARG_MAX limit). Do not add agy's read-only
#   `--sandbox`; the orchestrator already supplies an isolated writable
#   checkout for reviewer tools and probes.
#   NEVER `--dangerously-skip-permissions` (re-consents a high scope and
#   breaks headless auth on next run).
#   ALWAYS 2>&1 (so agy's own diagnostics are
#   captured into the output rather than silenced). Note: agy routes
#   fatal backend errors (e.g. RESOURCE_EXHAUSTED / 429 quota) to its
#   --log-file, NOT stdout/stderr — so a quota-exhausted run looks like
#   a plain empty success (rc=0, empty stdout). We pass --log-file and
#   grep it on degrade so the flag names the real reason.

set -euo pipefail

MODE="${1:-doc}"
PRINT_TIMEOUT="${AGY_PRINT_TIMEOUT:-15m}"

case "$MODE" in
  doc|code) ;;
  *)
    MODE="doc"
    echo "gemini: invalid MODE (expected doc|code) — degrade, flag '本轮缺 gemini'" >&2
    exit 1
    ;;
esac

# The repo UNDER REVIEW (where the orchestrator invoked us — the user's
# project), captured BEFORE any `cd`. agy's workspace must be THIS, not
# PROTO_ROOT: the skill itself lives under `~/.claude/skills/...` (hidden),
# so cd-ing agy into PROTO_ROOT made agy refuse the (hidden) workspace and
# run without repository context on EVERY registered-skill invocation. agy reads its cwd as
# the workspace, so we cd here (not PROTO_ROOT) before running it.
REVIEW_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# agy routes fatal backend errors (RESOURCE_EXHAUSTED / 429 quota, the
# agent-executor error line) to its --log-file, not to the captured
# stdout/stderr.
# Give agy a private log so the degrade paths can name the real reason;
# clean it up on any exit.
AGY_LOG="$(mktemp "${TMPDIR:-/tmp}/agy-cmr.XXXXXX")"
AGY_PROMPT_FILE="$(mktemp "${TMPDIR:-/tmp}/agy-cmr-prompt.XXXXXX")"
trap 'rm -f "$AGY_LOG" "$AGY_PROMPT_FILE"' EXIT

# agy refuses to add a workspace folder whose path has a hidden (dot)
# component ("... is hidden: ignore uri" in its log) → the Gemini reviewer
# gets NO repo context (cannot inspect or grep source). We now point agy
# at REVIEW_ROOT (the reviewed repo), so this only fires when the user's
# OWN project is under a dot-path (e.g. reviewing from a
# `.claude/worktrees/...` checkout) — NOT, as before, on every invocation
# just because the skill lives under `~/.claude/`. Warn (do not degrade —
# agy still reviews the diff); rerun from a non-hidden checkout for full
# context.
case "$REVIEW_ROOT" in
  */.*)
    echo "gemini: warn: the reviewed repo root '$REVIEW_ROOT' is under a hidden (dot) directory; agy will not add it as a workspace folder ('is hidden: ignore uri'), so the Gemini reviewer runs WITHOUT repo context and cannot inspect source. Review from a non-hidden checkout for full agy context." >&2
    ;;
esac

# Single source for "is $AGY_LOG a quota/429 exhaustion?". Match explicit
# quota/429 shapes: bare RESOURCE_EXHAUSTED may describe non-quota pressure.
# grep reads the file directly (no `printf | grep -q` SIGPIPE under pipefail).
agy_log_has_quota() {
  grep -qiE '\(code 429\)|quota reached|quota exceeded|individual quota' "$AGY_LOG"
}

# On a degrade, surface WHY by scanning ONLY agy's --log-file — that is
# where agy actually writes its fatal backend errors. Do NOT scan $RAW:
# on the extract-fail path $RAW is the full model output, which may quote
# reviewed source, so source that merely mentions quota/429 code
# would yield a false "quota exhausted" attribution (cross-model review
# R1: Claude C1 + codex#2 R1, live-reproduced). Always returns 0 (empty
# = no known reason).
agy_fatal_reason() {
  [ -s "$AGY_LOG" ] || return 0
  if agy_log_has_quota; then
    # Optional detail. `grep -m1 … || true` keeps it non-fatal under
    # `set -euo pipefail`: a no-match (grep exit 1) must NOT abort the
    # function before the reason is printed (online R1: gemini + sourcery;
    # the empty-/no-match degrade is exercised by the R2 characterization
    # tests). `-m1` caps to the first matching LINE, but agy writes the
    # error TWICE on one line, so `-o` still emits two matches — keep only
    # the first via `${resets%%<newline>*}` (no extra pipe → no SIGPIPE),
    # else the flag carries a doubled, newline-split "Resets in …".
    local resets
    resets="$(grep -m1 -oiE 'Resets in [0-9hdms]+' "$AGY_LOG" || true)"
    resets="${resets%%$'\n'*}"
    printf 'quota/429 — agy individual quota exhausted%s' "${resets:+; $resets}"
    return 0
  fi
  # `.*` (to end of line, not `[^:]*`) so a multi-colon executor error
  # like "agent executor error: call failed: backend timeout" is kept
  # whole, not truncated at the first colon (online R1: sourcery).
  local execerr
  execerr="$(grep -m1 -oE 'agent executor error: .*' "$AGY_LOG" || true)"
  [ -n "$execerr" ] && printf '%s' "$execerr"
  return 0
}

cat > "$AGY_PROMPT_FILE"
if [ ! -s "$AGY_PROMPT_FILE" ]; then
  echo "gemini: error: empty prompt on stdin" >&2
  exit 1
fi

if ! command -v agy >/dev/null 2>&1; then
  echo "gemini: degrade — flag '本轮缺 gemini' (agy not installed; the post-EOL replacement for the dead gemini CLI)" >&2
  exit 1
fi

# Primary gets one call. A confirmed quota/429 may use the configured second
# agy quota pool once; auth and every other failure degrade without another call.
AGY_PRIMARY_MODEL="${AGY_MODEL:-Gemini 3.5 Flash (High)}"
AGY_FALLBACK_MODEL="${AGY_FALLBACK_MODEL-Claude Sonnet 4.6 (Thinking)}"
AGY_RAN_MODEL="$AGY_PRIMARY_MODEL"
AGY_USED_FALLBACK=0

run_agy() {
  local model="$1"
  : > "$AGY_LOG"
  set +e
  RAW="$(cd "$REVIEW_ROOT" && agy --model "$model" --print '' --print-timeout "$PRINT_TIMEOUT" --log-file "$AGY_LOG" 2>&1 < "$AGY_PROMPT_FILE")"
  G_RC=$?
  set -e
}

run_agy "$AGY_RAN_MODEL"
if [ -n "$AGY_FALLBACK_MODEL" ] && agy_log_has_quota; then
  AGY_RAN_MODEL="$AGY_FALLBACK_MODEL"
  AGY_USED_FALLBACK=1
  run_agy "$AGY_RAN_MODEL"
fi

if [ -z "$RAW" ]; then
  REASON="$(agy_fatal_reason)"
  echo "gemini: degrade — flag '本轮缺 gemini' (empty output, agy rc=$G_RC${REASON:+; $REASON})" >&2
  exit 1
fi

# Past the empty-output degrade above, RAW holds agy's review. Degrade
# — visibly, never silent — iff agy itself failed (G_RC≠0) OR the selected
# model's log shows quota
# exhaustion; otherwise pass agy's review THROUGH VERBATIM for the
# orchestrator to read with judgment.
#
# The quota-log check catches agy exits that return zero with a non-empty
# diagnostic banner; it keys on the fatal log, not the output format.
#
# We deliberately do NOT run extract_json / require a sentinel-JSON shape.
# Gemini's review is prose; the old sentinel gate treated any prose as
# "no findings JSON" and degraded it to 本轮缺 gemini — dropping a real
# review over format (prose-review is this skill's contract: review text
# the agent reads). The degrade-reason scan still reads ONLY agy's
# --log-file (agy_fatal_reason), never $RAW, so a review body that quotes
# the diff's quota/429 code cannot mis-attribute a reason.
if [ "$G_RC" -ne 0 ] || agy_log_has_quota; then
  REASON="$(agy_fatal_reason)"
  echo "gemini: degrade — flag '本轮缺 gemini' (agy exit rc=$G_RC${REASON:+; $REASON}; agy's stderr is in the captured output per 2>&1)" >&2
  exit 1
fi

# Success with an explicit non-Gemini/non-Google model flags the actual family.
# Emitted only after success, never on a degraded round.
case "$AGY_RAN_MODEL" in
  *[Gg]emini*|*[Gg]oogle*) ;;
  *)
    if [ "$AGY_USED_FALLBACK" -eq 1 ]; then
      echo "gemini: note: agy primary '$AGY_PRIMARY_MODEL' exhausted quota; fallback '$AGY_RAN_MODEL' succeeded. Actual model is non-Google; NO Google family this round." >&2
    else
      echo "gemini: note: agy ran the explicit AGY_MODEL override '$AGY_RAN_MODEL'. Actual model is non-Google; NO Google family this round." >&2
    fi
    ;;
esac
printf '%s\n' "$RAW"
