#!/usr/bin/env bash
# Gemini reviewer backend — calls `agy` (Antigravity CLI), the in-kind
# replacement for the `gemini` CLI that Google stopped serving
# 2026-06-18. agy is locked to Gemini 3.5 Flash — the wiki's explicit
# exception to the strongest-review-model rule, traded off to keep
# 3-vendor cross-family coverage.
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
#   AGY_MODEL                override the agy model-degradation ladder
#                            with ONE explicit model (manual / tests).
#                            Unset = the ladder: Gemini 3.5 Flash →
#                            (quota) Claude Sonnet 4.6 (Thinking) → (all
#                            quota) degrade. See the ladder block below.
#
# Hard rules (wiki §并行启动 / §agy auth callout):
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

PROTO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-doc}"
PRINT_TIMEOUT="${AGY_PRINT_TIMEOUT:-15m}"

# agy routes fatal backend errors (RESOURCE_EXHAUSTED / 429 quota, the
# agent-executor error line) to its --log-file, not to the captured
# stdout/stderr. (The keychain auth-race is the exception — it surfaces
# on stdout/stderr and is handled by the retry gate below, not here.)
# Give agy a private log so the degrade paths can name the real reason;
# clean it up on any exit.
AGY_LOG="$(mktemp "${TMPDIR:-/tmp}/agy-cmr.XXXXXX")"
trap 'rm -f "$AGY_LOG"' EXIT

# agy refuses to add a workspace folder whose path has a hidden (dot)
# component ("... is hidden: ignore uri" in its log) — so when cmr runs
# from e.g. a `.claude/worktrees/...` worktree, the Gemini reviewer gets
# NO repo context (it sees only the diff on stdin, cannot grep source).
# Warn (do not degrade — agy still reviews the diff), so the quality gap
# is visible and the user can rerun from a non-hidden path.
case "$PROTO_ROOT" in
  */.*)
    echo "gemini: warn: workspace root '$PROTO_ROOT' is under a hidden (dot) directory; agy will not add it as a workspace folder ('is hidden: ignore uri'), so the Gemini reviewer runs WITHOUT repo context (diff-only, no source grep). Run cmr from a non-hidden path for full agy context." >&2
    ;;
esac

# On a degrade, surface WHY by scanning ONLY agy's --log-file — that is
# where agy actually writes its fatal backend errors. Do NOT scan $RAW:
# on the extract-fail path $RAW is the full model output, which quotes
# the reviewed diff, so any diff that merely mentions quota/429 code
# would yield a false "quota exhausted" attribution (cross-model review
# R1: Claude C1 + codex#2 R1, live-reproduced). Patterns are pinned to
# agy's fatal-line shapes (not a bare "quota"/"429"). grep reads the
# file directly (no `printf | grep -q`, which can SIGPIPE under
# `set -o pipefail` on a large blob). Always returns 0 (empty = none).
agy_fatal_reason() {
  [ -s "$AGY_LOG" ] || return 0
  if grep -qiE 'RESOURCE_EXHAUSTED|\(code 429\)|quota reached|quota exceeded|individual quota' "$AGY_LOG"; then
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
AGY_MODELS=("" "Claude Sonnet 4.6 (Thinking)")
[ -n "${AGY_MODEL:-}" ] && AGY_MODELS=("$AGY_MODEL")
AGY_LADDER_LAST=$(( ${#AGY_MODELS[@]} - 1 ))

RAW=""; G_RC=0; AGY_RAN_MODEL=""; mi=0
for LADDER_MODEL in "${AGY_MODELS[@]}"; do
  # agy keychain auth-race: per-attempt keychain warm + retry (×4).
  for attempt in 1 2 3 4; do
    security find-generic-password -s "Antigravity Safe Storage" \
      >/dev/null 2>&1 || true

    # Truncate the shared log before each attempt so agy_fatal_reason
    # reflects ONLY the final attempt (online R1: sourcery).
    : > "$AGY_LOG"

    set +e
    if [ -n "$LADDER_MODEL" ]; then
      RAW="$(cd "$PROTO_ROOT" && agy --sandbox --model "$LADDER_MODEL" --print '' --print-timeout "$PRINT_TIMEOUT" --log-file "$AGY_LOG" 2>&1 <<<"$AGY_PROMPT")"
    else
      RAW="$(cd "$PROTO_ROOT" && agy --sandbox --print '' --print-timeout "$PRINT_TIMEOUT" --log-file "$AGY_LOG" 2>&1 <<<"$AGY_PROMPT")"
    fi
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
  AGY_RAN_MODEL="$LADDER_MODEL"

  # Quota on this rung + a lower rung exists → step the agy leg DOWN to
  # the next model (different voice) instead of degrading the whole leg.
  if [ "$mi" -lt "$AGY_LADDER_LAST" ] && \
     grep -qiE 'RESOURCE_EXHAUSTED|\(code 429\)|quota reached|quota exceeded|individual quota' "$AGY_LOG"; then
    echo "gemini: warn: agy model '${LADDER_MODEL:-Gemini 3.5 Flash}' quota-exhausted → stepping down to next agy model" >&2
    mi=$(( mi + 1 ))
    continue
  fi
  break
done

# When the agy leg ran a non-Gemini fallback model, this round has NO
# Google voice — the agy slot became a same-vendor-as-agy Claude fallback
# for a 3rd independent read. Flag it so the round report stays honest.
if [ -n "$RAW" ] && printf '%s' "$AGY_RAN_MODEL" | grep -qi 'claude'; then
  echo "gemini: note: agy leg ran fallback model '$AGY_RAN_MODEL' (agy Gemini quota-exhausted) — NO Google voice this round; the 3rd voice is agy-served Claude (separate quota), distinct from the squad's Opus 4.8 leg" >&2
fi

if [ -z "$RAW" ]; then
  REASON="$(agy_fatal_reason)"
  echo "gemini: degrade — flag '本轮缺 gemini' (empty output, agy rc=$G_RC${REASON:+; $REASON})" >&2
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
  REASON="$(agy_fatal_reason)"
  echo "gemini: degrade — flag '本轮缺 gemini' (extract_json rc=$EX_RC, agy exit rc=$G_RC${REASON:+; $REASON}; agy's stderr is in the captured output per 2>&1)" >&2
  printf '{"reviewer":"gemini","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi
printf '%s\n' "$EXTRACTED"
