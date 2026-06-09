---
name: ak-cross-m-review
description: Local pre-PR cross-model review — the executable form of the wiki's cross-model-review.md (tdd-autonomous-dev spine step 4 per-slice / step 5 ship-pre, Layer 1). Dispatches the v3 vendor squad (1 Claude opus Agent + N codex gpt-5.5 + 1 Gemini via agy 1.0.0 = N+1+1, N by diff size) in a two-phase 顺机理 dispatch (msg1 = all CLI Bash run-in-background, msg2 = Claude Agent, no-peek invariant between), then merge / grade / drift-check / loop as the agent judgment the wiki prescribes. Use every dev cycle before a PR, so the agent runs the wiki step the same way instead of re-deciding by feel.
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

If `--scenario` is omitted, default to **ship-pre** (the wider, safer
lens — reviewing more than a slice is fail-safe; reviewing less is not).

Build the reviewed diff with plain git (`git diff <base>...HEAD`, or
`git diff <range>`, or the `--diff` file). No diff state machine — it is
just the change under review for this round.

Pre-flight gates (wiki §操作规程 / §边界):

- **Content PR with user-facing fact claims** (dates / names / orgs /
  stats / security): run `content-fact-gate` FIRST. Cross-model
  reviewers share training-data bias and rubber-stamp shared
  hallucinations; this lens cannot catch that. (`content-fact-gate` is
  the upstream wiki gate `content-fact-gate.md` — a caller precondition,
  not a script bundled in this repo.)
- **Small diff** (typo / copy, < 50 changed lines): explicit exception —
  run **1+1** (Claude Agent + codex, cross-family) instead of the v3
  default, and you MUST annotate the eventual commit message
  `"小 diff 例外，跑 1+1 不跑 v3 default"`. Silent degrade is an
  anti-pattern.

## Step 1 — setup (v3 N+1+1) + the N table

Default **1+1+1**: 1 × Claude opus-4.7 (Agent subagent, full diff) +
1 × codex `gpt-5.5` + 1 × Gemini (via `agy` 1.0.0, locked to **3.5
Flash** — the explicit exception to "strongest review model", since
the original `gemini` CLI stopped serving 2026-06-18 and `agy` is the
only in-kind in-place replacement), **all full diff**. Only codex
instantiates by diff size; Claude & Gemini are always ×1 on the full
diff.

| Diff size | codex N | total reviewers | lens split |
|---|---|---|---|
| Small/Tiny (< 200 lines / 1 section) | 1 | 3 (1+1+1) | all three full diff |
| Medium (200–500 / 2 sections) | 2 | 4 (1+2+1) | 2 codex split 1/2 within-section; Claude+Gemini full |
| Large (500+ / 3+ sections) | 3 | 5 (1+3+1) | 3 codex split 1/3 within-section; Claude+Gemini full |

**Strongest review model only** — Anthropic `claude opus-4.7`, OpenAI
`gpt-5.5`; **Gemini is the documented exception** (locked to 3.5 Flash
via `agy` 1.0.0 — wiki trade-off: keep 3-vendor cross-family coverage
over dropping the Gemini leg entirely after the `gemini` CLI EOL).
**Never** dev-tier `gpt-5.3-codex-spark` / `claude sonnet-4.6` as a
reviewer (coding-tier model choice is a separate matter; do not carry
it into review).

> Orchestration law: cross-model review is ALWAYS run by the **main
> session**. There is no "subagent runs review internally" — a subagent
> cannot spawn the Claude reviewer (Claude Code does not expose `Agent`
> to subagents). A slice may be *implemented* by a subagent, but its
> per-slice review and the ship-pre review are both run here, by the
> main session, as N+1+1.

## Step 2 — two-phase dispatch (wiki §并行启动, 2026-05-18 顺机理 reorder)

The old "all reviewers in ONE assistant message" rule **fights the tool
mechanics** — Agent is synchronous foreground, Bash + `run_in_background:
true` is async background; mixing both in one message kept failing
(missed Gemini, accidental serialization, bg-Bash not actually
dispatched). Replaced with **two-phase 顺机理** that flows WITH the
mechanics:

