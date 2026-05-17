---
name: cross-model-review
description: Local pre-PR cross-model review, main-session-orchestrated. Dispatches the v3 vendor squad — N codex gpt-5.5 + 1 Claude opus Agent + 1 Gemini = N+1+1 — in a single parallel message against a diff, merges findings with consensus severity upgrade + grounding-density floor boost, runs a deterministic drift/termination check, proposes a fixer diff per round with the defer protocol, and loops to N/N concur or an architectural stop. Use every dev cycle before ship — this is wiki Step 2.4 / 2.6, the part sessions repeatedly get wrong.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
  - TodoWrite
---

# /cross-model-review — v3 vendor-squad pre-PR review

This skill is the executable form of
`~/WorkSpace/vault/ak-cc-wiki/wiki/concepts/cross-model-review.md`
(Step 2.4 / 2.6 of `tdd-autonomous-dev`). The wiki is the source of
truth; this file transcribes its **hard rules** into a loop so every
session runs it the same way instead of re-deciding by feel.

Shared library lives in the grounded-review proto repo:
`PROTO_ROOT="$HOME/WorkSpace/gstack-grounded-review-proto"` — reuses
`lib/merge.py` (consensus), `lib/extract_json.py` (robust parse),
`lib/drift.py` (deterministic drift/termination). Codex runs through
`cross-model-review/backends/codex-review.sh` (the corrected
invocation — see Tier-0 rules).

---

## Tier-0 hard rules (violating any of these = wrong, full stop)

> **Rule 0 — main-session-orchestrated only (the capability law).**
> This skill MUST run in the main session. Do NOT invoke it from inside
> a subagent: Step 2a spawns the Claude reviewer via the `Agent` tool,
> and Claude Code does not expose `Agent` to subagents (anti-recursion).
> A slice may be *implemented* by a subagent, but its
> post-baseline-commit per-slice review AND the all-slices-done ship-pre
> review are BOTH run here, by the main session, as **N+1+1**. The old
> "subagent runs its own 1+1 internally" model is **deprecated** — it
> was based on a wrong capability assumption (nested `Agent` simply does
> not start); do not implement or expect it.
> (wiki cross-model-review.md §N 取值表 callout, 2026-05-17 能力修正.)

1. **Single-message parallel spawn.** Every reviewer tool call for a
   round goes out in ONE assistant message. Never "send some, wait,
   send the rest". Never one tool call per message.
2. **Codex only via `backends/codex-review.sh`.** Never call `codex exec`
   directly from this loop. The backend pins the correct form:
   `printf %s "$PROMPT" | codex exec --model gpt-5.5 - 2>&1`.
   Never `-C`. Never a positional-arg prompt. Never a dev-tier model
   (`gpt-5.3-codex-spark`/`gpt-5.3-codex`) for review.
3. **Claude reviewer = Agent subagent, model `opus`, full diff, spawned
   BY THE MAIN SESSION (Rule 0).** Never the headless `claude -p` path
   (rate-limit + 25min timeout footgun).
4. **Gemini = `backends/gemini.sh` (auto_edit + retry).** Never
   `--approval-mode plan` (blocks tools → weak findings).
5. **Every external call `2>&1`. Run from the repo root. No `-C`.**
6. **`concur ≠ done`.** N/N concur means "the correctness lens is
   exhausted, proceed to the next gate" — NOT "ship-ready". Coverage
   audit / specialist / ship Red Team are different lenses and are not
   skippable downstream. (`gate-lens-heterogeneity`.)
7. **Defer protocol is mandatory.** A finding is either fixed or
   deferred-with-all-three-parts. Never re-rank P1→P2 to escape the loop.
8. **Drift verdict is computed, not felt.** Use `lib/drift.py`. When it
   says `stop_reground`, stop — do not "try one more round".

---

## Step 0 — args + env

> Precondition (Rule 0): you are the **main session**. If you are a
> subagent, stop now and return to the orchestrator — you cannot spawn
> the Claude reviewer, so this loop cannot run here.

Invocation:

```
/cross-model-review [--base BRANCH] [--range A..B] [--diff FILE]
                    [--mode doc|code|auto] [--rounds N]
                    [--scenario per-slice|ship-pre]
```

- `--base` — base branch for the cumulative diff. Default: `main`
  (fallback `master`).
- `--range` — explicit `A..B` commit range (e.g. a single slice's
  commits). Overrides `--base`.
- `--diff` — review a pre-computed diff file instead of computing one.
- `--mode` — `auto` (default): `doc` if the diff is >70% `.md`, else
  `code`.
