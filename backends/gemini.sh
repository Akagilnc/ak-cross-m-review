#!/usr/bin/env bash
# Gemini reviewer backend — calls `agy` (Antigravity CLI), the in-kind
# replacement for the `gemini` CLI that Google stopped serving
# 2026-06-18. agy is locked to Gemini 3.5 Flash — the recorded 2026-06-18
# exception to the strongest-review-model rule, traded off to keep
# 3-vendor cross-family coverage.
#
# Invocation:
#   <stdin: full reviewer prompt incl. the diff to review>
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
#   GEMINI_RETRY_WARM_SLEEP  inter-attempt sleep between auth-race
#                            retries (default 0; production needs none
#                            — the per-attempt keychain warm is the
#                            actual mitigation. Tests can set this to 0
#                            explicitly; non-zero is for debugging).
#   AGY_MODEL                override the agy model-degradation ladder
#                            with ONE explicit model (manual / tests).
#                            Unset = the ladder: Gemini 3.5 Flash →
#                            (quota) Claude Sonnet 4.6 (Thinking) → (all
#                            quota) degrade. See the ladder block below.
#
# Hard rules (recorded 2026-06; origin: wiki §并行启动 / §agy auth callout):
#   Invocation form: `agy --sandbox --print '' <<<prompt` (read OK,
#   terminal/write restricted, existing OAuth scope). NOT the old
#   `agy -p --sandbox <<<prompt`: agy 1.0.7 changed `--print`/`-p` to a
#   string flag that takes its value from the NEXT token, so `-p
#   --sandbox` silently swallowed `--sandbox` as the prompt value —
#   `--sandbox` never engaged and the real prompt rode in only via the
#   stdin-concatenation path (prompt = <--print value> + "\n" + stdin).
#   `--sandbox` BEFORE an explicit empty `--print ''` keeps sandbox a
#   real flag and the diff on stdin (no ARG_MAX limit). Verified by
#   the "enabling terminal sandbox for this session" log line.
#   NEVER `--dangerously-skip-permissions` (re-consents a high scope and
#   breaks headless auth on next run).
#   ALWAYS 2>&1 (so agy's own diagnostics — auth race etc. — are
#   captured into the output rather than silenced). Note: agy routes
#   fatal backend errors (e.g. RESOURCE_EXHAUSTED / 429 quota) to its
#   --log-file, NOT stdout/stderr — so a quota-exhausted run looks like
#   a plain empty success (rc=0, empty stdout). We pass --log-file and
#   grep it on degrade so the flag names the real reason.
#   agy keychain auth-race recipe: warm "Antigravity Safe Storage" each
#   attempt + retry up to 4 attempts total; 4 failed → §降级链 flag
#   "本轮缺 gemini (auth race after retry×3)", do not block.

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
# run diff-only on EVERY registered-skill invocation. agy reads its cwd as
# the workspace, so we cd here (not PROTO_ROOT) before running it.
REVIEW_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# agy routes fatal backend errors (RESOURCE_EXHAUSTED / 429 quota, the
# agent-executor error line) to its --log-file, not to the captured
# stdout/stderr. (The keychain auth-race is the exception — it surfaces
# on stdout/stderr and is handled by the retry gate below, not here.)
# Give agy a private log so the degrade paths can name the real reason;
# clean it up on any exit.
AGY_LOG="$(mktemp "${TMPDIR:-/tmp}/agy-cmr.XXXXXX")"
trap 'rm -f "$AGY_LOG"' EXIT

# agy refuses to add a workspace folder whose path has a hidden (dot)
# component ("... is hidden: ignore uri" in its log) → the Gemini reviewer
# gets NO repo context (diff-only, cannot grep source). We now point agy
# at REVIEW_ROOT (the reviewed repo), so this only fires when the user's
# OWN project is under a dot-path (e.g. reviewing from a
# `.claude/worktrees/...` checkout) — NOT, as before, on every invocation
# just because the skill lives under `~/.claude/`. Warn (do not degrade —
# agy still reviews the diff); rerun from a non-hidden checkout for full
# context.
case "$REVIEW_ROOT" in
  */.*)
    echo "gemini: warn: the reviewed repo root '$REVIEW_ROOT' is under a hidden (dot) directory; agy will not add it as a workspace folder ('is hidden: ignore uri'), so the Gemini reviewer runs WITHOUT repo context (diff-only, no source grep). Review from a non-hidden checkout for full agy context." >&2
    ;;
esac

# Single source for "is $AGY_LOG a quota/429 exhaustion?" — used by both
# agy_fatal_reason (the degrade reason) and the model-ladder step-down
# gate, so the two can never drift (online R1: sourcery). Patterns pinned
# to agy's fatal-line shapes, not a bare "quota"/"429". grep reads the
# file directly (no `printf | grep -q` SIGPIPE under `set -o pipefail`).
agy_log_has_quota() {
  grep -qiE 'RESOURCE_EXHAUSTED|\(code 429\)|quota reached|quota exceeded|individual quota' "$AGY_LOG"
}