**msg1 — homogeneous async batch.** ONE assistant message containing
every Bash CLI reviewer tool call, ALL with `run_in_background: true`:

- Default (N=1): 1 × `Bash` (`backends/codex-review.sh`) + 1 × `Bash`
  (`backends/gemini.sh` — which calls `agy -p --sandbox` internally,
  see invocation forms) = **2 bg jobs**.
- Upgraded (N codex): N × `Bash` codex (section k/N, non-overlapping
  diff slices) + 1 × `Bash` `gemini.sh` (full diff) = **N+1 bg jobs**.

**msg2 — the very next message; first content MUST be the Agent call.**
1 × `Agent` tool call (Claude opus subagent, full-diff reviewer prompt).
The Agent runs foreground (the turn blocks here) while msg1's bg CLIs
continue running.

**no-peek invariant** (the one thing prose still has to enforce):
between msg1 and msg2, do NOT read any CLI output, do NOT make any
other tool call. msg2's first content IS the Agent call, full stop.
Peeking at a background notification or doing anything else between
the two messages = silent serialization = drift back to the old failure
mode.

Both wiki goals are preserved by construction:

- **Concurrency**: msg1's CLIs run in the background while msg2's Agent
  runs foreground → wall-clock ≈ max(cli, agent).
- **Independence**: Agent is dispatched with ZERO CLI results in hand
  (you have not read them) → no cross-vendor contamination.

Invocation forms (wiki §调用规范, from `codex-bot-conventions`):