- `--rounds` — max reviewer→fixer iterations. Default `3` (the wiki
  3-round cap; round 4 is reviewer-taste, not value).
- `--scenario` — `ship-pre` (default; cross-slice cumulative diff vs
  base) or `per-slice` (one slice's range, within-slice lens). Affects
  only the reviewer-prompt emphasis line.

```bash
PROTO_ROOT="$HOME/WorkSpace/gstack-grounded-review-proto"
CMR="$PROTO_ROOT/cross-model-review"
for bin in claude codex gemini python3 jq git; do
  command -v "$bin" >/dev/null 2>&1 || { echo "missing: $bin" >&2; exit 2; }
done
python3 "$PROTO_ROOT/lib/merge.py" --selftest >/dev/null && \
python3 "$PROTO_ROOT/lib/drift.py" --selftest >/dev/null && \
bash "$CMR/backends/codex-review.sh" --selftest >/dev/null && \
echo "env + lib selftests OK"
```

If any selftest fails, stop and report — the loop's determinism depends
on them.

---

## Step 1 — build the diff + size it

```bash
# Defaults FIRST — these flags are optional and the orchestrator may run
# under `set -u`; referencing them unset would abort before the diff is
# even built. SCENARIO default is ship-pre (wiki Step 2.6).
BASE="${BASE:-main}"; DIFF_FILE="${DIFF_FILE:-}"; RANGE="${RANGE:-}"
SCENARIO="${SCENARIO:-ship-pre}"
git rev-parse --verify "$BASE" >/dev/null 2>&1 || BASE=master
RUN_DIR="$PROTO_ROOT/outputs/cmr-$(date +%Y%m%d-%H%M%S)"; mkdir -p "$RUN_DIR"

if   [ -n "$DIFF_FILE" ]; then cp "$DIFF_FILE" "$RUN_DIR/change.diff"
elif [ -n "$RANGE" ];     then git diff "$RANGE"            > "$RUN_DIR/change.diff"
else                            git diff "$BASE"...HEAD     > "$RUN_DIR/change.diff"
fi

# `grep -c` prints "0" AND exits 1 on no match. `|| echo 0` would APPEND
# a second line → LINES="0\n0" → the numeric N-table compare blows up on
# an empty / binary-only / pure-rename diff. Swallow the exit, don't
# append; then floor with parameter expansion.
LINES=$(grep -cE '^[+-]' "$RUN_DIR/change.diff" || true);          LINES=${LINES:-0}
SECTIONS=$(grep -cE '^diff --git' "$RUN_DIR/change.diff" || true); SECTIONS=${SECTIONS:-0}
[ "${SECTIONS:-0}" -eq 0 ] 2>/dev/null && SECTIONS=1
echo "diff: $LINES changed lines across $SECTIONS file-sections"
```

**N table.** Canonical notation is **N+1+1** = N codex + 1 Claude Agent
+ 1 Gemini (wiki "统一记法 N+1+1"; N=1 ⇒ 1+1+1). Only codex instantiates
by diff size; Claude & Gemini are always ×1 on the full diff:

| changed lines | setup (N+1+1) | codex N | reviewer total |
|---------------|---------------|---------|----------------|
| < 200         | 1+1+1         | 1       | 3              |
| 200–500       | 2+1+1         | 2       | 4              |
| 500+          | 3+1+1         | 3       | 5              |

> **Small-diff exception** (typo / copy, < 50 changed lines): run 1+1
> (Claude subagent + codex only), and you MUST annotate the eventual
> commit message `"小 diff 例外，跑 1+1 不跑 v3 default"`. Silent
> degrade is an anti-pattern.

Compose the reviewer prompt once:

```bash
EMPHASIS="FULL DIFF — prioritize cross-section / cross-slice consistency."
[ "$SCENARIO" = "per-slice" ] && EMPHASIS="FULL DIFF — within-slice lens: local logic, edge cases, test coverage of changed branches."
build_prompt() {  # $1 = view header
  printf '%s\n\nVIEW: %s\n\n--- BEGIN DIFF ---\n' "$(cat "$CMR/prompts/cmr-reviewer.md")" "$1"
  cat "$RUN_DIR/change.diff"
  printf '\n--- END DIFF ---\nReturn JSON only. No markdown wrapper.\n'
}
```

For N≥2, codex section k gets `VIEW: SECTION k/N` and a diff sliced to
its file-sections (split `change.diff` on `^diff --git` into N roughly
equal groups, write `$RUN_DIR/codex-sec-k.diff`). Claude & Gemini always
get `VIEW: FULL DIFF`.

---

## Step 2 — round loop (1..ROUNDS)

Track rounds with TodoWrite.

### 2a — Tier-0 parallel dispatch (ONE message, all reviewers)

This is the **N+1+1** spawn and it happens here, in the main session
(Rule 0). The `Agent` tool below only works because you are the main
session — that is the whole reason this loop is not delegated.

`ROUND_DIR="$RUN_DIR/round-$N"; mkdir -p "$ROUND_DIR"`

In a **single assistant message**, emit all of:

- **1 × Agent tool** — Claude reviewer:
  - `description`: `"cmr claude reviewer round N"`
  - `model`: `opus`
  - `prompt`: full-diff reviewer prompt (`build_prompt "FULL DIFF ..."`).
  - After it returns, write its text to `$ROUND_DIR/claude.raw` and:
    `python3 "$PROTO_ROOT/lib/extract_json.py" claude "$MODE" < "$ROUND_DIR/claude.raw" > "$ROUND_DIR/claude.json"`
- **N × Bash tool** — codex reviewer(s), one per section (N=1 → full):
  ```bash
  printf '%s' "$CODEX_PROMPT_k" \
    | "$CMR/backends/codex-review.sh" "$MODE" "section-$k-of-$NCODEX" \
    > "$ROUND_DIR/codex-$k.json" 2> "$ROUND_DIR/codex-$k.err"
  ```
- **1 × Bash tool** — Gemini reviewer (full diff):
  ```bash
  printf '%s' "$GEMINI_PROMPT" \
    | "$PROTO_ROOT/backends/gemini.sh" "$MODE" \
    > "$ROUND_DIR/gemini.json" 2> "$ROUND_DIR/gemini.err"
  ```

Total tool calls = `1 (Agent) + N (codex Bash) + 1 (gemini Bash)`. Do
NOT split across messages. Do NOT await one before sending the next.

### 2b — vendor-degradation check, then merge

A backend that emits the synthetic `{"...","findings":[]}` + nonzero
exit = that vendor is **down this round**. Apply the matrix and **flag
explicitly in the round report** (never silent-degrade):

| down            | continue with         | flag                                  |
|-----------------|-----------------------|----------------------------------------|
| codex (all)     | Claude + Gemini       | "本轮缺 codex"                          |
| gemini          | Claude + Codex        | "本轮缺 gemini"                         |
| 1 of N codex    | Claude + (N-1) + Gem  | "codex 实例 N→N-1"                      |
| 2 vendors down  | single vendor         | "本轮无 outside voice — 需人工补 review" |

Merge every reviewer JSON that exists (variable N — `merge.py` dedups by
vendor, so split-by-section codex correctly collapses to one "codex"
vote, not N votes). `merge.py` applies two independent trust axes per the
wiki: **concur** (horizontal — cross-vendor consensus → severity upgrade)
and **grounding density** (vertical — count of real tool calls in a
finding's `verification` → severity floor boost, only-up). A
well-grounded single-vendor finding is not automatically weak. (wiki
"grounding 密度 = 信任权重"; thresholds are proto-calibrated constants,
not portable — the portable rule is just "grounding density is a trust
weight".)

Each backend in 2a MUST record its exit status so degradation is
detectable (a degraded backend emits the same `findings: []` shape as a
clean approve — only the exit code distinguishes them). After each
backend call write its rc, e.g. `echo $? > "$ROUND_DIR/codex-$k.rc"`
(Claude reviewer: rc 0 only if the subagent returned parseable findings
JSON). Then merge and compute how many distinct vendors actually ran:

```bash
python3 "$PROTO_ROOT/lib/merge.py" \
  "$ROUND_DIR"/claude.json "$ROUND_DIR"/codex-*.json "$ROUND_DIR"/gemini.json \
  > "$ROUND_DIR/merged.json"
jq -r '"merged: \(.merged_findings|length) (\(.stats.by_severity))"' "$ROUND_DIR/merged.json"

# Active = vendors with at least one non-degraded (rc 0) run this round.
av=0
[ "$(cat "$ROUND_DIR/claude.rc" 2>/dev/null)" = 0 ] && av=$((av+1))
ls "$ROUND_DIR"/codex-*.rc >/dev/null 2>&1 && grep -qx 0 "$ROUND_DIR"/codex-*.rc 2>/dev/null && av=$((av+1))
[ "$(cat "$ROUND_DIR/gemini.rc" 2>/dev/null)" = 0 ] && av=$((av+1))
echo "$av" > "$ROUND_DIR/active_vendors"
echo "active vendors this round: $av"
```

### 2c — present findings

≤30 lines: total + by-severity; enumerate only `critical`/`high`
(`merged_id`, `category`, `reviewer_count`, first `claim_quote`); count
only for the rest. Full detail stays in `merged.json`.

### 2d — drift + termination (computed verdict drives the loop)

Round dirs MUST be passed in **numeric** order — a bare `round-*` glob
sorts lexically (`round-1, round-10, round-2`), so with ≥10 rounds
drift.py (which treats the last argv as "latest") would judge the wrong
round. Pass the active-vendor count so a degraded zero-finding round
cannot read as concur (drift.py cannot infer degradation from
merged.json — same `findings: []` shape as a clean approve):

```bash
# bash 3.2 safe (macOS /bin/bash has NO `mapfile`). Sort on the round
# integer extracted from `round-N`, NOT on the RUN_DIR path: RUN_DIR is
# `outputs/cmr-YYYYMMDD-HHMMSS/...`, so a path-keyed numeric sort keys
# on the date (identical for every round) and stays lexical
# (round-10 before round-2). Extract N, sort numeric, rebuild paths.
RD=()
while IFS= read -r _d; do RD+=("$_d/merged.json"); done < <(
  for _r in "$RUN_DIR"/round-*/; do
    _n=${_r%/}; _n=${_n##*/round-}
    printf '%s\t%s\n' "$_n" "${_r%/}"
  done | sort -n -k1,1 | cut -f2-
)
AV=$(cat "$ROUND_DIR/active_vendors" 2>/dev/null || echo 2)
python3 "$PROTO_ROOT/lib/drift.py" --active-vendors "$AV" \
  "${RD[@]}" > "$ROUND_DIR/drift.json"
DRIFT_RC=$?
jq -r '.verdict + " / " + .action + " — " + .explain' "$ROUND_DIR/drift.json"
```

`drift.py` exits 3 on `input_error` (every round file missing/invalid —
a glob typo or failed merge, NOT a benign tick). If `DRIFT_RC` is 3,
STOP and report the broken pipeline; do not proceed as if converging.

Act on `.action`:

| action                   | do                                                                                                |
|--------------------------|---------------------------------------------------------------------------------------------------|
| `stop_converged`         | positive termination. Print the **concur ≠ done** reminder (rule 6). Go to Step 3.                 |
| `need_more_rounds`       | 1 round so far / latest non-empty / **degraded round** (`degraded_inconclusive`: 0 findings but <2 vendors ran — flag "需人工补 review / 等 vendor 恢复", do NOT treat as concur). Proceed to fixer only if there are findings; if degraded, re-run reviewers next round (recover the vendor) instead. |
| `continue`               | converging — proceed to fixer (2e).                                                               |
| `centralize_then_continue` | coverage drift (not architectural). Tell the fixer to **centralize the repeated rule into one referenced place** rather than re-inlining; proceed to fixer. |
| `stop_reground`          | architectural drift **or** `input_error` (broken input pipeline). STOP the loop. Report per wiki §例外 (b)/(c): which triggers fired, recommend implementation/architecture-level rework (or fix the pipeline). Do NOT fix-and-retry. |

Also: if `N == ROUNDS` and not converged → stop after this round;
remaining `critical`/`high` is a hard problem (report it), remaining
`medium`/`low`/`clarity` → defer protocol.

Single-vendor-only rounds never count as `stop_converged` even if
findings hit zero — flag "需人工补 review / 等 vendor 恢复".

### 2e — fixer (subagent, proposes a diff + deferrals)

Dispatch via **Agent tool**, `model` = `${CMR_FIXER_MODEL:-sonnet}`.
The fixer MUST NOT use Edit/Write — it only returns JSON.

```
Agent:
  description: "cmr fixer round N"
  model: <sonnet|opus from env>
  prompt: |
    IMPORTANT: Do NOT use Edit or Write. Return JSON only with a "diff"
    and a "deferred" array. The caller applies the diff with git apply.
    You may use Read/Grep to locate claim_quotes and sweep related sites.

    {contents of cross-model-review/prompts/cmr-fixer.md}

    --- MERGED FINDINGS ---
    {contents of $ROUND_DIR/merged.json}
    --- END ---

    Diff target root: <repo root>. Findings reference real files in the
    working tree — Read them to produce a correct unified diff.
```

`python3 "$PROTO_ROOT/lib/extract_json.py" claude "$MODE" < fixer.raw > "$ROUND_DIR/fixer.json"`

### 2f — check the diff (git apply, multi-file safe)

Do **not** use `lib/apply_diff.py` here — it basename-normalizes paths
(correct for grounded-review's single file, wrong for a multi-file
cross-slice diff). Apply with git directly; git itself is the backup
(reversible on a branch):

```bash
jq -r '.diff' "$ROUND_DIR/fixer.json" > "$ROUND_DIR/fixer.diff"
if [ ! -s "$ROUND_DIR/fixer.diff" ] || [ "$(cat "$ROUND_DIR/fixer.diff")" = "null" ]; then
  echo "fixer produced no diff this round"
else
  git apply --check "$ROUND_DIR/fixer.diff" 2>"$ROUND_DIR/apply.err" \
    && echo "diff applies cleanly" \
    || { echo "diff does NOT apply:"; cat "$ROUND_DIR/apply.err"; }
fi
```

### 2g — approve (AskUserQuestion)

Show: fixes_applied / fixes_skipped / deferred counts, the diff, and the
`git apply --check` result. Options:

- **A) apply + continue** to round N+1
- **B) skip apply, continue** (re-review same content next round)
- **C) stop here** (leave tree unchanged)