# On a degrade, surface WHY by scanning ONLY agy's --log-file — that is
# where agy actually writes its fatal backend errors. Do NOT scan $RAW:
# on the extract-fail path $RAW is the full model output, which quotes
# the reviewed diff, so any diff that merely mentions quota/429 code
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

FULL_PROMPT="$(cat)"

if [ -z "$FULL_PROMPT" ]; then
  echo "gemini: error: empty prompt on stdin" >&2
  exit 1
fi

if ! command -v agy >/dev/null 2>&1; then
  echo "gemini: degrade — flag '本轮缺 gemini' (agy not installed; the post-EOL replacement for the dead gemini CLI)" >&2
  exit 1
fi

# Reviewer discipline (recorded contract). `--sandbox` is not a write-hard
# guarantee, so prepend the no-modify/no-fix contract while preserving the
# user decision 2026-07-13 REVIEW-ONLY verification-command relaxation.
AGY_PROMPT="REVIEW ONLY — HARD CONSTRAINT. Do NOT modify, create, rename, or delete any file in the reviewed repo, and do NOT fix findings yourself. You MAY run read-only inspection and verification commands, including tests/builds and exercises with injected defects in a throwaway copy or fixture. Your ONLY output is your grounded prose review.

$FULL_PROMPT"

# agy keychain auth-race: per-attempt keychain warm + retry. The
# `security find-generic-password` warms the macOS Keychain item path
# so agy's 1s keyringAuth doesn't time out; redirect both streams and
# `|| true` so a missing `security` binary (non-macOS CI) is harmless.
# Capture agy's OWN exit code (G_RC) — a non-zero exit that still
# printed a salvageable JSON error body must STILL degrade, never slip
# through as a silent zero-finding approve.
# agy model-degradation ladder (the agy/Gemini leg's OWN fallback, not a
# new vendor). Preferred model = Gemini 3.5 Flash (agy default, empty
# --model). If a rung quota-exhausts (429), step DOWN to the next model
# so the leg still returns a third independent voice; only when EVERY
# rung is quota-exhausted does the agy leg step down entirely (degrade →
# 本轮缺 gemini). The fallback rung is `Claude Sonnet 4.6 (Thinking)` via
# agy — a SEPARATE quota bucket from agy's Gemini (verified: Gemini 429
# while agy-Claude still answers), and deliberately a DIFFERENT model
# from the squad's existing Claude leg (Opus 4.8) so it is a distinct
# voice, not a near-duplicate. (Cross-family is preferred, but Gemini is
# already quota-dead either way; a distinct 3rd read beats only two.)
# `AGY_MODEL` env overrides the ladder with one explicit model (manual /
# tests). The "no Google voice this round" caveat is flagged below.
# Single source for the fallback model name (online R1: sourcery) — change
# it here, not in the array / messages / tests.
AGY_FALLBACK_MODEL="Claude Sonnet 4.6 (Thinking)"
AGY_MODELS=("" "$AGY_FALLBACK_MODEL")
[ -n "${AGY_MODEL:-}" ] && AGY_MODELS=("$AGY_MODEL")
AGY_LADDER_LAST=$(( ${#AGY_MODELS[@]} - 1 ))

# `mi` MUST advance in lockstep with the outer for-iteration — ONLY the
# step-down `continue` below increments it; preserve that invariant if you
# ever add another outer-loop continue/break (Claude C2). AGY_STEPPED_DOWN
# records whether a quota step-down actually happened (vs a manual
# AGY_MODEL override), so the success-path note can word itself correctly.
RAW=""; G_RC=0; AGY_RAN_MODEL=""; AGY_STEPPED_DOWN=0; mi=0
for LADDER_MODEL in "${AGY_MODELS[@]}"; do
  # agy keychain auth-race: per-attempt keychain warm + retry (×4).
  for attempt in 1 2 3 4; do
    security find-generic-password -s "Antigravity Safe Storage" \
      >/dev/null 2>&1 || true

    # Truncate the shared log before each attempt so agy_fatal_reason
    # reflects ONLY the final attempt (online R1: sourcery).
    : > "$AGY_LOG"

    # One agy invocation; the optional --model is a guarded array so the
    # command line isn't duplicated (online R1: gemini). Outer-quoted
    # `"${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"}"` — the canonical form: empty
    # array → zero args (no stray empty arg), set → each element preserved
    # whole (the spaces in "Claude Sonnet 4.6 (Thinking)" stay one arg).
    # bash-3.2-safe under `set -u`; verified on 3.2.57 that this and the
    # unquoted form behave identically here, but the outer quotes are the
    # unambiguous idiom (online R3: gemini, defensive).
    MODEL_FLAG=()
    [ -n "$LADDER_MODEL" ] && MODEL_FLAG=(--model "$LADDER_MODEL")
    set +e
    RAW="$(cd "$REVIEW_ROOT" && agy --sandbox "${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"}" --print '' --print-timeout "$PRINT_TIMEOUT" --log-file "$AGY_LOG" 2>&1 <<<"$AGY_PROMPT")"
    G_RC=$?
    set -e

    if [ "$G_RC" -ne 0 ] && grep -qE "Authentication required|authentication timed out" <<<"$RAW"; then
      if [ "$attempt" -lt 4 ]; then
        echo "gemini: warn: agy auth-race on attempt $attempt/4, retrying..." >&2
        [ "${GEMINI_RETRY_WARM_SLEEP:-0}" != "0" ] && sleep "${GEMINI_RETRY_WARM_SLEEP}"
        continue
      fi
      echo "gemini: degrade — flag '本轮缺 gemini (auth race after retry×3)'" >&2
      exit 1
    fi
    break
  done
  AGY_RAN_MODEL="$LADDER_MODEL"

  # Quota on this rung + a lower rung exists → step the agy leg DOWN to
  # the next model (different voice) instead of degrading the whole leg.
  if [ "$mi" -lt "$AGY_LADDER_LAST" ] && agy_log_has_quota; then
    echo "gemini: warn: agy model '${LADDER_MODEL:-Gemini 3.5 Flash}' quota-exhausted → stepping down to next agy model" >&2
    AGY_STEPPED_DOWN=1
    mi=$(( mi + 1 ))
    continue
  fi
  break
done

if [ -z "$RAW" ]; then
  REASON="$(agy_fatal_reason)"
  echo "gemini: degrade — flag '本轮缺 gemini' (empty output, agy rc=$G_RC${REASON:+; $REASON})" >&2
  exit 1
fi

# Past the empty-output degrade above, RAW holds agy's review. Degrade
# — visibly, never silent — iff agy itself failed (G_RC≠0, a quota/crash
# non-auth-race exit) OR the FINAL ladder rung's log shows quota
# exhaustion; otherwise pass agy's review THROUGH VERBATIM for the
# orchestrator to read with judgment.
#
# The quota-log check is essential: the per-rung step-down only fires
# while a LOWER rung still exists, so the LAST rung's quota must be caught
# here — else an exhausted Gemini leg that exits 0 with a non-empty banner
# on stdout (RAW non-empty → the empty-output gate above is skipped) would
# be passed through as a real review (codex online R, P2). We key on the
# quota LOG (agy_log_has_quota) — the correct fatal signal — not on output
# format.
#
# We deliberately do NOT run extract_json / require a sentinel-JSON shape.
# Gemini's review is prose; the old sentinel gate treated any prose as
# "no findings JSON" and degraded it to 本轮缺 gemini — dropping a real
# review over format (the divergence from the wiki, which returns review
# text the agent reads). The degrade-reason scan still reads ONLY agy's
# --log-file (agy_fatal_reason), never $RAW, so a review body that quotes
# the diff's quota/429 code cannot mis-attribute a reason.
if [ "$G_RC" -ne 0 ] || agy_log_has_quota; then
  REASON="$(agy_fatal_reason)"
  echo "gemini: degrade — flag '本轮缺 gemini' (agy exit rc=$G_RC${REASON:+; $REASON}; agy's stderr is in the captured output per 2>&1)" >&2
  exit 1
fi

# Success with any non-Gemini/non-Google model → flag that this round has no
# Google voice. Gemini/Google is the only family that suppresses the flag;
# do not enumerate every possible non-Google vendor. Emitted ONLY here,
# after the round actually succeeds (not before the degrade gates, or it
# would falsely claim a 3rd voice on a degraded round — codex#1 R1).
# Word it by cause: quota step-down vs an explicit AGY_MODEL override.
case "$AGY_RAN_MODEL" in
  ""|*[Gg]emini*|*[Gg]oogle*) ;;
  *)
    if [ "$AGY_STEPPED_DOWN" -eq 1 ]; then
      echo "gemini: note: agy Gemini quota-exhausted → leg stepped down to '$AGY_RAN_MODEL' (separate quota). NO Google voice this round; the 3rd voice is agy-served Claude, distinct from the squad's Opus 4.8 leg." >&2
    else
      echo "gemini: note: agy ran the explicit AGY_MODEL override '$AGY_RAN_MODEL' (non-Google). NO Google voice this round; the 3rd voice is agy-served '$AGY_RAN_MODEL'." >&2
    fi
    ;;
esac
printf '%s\n' "$RAW"