- **Codex** — only via `backends/codex-review.sh` (pins
  `printf %s "$PROMPT" | codex exec --ephemeral --model gpt-5.5 - 2>&1`).
  **`--ephemeral` is mandatory** — cmr runs N codex in parallel
  (1+N+1); without it concurrent instances collide on `~/.codex/session`
  → cross-talk (prompt A surfaces in instance B's context). Wiki
  §额外硬规则 #6 / codex#11435. Never `codex exec "$(...)"` (hangs → pkill),
  never `-C <dir>` (wrong workdir), never `codex review --base B
  "PROMPT"` (can't pass both).
- **Gemini** — only via `backends/gemini.sh`, which calls
  `agy -p --sandbox` (Antigravity CLI 1.0.0, the in-kind replacement
  after `gemini` CLI's 2026-06-18 EOL; locked to 3.5 Flash, no
  `--model` flag). cwd = repo root (agy auto-enters the workspace);
  large diff → `AGY_PRINT_TIMEOUT=15m` (default 5m is short). Never
  `agy --dangerously-skip-permissions` (re-consents high scope, breaks
  headless auth); never the deprecated `gemini --approval-mode plan`.
  **agy is agentic — `--sandbox` does NOT stop it editing files / running
  commands** (first-run: an agy review rewrote tracked files + ran
  pytest). `gemini.sh` therefore prepends an explicit "REVIEW ONLY, do
  not modify any file, do not run commands" preamble to every agy prompt
  (wiki §调用规范 line 185); the preamble is the real read-only guard,
  `--sandbox` is defense-in-depth. cmr-reviewer.md carries the same
  read-only hard-constraint for all vendors.
  The backend handles agy's keychain auth-race with warm + retry (4
  attempts total = initial 1 + 3 retries; each attempt pre-warms
  `Antigravity Safe Storage` keychain item). All 4 failing → emit the
  exact flag `本轮缺 gemini (auth race after retry×3)`, do not block
  (§降级链).
- **Claude reviewer** — the `Agent` tool, model `opus`, full-diff
  reviewer prompt. Never the headless `claude -p` path here
  (rate-limit + 25min timeout footgun, plus 2026-05-17 capability
  correction: subagents cannot spawn subagents, so the Claude reviewer
  MUST be spawned by the main session via `Agent`).
- Always `2>&1`. Run from the repo root, no `-C`. The backends
  self-time-out (`backends/codex-review.sh`: `CMR_CODEX_TIMEOUT`,
  default 600s, scoped kill of its own pid tree) and degrade
  automatically — you rarely need to intervene. If you must kill a hung
  reviewer, kill ONLY its specific pid; **never a global `pkill -f
  codex`** (msg1 launched N parallel codex reviewers — a global pkill
  takes the siblings down too). rate / quota / limit → the backend
  degrades and flags "本轮缺 X"; do not retry by hand.

Findings channel: reviewers wrap their JSON between
`===CMR-FINDINGS-BEGIN===` / `===CMR-FINDINGS-END===` sentinels
(`prompts/cmr-reviewer.md` enforces this); `lib/extract_json.py` takes
**only** the sentinel block — schema echoed from the prompt or JSON
quoted from the diff under review is structurally ignored, never
mistaken for the review. `backends/codex-review.sh` / `gemini.sh`
degrade cleanly (synthetic empty findings + nonzero exit + visible
"本轮缺 X" flag) on timeout / auth / quota / no-sentinel / agy keychain
auth-race (after 4 attempts), so a failed or non-compliant vendor is
always detectable, never a silent zero-finding pass.

Prompt templates: feed every reviewer `prompts/cmr-reviewer.md` + the
diff; the fixer (Step 7) uses `prompts/cmr-fixer.md` (the 3-part defer
protocol). They are templates, not control logic — adjust the lens line
per scenario (per-slice vs ship-pre).

## Step 3 — degradation (never silent)

v3 requires all 3 vendors. If one is unavailable, run with the rest and
**flag explicitly in the round report** — never silent-degrade to 1+1.

| Down (main = Claude) | Continue with | Flag |
|---|---|---|
| codex (all) | Claude + Gemini | `本轮缺 codex` |
| gemini | Claude + codex | `本轮缺 gemini` (reason: rate / quota / agy auth-race after retry×3 / sandbox write denied) |
| 1 of N codex | Claude + (N−1) codex + Gemini | `codex 实例 N→N−1` |
| codex + gemini both | Claude only (fallback, no outside voice) | `本轮无 outside voice — 需人工补 review` |

(Main = Codex variant + the Claude-auth live-smoke rule:
`printf 'Return exactly: CLAUDE_OK\n' | claude -p --output-format json
--disable-slash-commands --tools ""` — never file/env auth checks. See
wiki §降级链.)

## Step 4 — merge + grade (agent judgment, not a deterministic engine)

Collect every reviewer's findings (use `lib/extract_json.py` to pull the
JSON out of each CLI's stdout). Then, as judgment:

- Group findings that describe the same issue across reviewers.
- Grade each P0 / P1 / P2 / P3 / P4. Reviewers emit
  `critical|high|medium|low|clarity` (the `prompts/cmr-reviewer.md`
  schema) — map critical→P0, high→P1, medium→P2, low→P3, clarity→P4.
  P0–P4 is the wiki's grade scale; keep that vocabulary downstream.
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
  → P0/P1 exist → FIX (see fix-loop discipline below) → narrow self-check
                  (same-pattern bug elsewhere? fix introduced a new bug?)
                  → commit → next round
  → no P0/P1     → STOP (normal convergence)
  → not converging / drift hit → STOP, architectural/implementation
                  rework (Step 6), not "one more round"
```

**Fix-loop discipline (wiki §修复).** The wiki's ground truth: "findings
are stable, the fix loop is the bottleneck — agent fixes by feel, breaks
neighbors, skips repro / the regression test." So the fix step is gated.

> **Default = non-trivial. The burden of proof is on whoever claims
> "mechanical" (wiki `91a4e1f`).** The FIRST action in the fix loop is to
> **explicitly classify** the fix, in writing (commit msg, or a
> conversation line as you start the fix). No explicit classification =
> non-trivial = you MUST `Skill` invoke `/diagnose`. This makes "skip
> /diagnose" a visible, audited decision instead of a silent default —
> the silent default is exactly why real fixes almost never reach
> /diagnose even though most of them should.

| Fix kind | Route |
|---|---|
| **Mechanical** — see the hard bar below; **must be explicitly declared + a one-line justification of why it qualifies** | edit directly, no protocol |
| **Non-trivial** (behavioral / runtime / may-touch-neighbors / not-fully-understood / **anything not explicitly declared mechanical**) | the **first tool call MUST be `Skill` invoke `/diagnose`** — not first grep, not first guess, not first write a patch, not first read a file. /diagnose's 6 phases (feedback loop → reproduce → ranked falsifiable hypotheses → one-probe-at-a-time instrument → fix + regression test → cleanup, with a HITL fallback) are an iterative, possibly human-in-the-loop investigation the **main session** drives — it does not collapse into a single fixer-subagent return. Canonical: wiki §修复 + `matt-pocock-skills#/diagnose`. |

> **The mechanical bar is HIGH — claim it rarely.** Observed reality:
> almost everything gets waved through as "mechanical," and those
> "mechanical" fixes are where the breakage comes from. Mechanical is a
> **closed allowlist**, not a vibe:
> - typo in prose/comment · dead/renamed doc anchor or link · stale
>   label or display string · frontmatter/CHANGELOG date · pure
>   whitespace/formatting.
>
> ALL of these must ALSO hold, or it is non-trivial:
> 1. **Touches zero executing code.** Any change to shell logic, a flag,
>    a condition, control flow, an arg, a regex, a path, a number, a
>    config value → NOT mechanical, even one line, even if "obvious."
> 2. **Single site, no propagation.** Cannot affect any other file or
>    call site.
> 3. **Provably inert.** You could stake that it cannot change any test
>    outcome or runtime behavior — and ideally a test/`--selftest` proves
>    it.
>
> NOT valid mechanical justifications: "it's simple," "it's one line,"
> "I'm confident," "it's obvious," "just a small fix." Those are the
> over-claims. **When the slightest doubt exists → non-trivial.** A
> changed flag like `--ephemeral`, a guard condition, a quoting fix in a
> command — all non-trivial, no matter how small.

A fresh-context subagent told to "fix a non-trivial bug" guesses and
breaks neighbors — exactly what /diagnose exists to prevent. The
`cmr-fixer.md` subagent therefore produces **mechanical** diffs only
(by the hard bar above); non-trivial defects go back to the main session
for /diagnose.

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
6. **Two-phase dispatch violations** — peeking at any CLI output between msg1 and msg2, or emitting anything other than the Agent call as msg2's first content, or mixing Agent + Bash in a single message (the old 逆机理 rule the two-phase replaced). All collapse to silent serialization.
7. Drift hit → rationalize "one more round" — the infinite-loop entrance.
8. Silent vendor degrade — always flag "本轮缺 X".
9. v2 N × Claude opus split sections — violates current quota allocation.
10. Treating N/N concur as ship-ready — category error (Step 5).
11. `gemini -p` headless (CLI stopped serving 2026-06-18) or `agy --dangerously-skip-permissions` (re-consents high scope, breaks headless auth) — use `backends/gemini.sh`, which pins `agy -p --sandbox` + the warm-retry recipe.
12. **A reviewer that writes** — relying on `--sandbox` alone to keep an agentic CLI (agy) read-only. It edits files / runs commands anyway (first-run: rewrote tracked files + ran pytest mid-review). The prompt MUST forbid writes ("REVIEW ONLY, do not modify any file, do not run commands"); a review that mutates the repo under review is the defect, even when the mutation is correct.
13. **Over-claiming "mechanical" to skip /diagnose** — waving a fix through as mechanical on "it's simple / one line / obvious / I'm confident." Default is non-trivial; mechanical is a closed high-bar allowlist that touches zero executing code (Step 7). A changed flag / guard / condition / quoting fix is non-trivial no matter how small. Skipping classification = non-trivial = `/diagnose` required.