### 2h — apply + persist deferrals

If A and the diff checked clean:

```bash
git apply "$ROUND_DIR/fixer.diff"
echo "applied round $N — reversible via: git checkout -- . / git stash"
```

Persist every `deferred[]` entry (defer protocol). If a PR exists
(`gh pr view` succeeds) append/update its body's `## Deferred Findings`
section; else write/append `DEFERRED.md` at the repo root:

```
- [ ] [<severity>] <summary> — <rationale> — <expected_timing>
```

Then loop to round N+1.

---

## Step 3 — final report

```
CROSS-MODEL REVIEW COMPLETE
===========================
scenario:     ship-pre | per-slice
setup:        N+1+1  (codex N=<n>)   [small-diff exception: <yes/no>]
rounds:       <r> / <ROUNDS>
termination:  converged (N/N concur) | architectural_drift(<triggers>)
              | round-budget
vendor flags: <none | 本轮缺 codex | ...>
fixes:        <applied> across <r> rounds
deferred:     <count>  (see PR ## Deferred Findings / DEFERRED.md)
artifacts:    <RUN_DIR>
```

If converged, end with the gate-lens reminder verbatim:

> concur ≠ done. The correctness lens is exhausted. Coverage audit,
> domain specialist, and ship Red Team are different lenses and are
> still required downstream — do not read this as ship-ready.

