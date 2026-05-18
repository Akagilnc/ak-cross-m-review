---
name: ak-cross-m-review
description: Local pre-PR cross-model review — the executable form of the wiki's cross-model-review.md (tdd-autonomous-dev spine step 4 per-slice / step 5 ship-pre, Layer 1). Dispatches the v3 vendor squad (1 Claude opus Agent + N codex gpt-5.5 + 1 Gemini = N+1+1, N by diff size) in ONE parallel message against a diff, then merge / grade / drift-check / loop as the agent judgment the wiki prescribes. Use every dev cycle before a PR, so the agent runs the wiki step the same way instead of re-deciding by feel.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
  - TodoWrite
---

# /ak-cross-m-review — wiki cross-model-review, executable

This skill is a faithful, compact transcription of the **single source
of truth**:
`~/WorkSpace/vault/ak-cc-wiki/wiki/concepts/cross-model-review.md`
(setup / invocation / termination / drift live there; defer + cross-slice
discipline in `tdd-autonomous-dev.md` §切片内纪律). The wiki frames
merge / grade / drift / termination as **agent judgment**, not a
deterministic engine — this file keeps it that way. If this file and the
wiki ever disagree, the wiki wins; re-sync, do not fork behavior.

It is **Layer 1** (local, pre-PR). It does not replace Layer 3
(`pr-review-loop`). It does not commit / push / open a PR — the caller
(or `gstack-ship`) does. One change set per invocation.

## Step 0 — scenario, scope, pre-flight

Invocation:

```
/ak-cross-m-review [--base BRANCH] [--range A..B] [--diff FILE]
                    [--scenario per-slice|ship-pre]
```

