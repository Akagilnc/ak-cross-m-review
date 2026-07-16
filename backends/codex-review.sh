#!/usr/bin/env bash
# Codex reviewer backend for /ak-cross-m-review.
#
# This is the DELIVERATELY-CORRECT codex invocation. It exists because the
# naive/uncorrected codex invocations use the two patterns
# recorded as confidence-10 footguns (D1/D2 in the analysis):
#
#   ❌ codex exec "$PROMPT" -C "$WORKDIR" -s read-only
#      - positional-arg prompt (stdin-pipe hang risk; off-convention)
#      - `-C` flag → runs in the wrong workdir (codex-wrong-repo-cwd)
#      - no `--model` → review quality drifts to the CLI default
#
#   ✅ cat <<'PROMPT' | codex exec --ephemeral \
#        -c model_reasoning_effort="medium" --model gpt-5.6-sol \
#        -o <last-message-file> - 2>&1
#      - stdin pipe (the `-` means "read prompt from stdin")
#      - `-o <file>` (--output-last-message): codex writes ONLY its final
#        message (the review candidates + verification) to
#        this file. We emit THAT, not stdout. `codex exec`'s stdout is the
#        task echo + reasoning trace; `-o` is codex's native "last message
#        only" output: concise, complete, and parser-free.
#      - `--ephemeral`: do NOT persist a session rollout file. CMR and other
#        callers may run Codex reviewers in parallel; without it instances
#        collide on ~/.codex/session → cross-talk (prompt A surfaces in
#        instance B's context). Recorded rule; evidence: codex#11435.
#      - `-c model_reasoning_effort=<effort>`: pass the effort in effect
#        EXPLICITLY so codex can't silently inherit ~/.codex/config.toml's
#        global value (a clone / other host could drift otherwise). This
#        pins the FORM, not the VALUE — default is medium when the caller
#        passes nothing, but any CMR_CODEX_EFFORT override (low/high/xhigh/…)
#        flows through verbatim. NOT a hard "must be medium" restriction.
#      - `--model gpt-5.6-sol`: the DEFAULT review model, passed explicitly
#        for the same anti-drift reason. Fully overridable via
#        CMR_CODEX_MODEL (e.g. luna) — the pin prevents silent drift, it
#        does not lock the value.
#      - NO `-C`: codex runs from the current dir (the repo root)
#      - always 2>&1 so a bounded native failure tail can be surfaced
#
# This file's ONLY job is avoiding codex invocation pitfalls (the correct
# invocation FORM). It imposes NO hard restriction on model or reasoning
# effort: default = gpt-5.6-sol + medium ONLY when the caller passes
# nothing; both are fully overridable (CMR_CODEX_MODEL / CMR_CODEX_EFFORT)
# and any override is passed through verbatim, never validated or rejected.
#
# Historical lineage (wiki sync cancelled 2026-07-13, ADR 0002):
#   wiki/concepts/cross-model-review.md  §调用规范 / §额外硬规则
#   wiki/concepts/codex-bot-conventions.md  §CLI 侧的正确 pattern / §模型变体
#
# Invocation:
#   <stdin: pinned review task; reviewer reads the clone>
#           | codex-review.sh <mode> [<label>]
#     mode  : doc | code   (review lens)
#     label : optional diagnostic tag (e.g. "full")
#
#   CMR_CODEX_MODEL   override review model (default: gpt-5.6-sol). Any
#                     value (e.g. luna) is passed through verbatim.
#   CMR_CODEX_EFFORT  override reasoning effort (default: medium). Any
#                     value (low/high/xhigh/…) is passed through verbatim
#                     to -c model_reasoning_effort=…; never validated or
#                     rejected. Mirrors CMR_CODEX_MODEL: default when unset,
#                     pass-through when set.
#   CMR_CODEX_TIMEOUT IDLE/silence seconds before pkill — kill only after
#                     this long with NO new stdout/stderr (a hang), NOT a
#                     total wall-clock cap. A codex still streaming its
#                     reasoning/trace runs as long as it needs. Default 900
#                     (= 15min, user decision 2026-07-06: an xhigh codex
#                     was false-killed at the 8min threshold too — deep
#                     reasoning / large diffs go silent for MANY minutes
#                     before the first token. Escalation history: 3min →
#                     8min → 15min. Wiki §额外硬规则 #4 updated to 15min
#                     the same day (vault b5495e8; historical note). Matches
#                     agy --print-timeout 15m).
#   CMR_CODEX_IDLE_POLL  watchdog poll interval seconds (default 5).
#   CMR_DRY_RUN=1     print the exact command that WOULD run to stderr, do
#                     not call codex, leave stdout empty, and exit 2. This
#                     is never a review leg; --selftest is a separate path.
#
# On success we emit codex's FINAL MESSAGE (the review — prose or JSON,
# from the `-o` file) to stdout; the orchestrator reads it with judgment
# (the recorded prose-review contract). Diagnostics to stderr. On timeout /
# non-zero codex exit / an empty final message: empty stdout + exit 1 + a
# stderr "本轮缺 codex" flag. Native failure output is surfaced as a bounded
# tail before that flag. The script does NOT parse
# findings or demand a sentinel-JSON format — that gate dropped codex's
# prose review as a phantom outage (removed in 0.3.9.0). It also does NOT
# tail-parse the verbose stdout — codex's own `-o` gives the clean last
# message directly.