If `architectural_drift`: do not present a tidy "done" — present the
drift triggers and the implementation/architecture rework recommendation
(wiki §例外 (b)/(c)). If `critical`/`high` remain at budget: flag the
file/change as still broken.

---

## Anti-patterns (wiki §反模式 — refuse these)

1. Serial reviewer launch (send some, await, send rest) — defeats parallelism.
2. N codex all on the full diff — duplicate findings, no coverage gain (N≥2 ⇒ split sections).
3. Self-scan instead of an independent subagent — author bias, high miss rate.
4. Same-family different-size as "outside voice" (Opus main + Sonnet outside) — not cross-vendor.
5. Hardcoded N=3 ignoring diff size — tiny wastes, large under-covers.
6. Drift hit → "one more round" rationalize — that is the infinite-loop entrance.
7. Silent vendor degrade — always flag "本轮缺 X".
8. Dev-tier model as reviewer — review must be `opus` / `gpt-5.5` / strongest Gemini.
9. Reading `~/.claude/.credentials.json` / `ANTHROPIC_API_KEY` to judge Claude — false negative; only the Agent subagent path is used here so this does not arise.
10. Treating N/N concur as ship-ready — category error (rule 6).

## Non-goals / boundary

- This is **Layer 1** (local, pre-PR). It does not replace Layer 3
  (`pr-review-loop`, the post-push bot review) or the ship Red Team.
- It does not commit, push, or open a PR (the caller / `gstack-ship`
  does). It only edits the working tree on the current branch.
- Content PRs with user-facing fact claims (dates/names/stats/security
  claims) must pass `content-fact-gate` / `/grounded-review` FIRST —
  cross-model reviewers share training bias and rubber-stamp shared
  hallucinations; this lens cannot catch that.
- One change set per invocation.

## Invocation examples

```
/cross-model-review                              # ship-pre, diff vs main, 3 rounds
/cross-model-review --range HEAD~3..HEAD --scenario per-slice
/cross-model-review --base develop --rounds 2
/cross-model-review --diff /tmp/change.diff --mode code
```