- **`per-slice`** (tdd spine step 4, after a slice's baseline commit) —
  within-slice lens: local logic / naming / test coverage / single-slice
  spec-impl consistency. Scope = that slice's commit range.
- **`ship-pre`** (tdd spine step 5, all slices done) — cross-slice lens:
  cross-slice spec-impl contradictions / shared type & interface
  invariants / global logic after merge. Scope = whole-PR cumulative
  diff vs base (default `main`, fallback `master`).

Build the reviewed diff with plain git (`git diff <base>...HEAD`, or
`git diff <range>`, or the `--diff` file). No diff state machine — it is
just the change under review for this round.

Pre-flight gates (wiki §操作规程 / §边界):

- **Content PR with user-facing fact claims** (dates / names / orgs /
  stats / security): run `content-fact-gate` FIRST. Cross-model
  reviewers share training-data bias and rubber-stamp shared
  hallucinations; this lens cannot catch that.
- **Small diff** (typo / copy, < 50 changed lines): explicit exception —
  run **1+1** (Claude Agent + codex, cross-family) instead of the v3
  default, and you MUST annotate the eventual commit message
  `"小 diff 例外，跑 1+1 不跑 v3 default"`. Silent degrade is an
  anti-pattern.

## Step 1 — setup (v3 N+1+1) + the N table

Default **1+1+1**: 1 × Claude opus-4.7 (Agent subagent, full diff) +
1 × codex `gpt-5.5` + 1 × Gemini strongest review model, **all full
diff**. Only codex instantiates by diff size; Claude & Gemini are always
×1 on the full diff.

| Diff size | codex N | total reviewers | lens split |
|---|---|---|---|
| Small/Tiny (< 200 lines / 1 section) | 1 | 3 (1+1+1) | all three full diff |
| Medium (200–500 / 2 sections) | 2 | 4 (1+2+1) | 2 codex split 1/2 within-section; Claude+Gemini full |
| Large (500+ / 3+ sections) | 3 | 5 (1+3+1) | 3 codex split 1/3 within-section; Claude+Gemini full |

**Strongest review model only** — Anthropic `claude opus-4.7`, OpenAI
`gpt-5.5`, Google strongest review Gemini. **Never** dev-tier
`gpt-5.3-codex-spark` / `claude sonnet-4.6` as a reviewer (coding-tier
model choice is a separate matter; do not carry it into review).

> Orchestration law: cross-model review is ALWAYS run by the **main
> session**. There is no "subagent runs review internally" — a subagent
> cannot spawn the Claude reviewer (Claude Code does not expose `Agent`
> to subagents). A slice may be *implemented* by a subagent, but its
> per-slice review and the ship-pre review are both run here, by the
> main session, as N+1+1.

## Step 2 — parallel launch (operational HARD RULE)

Emit **every reviewer tool call in ONE assistant message**:

- Default 1+1+1 → 3 tool calls: 1 × `Agent` (Claude opus, full diff) +
  1 × `Bash` (`backends/codex-review.sh`) + 1 × `Bash`
  (`backends/gemini.sh`).
- Upgraded N codex → N+2 tool calls: 1 × `Agent` + N × `Bash` codex
  (section k/N, non-overlapping diff slices) + 1 × `Bash` gemini (full).

**Forbidden:** sending some and awaiting before sending the rest; one
tool call per message. Serial launch defeats the entire point.

Invocation forms (wiki §调用规范, from `codex-bot-conventions`):

- **Codex** — only via `backends/codex-review.sh` (pins
  `printf %s "$PROMPT" | codex exec --model gpt-5.5 - 2>&1`). Never
  `codex exec "$(...)"` (hangs → pkill), never `-C <dir>` (wrong
  workdir), never `codex review --base B "PROMPT"` (can't pass both).
- **Gemini** — only via `backends/gemini.sh` (`gemini --approval-mode
  auto_edit`, never `--approval-mode plan` — plan blocks tools → weak
  findings).
- **Claude reviewer** — the `Agent` tool, model `opus`, full-diff
  reviewer prompt. Never the headless `claude -p` path here.
- Always `2>&1`. Run from the repo root, no `-C`. Hang = >3min no
  output → `pkill -f codex` → next priority. rate / quota / limit →
  degrade immediately, do not retry.

`backends/codex-review.sh` salvages the findings JSON from noisy CLI
stdout via `lib/extract_json.py` and degrades cleanly (synthetic empty
findings + nonzero exit) on timeout / auth / quota so a failed vendor
is detectable, never a silent zero-finding pass.

Prompt templates: feed every reviewer `prompts/cmr-reviewer.md` + the
diff; the fixer (Step 7) uses `prompts/cmr-fixer.md` (the 3-part defer
protocol). They are templates, not control logic — adjust the lens line
per scenario (per-slice vs ship-pre).

## Step 3 — degradation (never silent)

v3 requires all 3 vendors. If one is unavailable, run with the rest and
**flag explicitly in the round report** — never silent-degrade to 1+1.

| Down (main = Claude) | Continue with | Flag |
|---|---|---|
| codex (all) | Claude + Gemini | "本轮缺 codex" |
| gemini | Claude + codex | "本轮缺 gemini" |
| 1 of N codex | Claude + (N−1) codex + Gemini | "codex 实例 N→N−1" |
| codex + gemini both | Claude only (fallback, no outside voice) | "本轮无 outside voice — 需人工补 review" |

(Main = Codex variant + the Claude-auth live-smoke rule:
`printf 'Return exactly: CLAUDE_OK\n' | claude -p --output-format json
--disable-slash-commands --tools ""` — never file/env auth checks. See
wiki §降级链.)

## Step 4 — merge + grade (agent judgment, not a deterministic engine)

Collect every reviewer's findings (use `lib/extract_json.py` to pull the
JSON out of each CLI's stdout). Then, as judgment:

- Group findings that describe the same issue across reviewers.
- Grade each P0 / P1 / P2 / P3 / P4.
- **Concurrence = horizontal trust**: the more independent vendors
  raised it, the higher confidence → severity upgrade.
- **Grounding density = vertical trust**: a finding whose `verification`
  shows real tool calls (rg / python / Read / `--help` …) is
  structurally more credible than pure reasoning; give a well-grounded
  single-reviewer finding a severity floor boost (only up). Two
  independent axes — do not read concurrence alone.

The wiki is explicit that any numeric thresholds are proto-calibrated
constants, **not portable**. The portable rules are exactly the two
sentences above. Do not re-import a deterministic merge engine.

Present ≤30 lines: total + by-severity; enumerate only P0/P1 (id,
category, reviewer count, first claim quote); count the rest.

## Step 5 — termination signals (wiki §终止信号)

> **concur ≠ done.** The concur thresholds below mean "the
> code+spec-correctness lens is exhausted, proceed to the next gate" —
> NOT "ship-ready". Downstream ship gates (coverage / specialist / Red
> Team) are different lenses and are not skippable. Reading concur as
> ship-ready is a category error.

**Positive termination (may proceed to next step):**
- v3 default: **3/3 concur** (all reviewers approve).
- Upgraded 1+N+1, 3 vendors present: **(N+2)/(N+2) concur**.
- One vendor degraded (1+1+1 → 2 reviewers): **2/2 concur + flag**.
- Only 1 vendor ran (no outside voice): **NOT positive** — needs human
  review or wait for vendor recovery.

**Hard stop (do not continue):** bug count not converging → the
implementation method or architecture needs rework, not another patch.

## Step 6 — drift triple-detection (agent judgment, wiki §drift)

Hit any one → **STOP, rework at implementation/architecture level, do
NOT keep patching**:

| Drift | Trigger | Meaning |
|---|---|---|
| Quantity | this round's findings count not decreasing (flat/up) | patch introduces bugs ≥ rate it fixes → wrong direction |
| Class | a new class of finding not seen last round | not converging, exposing new surface → re-examine architecture |
| Target | reviewers polishing secondary output, not fixing core | drifted off core scope → reground |

> **Coverage drift ≠ architectural drift.** Same rule-class recurring
> across rounds but each round on a NEW surface (the rule is right, it
> just wasn't propagated) → this is *fix-coverage drift*: respond by
> **centralizing the rule** (write once, reference elsewhere), not by
> hard-stopping and not by inlining the same fix again. Signal: finding
> count flat (not down, not up) + file/line each round non-repeating +
> same rule class.

`3 rounds is not a hard cap` — drift detection decides when to stop, not
a round counter (no-3-cap, see `iterative-adversarial-review`).

## Step 7 — the loop

```
findings present
  → P0/P1 exist → fix → narrow self-check (same-pattern bug elsewhere?
                  fix introduced a new bug?) → commit → next round
  → no P0/P1     → STOP (normal convergence)
  → not converging / drift hit → STOP, architectural/implementation
                  rework (Step 6), not "one more round"
```

Self-check is mandatory and is NOT review — they are not
interchangeable (anti-pattern #3). The author scanning their own change
misses far more than an independent reviewer; the self-check only adds
the narrow "did my own fix regress / repeat a pattern" pass on top of
review, never instead of it.

**Defer protocol** (tdd-autonomous-dev §切片内纪律, three parts, none
optional): ① explicit P2/P3/P4 (not "minor") ② a specific 1–2 sentence
reason (not generic) ③ accumulate to deferred staging; `gstack-ship`
lands it into the PR body `## Deferred Findings`
(`- [ ] [P2] <summary> — <reason> — <expected timing>`).

## Anti-patterns (wiki §反模式 — refuse these)

1. N codex all on the full diff (N>1 must split sections — duplicate findings, no coverage gain).
2. No cross-family reviewer (only Claude / only codex) — single family cannot break section silos.
3. Self-scan instead of an independent subagent — author bias, high miss rate. Self-check ≠ review.
4. Same-family different-size as "outside voice" (Opus + Sonnet) — not cross-vendor.
5. Hardcoded N=3 ignoring diff size.
6. Serial launch (send some, await, send rest).
7. Drift hit → rationalize "one more round" — the infinite-loop entrance.
8. Silent vendor degrade — always flag "本轮缺 X".
9. v2 N × Claude opus split sections — violates current quota allocation.
10. Treating N/N concur as ship-ready — category error (Step 5).