set -euo pipefail

MODE="${1:-code}"
LABEL="${2:-full}"
if [ "${1:-}" != "--selftest" ]; then
  case "$MODE" in
    doc|code) ;;
    *)
      MODE="code"
      echo "codex-review: invalid MODE (expected doc|code) — degrade, flag '本轮缺 codex'" >&2
      exit 1
      ;;
  esac
fi
MODEL="${CMR_CODEX_MODEL:-gpt-5.6-sol}"
# IDLE/silence timeout — seconds with NO new output before we call it a hang
# and kill (NOT a total wall-clock cap). Default 900 = 15min (user decision
# 2026-07-06 after an 8min false-kill; wiki §额外硬规则 #4 updated to 15min
# the same day, historical note). A streaming codex is never killed for total
# runtime.
IDLE_TIMEOUT="${CMR_CODEX_TIMEOUT:-900}"
IDLE_POLL="${CMR_CODEX_IDLE_POLL:-5}"
# Reasoning effort: default medium when the caller passes nothing, else the
# caller's value passed through verbatim (low/high/xhigh/…) — NO whitelist,
# never validated or rejected (owner ruling 2026-07-12: this file's only job
# is avoiding codex pitfalls, not restricting model/effort). Symmetric with
# CMR_CODEX_MODEL above.
CMR_CODEX_EFFORT="${CMR_CODEX_EFFORT:-medium}"

if [ "${1:-}" != "--selftest" ]; then
  if ! [[ "$IDLE_TIMEOUT" =~ ^[1-9][0-9]*$ ]]; then
    echo "codex-review: invalid CMR_CODEX_TIMEOUT='$IDLE_TIMEOUT' (expected positive integer seconds) — degrade, flag '本轮缺 codex'" >&2
    exit 1
  fi
  if ! [[ "$IDLE_POLL" =~ ^[1-9][0-9]*$ ]]; then
    echo "codex-review: invalid CMR_CODEX_IDLE_POLL='$IDLE_POLL' (expected positive integer seconds) — degrade, flag '本轮缺 codex'" >&2
    exit 1
  fi
fi

# codex writes ONLY its final message (the review) here via
# `-o`/--output-last-message. We emit this file's contents on success, NOT
# codex's stdout (which is the task echo + reasoning trace). Created before
# CODEX_CMD so the array
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
# `-c model_reasoning_effort="$CMR_CODEX_EFFORT"` passes the effort in
# effect (default medium, or the caller's override) EXPLICITLY — codex
# inherits ~/.codex/config.toml's global value otherwise, so pinning it in
# the command prevents a clone / other machine from silently drifting. This
# passes whatever value is in effect; it does NOT lock the value to medium
# (the recorded reasoning-effort contract).
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
  # clone / other host can't inherit a config.toml value, per the recorded contract).
  # The effort is whatever's in effect (default medium, overridable via
  # CMR_CODEX_EFFORT) — the check interpolates ${CMR_CODEX_EFFORT} so it
  # pins the FORM not the VALUE, adapting to any override. A missing/altered
  # pin fails this single check (a separate guard would only double-report,
  # online R2: gemini).
  case "$CMD" in
    *"codex exec --ephemeral -c model_reasoning_effort=${CMR_CODEX_EFFORT} --model ${MODEL} -o "*) ;;
    *) echo "FAIL: command not canonical form ('codex exec --ephemeral -c model_reasoning_effort=${CMR_CODEX_EFFORT} --model X -o <file> -')" >&2; fail=1 ;;
  esac
  # -o/--output-last-message mandatory: it is how we get codex's clean
  # final review instead of the stdout task/trace stream (no -o → we'd have
  # nothing to emit on the success path).
  case "$CMD" in
    *" -o "*) ;;
    *) echo "FAIL: command missing -o/--output-last-message (last-message extraction)" >&2; fail=1 ;;
  esac
  # --ephemeral mandatory: parallel codex instances collide on
  # ~/.codex/session without it (recorded rule; evidence: codex#11435).
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
  # <effort> --model X -o <file> -), `codex exec` first, `-o` at [7], stdin
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

PROMPT_TMP="$(mktemp)"
TMP_OUT="$(mktemp)"
trap 'rm -f "$PROMPT_TMP" "$LASTMSG" "$TMP_OUT"' EXIT
cat > "$PROMPT_TMP"
if [ ! -s "$PROMPT_TMP" ]; then
  echo "codex-review: error: empty prompt on stdin" >&2
  exit 1
fi

if [ "${CMR_DRY_RUN:-0}" = "1" ]; then
  echo "codex-review: NON-REVIEW DRY_RUN — no Codex reviewer ran; 本轮缺 codex (NON-REVIEW DRY_RUN); command: printf %s \"\$PROMPT\" | ${CODEX_CMD[*]} 2>&1" >&2
  exit 2
fi

echo "codex-review: model=${MODEL} mode=${MODE} label=${LABEL} idle-timeout=${IDLE_TIMEOUT}s" >&2

# IDLE-based hang detection (recorded hard rule #4) — NOT a total wall-clock
# cap. A hang = codex produces NO new stdout/stderr for $IDLE_TIMEOUT
# seconds; a codex still streaming its reasoning/trace (deep reasoning +
# large diffs go silent for minutes before the first token, then stream)
# must NEVER be killed merely for taking long in total. We run codex in the
# background, capture combined output to a file, and watch that file's size:
# the watchdog kills ONLY after the size hasn't grown for $IDLE_TIMEOUT
# seconds. Pure bash (no `timeout(1)` total-cap dependency, works on every
# host). The kill is SCOPED to this codex + its children — never a global
# `pkill -f 'codex exec'`, which would take down sibling parallel codex
# reviewers and unrelated user runs. (The prompt always reaches codex via a
# temp file on stdin — `-` in CODEX_CMD; never a here-string into bash -c,
# the old bug that fed an empty prompt under GNU timeout.)
#
# Caveat: idle is measured by stdout/stderr GROWTH. If codex fully buffers
# stdout (no incremental flush) it could look idle while working; the 15min
# default is generous enough that any periodic flush keeps it alive, and
# codex exec streams its progress in practice.
"${CODEX_CMD[@]}" < "$PROMPT_TMP" > "$TMP_OUT" 2>&1 &
CODEX_PID=$!
TIMED_OUT=0
last_size=-1
idle=0
while kill -0 "$CODEX_PID" 2>/dev/null; do
  sleep "$IDLE_POLL"
  # The process can finish during this sleep. Do not count that final quiet
  # poll as idle time and label a successful exit as a timeout.
  if ! kill -0 "$CODEX_PID" 2>/dev/null; then
    break
  fi
  size=$(wc -c < "$TMP_OUT" 2>/dev/null || echo 0)
  if [ "$size" -eq "$last_size" ]; then
    idle=$(( idle + IDLE_POLL ))
  else
    idle=0
    last_size=$size
  fi
  if [ "$idle" -ge "$IDLE_TIMEOUT" ]; then
    TIMED_OUT=1
    echo "codex-review: no output for ${IDLE_TIMEOUT}s (idle/hang, not total time) — killing pid $CODEX_PID + children (scoped, not global)" >&2
    pkill -TERM -P "$CODEX_PID" 2>/dev/null || true
    kill  -TERM "$CODEX_PID" 2>/dev/null || true
    sleep 2
    pkill -KILL -P "$CODEX_PID" 2>/dev/null || true
    kill  -KILL "$CODEX_PID" 2>/dev/null || true
    break
  fi
done
set +e
wait "$CODEX_PID"
RC=$?
set -e
[ "$TIMED_OUT" -eq 1 ] && RC=124   # idle watchdog fired → force the degrade path

emit_native_output_tail() {
  [ -s "$TMP_OUT" ] || return 0
  echo "codex-review: native output tail (last 8192 bytes):" >&2
  # A byte tail can begin inside a multibyte character. Keep the same bounded
  # native tail, but discard invalid UTF-8 fragments such as that cut prefix.
  tail -c 8192 "$TMP_OUT" | iconv -c -f UTF-8 -t UTF-8 >&2 || true
  echo >&2
}

# Outage signals, in order. We emit codex's FINAL MESSAGE (the `-o`
# file) on success — not the full stdout echo+trace. On failure, only a
# bounded native-output tail is surfaced. Three true-outage cases degrade:
#
#  1. idle/hang kill (rc 124 = our idle watchdog; 137/143 = SIGKILL/TERM)
#     — a partial -o file from a killed codex must NEVER count as a review.
#  2. codex exited non-zero for any native CLI/model/service reason. rc is the clean,
#     content-independent outage signal; we do NOT grep the body for
#     auth/quota/429 — a real prose review legitimately discusses those as
#     defect categories (it self-degraded on this repo once).
#  3. rc=0 but the -o final-message file is empty — codex produced only a
#     trace, or `-o` is unsupported. An empty review must not slip through
#     as a silent zero-finding approve.
#
# We do NOT parse findings or require a sentinel-JSON shape (that gate
# dropped codex's prose as a phantom outage, removed 0.3.9.0), and we do
# NOT parse stdout as a review — codex's own `-o` gives the clean last message.
case "$RC" in
  124|137|143)
    emit_native_output_tail
    echo "codex-review: timeout/kill (rc=$RC) — degrade, flag '本轮缺 codex'" >&2
    exit 1
    ;;
esac
if [ "$RC" -ne 0 ]; then
  emit_native_output_tail
  echo "codex-review: codex exited non-zero (rc=$RC; not a review) — degrade, flag '本轮缺 codex'" >&2
  exit 1
fi

REVIEW="$(cat "$LASTMSG" 2>/dev/null || true)"
if [ -z "$REVIEW" ]; then
  emit_native_output_tail
  echo "codex-review: codex exited 0 but wrote no final message (empty -o file; only a trace, or -o unsupported) — degrade, flag '本轮缺 codex'" >&2
  exit 1
fi
printf '%s\n' "$REVIEW"
