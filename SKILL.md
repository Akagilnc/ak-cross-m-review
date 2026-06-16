---
name: ak-cross-m-review
description: Local pre-PR cross-model review — the executable form of the wiki's cross-model-review.md (tdd-autonomous-dev spine step 4 per-slice / step 5 ship-pre, Layer 1). Dispatches the v3 vendor squad (1 Claude reviewer Agent + N codex gpt-5.5 + 1 Gemini via agy = N+1+1, N by diff size) in a two-phase 顺机理 dispatch (msg1 = all CLI Bash run-in-background, msg2 = Claude Agent, no-peek invariant between), then merge / grade / drift-check / loop as the agent judgment the wiki prescribes. Use every dev cycle before a PR, so the agent runs the wiki step the same way instead of re-deciding by feel.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
  - TodoWrite
  - Skill
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
- **Design docs (ADR / spec / contract) get cmr too — same rigor as
  code** (wiki §设计文档). A design doc carries decisions *more
  upstream* than code (a wrong spec → the whole implementation is built
  on a wrong premise; TDD-green ≠ spec-correct — code can perfectly
  implement a wrong design). So an ADR / spec / contract **MUST run a
  full cmr in `doc` mode** — not "written → approved → done" — and when
  you *produce* such a doc you **proactively remind the user to review
  it**, without waiting to be asked. Doc-mode runs the same 1+1+1
  two-phase setup; concretely: pass mode `doc` to the backends
  (`backends/codex-review.sh doc` / `backends/gemini.sh doc`, and the
  Claude `Agent`) and append a **design-completeness** lens to the
  `cmr-reviewer.md` prompt instead of the code lens — contract holes /
  state-machine deadlocks / uncovered boundary cases / undefined
  invariants / contradictions with existing ADRs. (Evidence:
  ming-salvage-sim ADR 0008 — a *design doc* — took multiple cmr rounds
  to converge, each catching a real spec-level hole like a
  poison-payload soft-lock that no code read would surface.)

## Step 1 — setup (v3 N+1+1) + the N table

Default **1+1+1**: 1 × Claude reviewer (Agent subagent, full diff —
current strongest available Claude per Step 2: `fable`, or `opus`/Opus
4.8 while Fable is paused) + 1 × codex `gpt-5.5` + 1 × Gemini (via `agy`,
locked to **3.5 Flash** — the explicit exception to "strongest review
model", since the original `gemini` CLI stopped serving 2026-06-18 and
`agy` is the only in-kind in-place replacement), **all full diff**. Only
codex instantiates by diff size; Claude & Gemini are always ×1 on the
full diff.

| Diff size | codex N | total reviewers | lens split |
|---|---|---|---|
| Small/Tiny (< 200 lines / 1 section) | 1 | 3 (1+1+1) | all three full diff |
| Medium (200–500 / 2 sections) | 2 | 4 (1+2+1) | 2 codex split 1/2 within-section; Claude+Gemini full |
| Large (500+ / 3+ sections) | 3 | 5 (1+3+1) | 3 codex split 1/3 within-section; Claude+Gemini full |

**Strongest review model only** — Anthropic = the current strongest
available Claude (Step 2 is the authority: `claude-fable-5` when up;
**Fable paused 2026-06-13 → `claude-opus-4-8` now**), OpenAI `gpt-5.5`;
**Gemini is the documented exception** (locked to 3.5 Flash via `agy` —
wiki trade-off: keep 3-vendor cross-family coverage over dropping the
Gemini leg entirely after the `gemini` CLI EOL).
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
  (`backends/gemini.sh` — which calls `agy --sandbox --print ''`
  internally, see invocation forms) = **2 bg jobs**.
- Upgraded (N codex): N × `Bash` codex (section k/N, non-overlapping
  diff slices) + 1 × `Bash` `gemini.sh` (full diff) = **N+1 bg jobs**.

**msg2 — the very next message; first content MUST be the Agent call.**
1 × `Agent` tool call (Claude reviewer subagent, model per the
Claude-reviewer invocation form below — `fable` when up, else `opus`/Opus
4.8 while Fable is paused; full-diff reviewer prompt). The Agent runs
foreground (the turn blocks here) while msg1's bg CLIs continue running.

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

> **Reasoning-effort reality, per leg** (wiki §调用规范, 2026-06-14
> measured) — the three legs run at very different reasoning depth:
> **codex** = `xhigh` (pinned, maxed); **Claude reviewer Agent**
> (main=Claude — the primary path) = Opus 4.8 adaptive default and
> **cannot be dialed up** — the `Agent` tool exposes no effort param, and
> `ultrathink` written into a subagent prompt is inert literal text
> (claude-code#25669); **agy / Gemini** = 3.5 Flash, no knob. So in the
> main=Claude path **only codex is at max depth** — which is why codex
> tends to surface the most findings each round. (When main=Codex the
> Claude leg runs via `claude -p` and CAN take `--effort max` ≈ 5× depth
> — see Step 3.)

- **Codex** — only via `backends/codex-review.sh` (pins `printf %s
  "$PROMPT" | codex exec --ephemeral -c model_reasoning_effort="xhigh"
  --model gpt-5.5 - 2>&1`). **`--ephemeral` is mandatory** — cmr runs N
  codex in parallel (1+N+1); without it concurrent instances collide on
  `~/.codex/session` → cross-talk (prompt A surfaces in instance B's
  context). Wiki §额外硬规则 #6 / codex#11435. **`-c
  model_reasoning_effort="xhigh"` is also pinned** — codex would
  otherwise inherit the machine's `~/.codex/config.toml` value and
  silently drop review depth on a clone / other host (`--selftest`
  guards both flags). Never `codex exec "$(...)"` (hangs → pkill), never
  `-C <dir>` (wrong workdir), never `codex review --base B "PROMPT"`
  (can't pass both).
- **Gemini** — only via `backends/gemini.sh`, which calls
  `agy --sandbox --print '' <<<prompt` (Antigravity CLI, the in-kind
  replacement after `gemini` CLI's 2026-06-18 EOL; locked to 3.5 Flash).
  **NOT the old `agy -p --sandbox`**: agy 1.0.7 made `--print`/`-p` a
  string flag that takes its value from the next token, so `-p
  --sandbox` silently swallowed `--sandbox` as the prompt value —
  `--sandbox` never engaged and the diff rode in only via agy's
  stdin-concatenation (prompt = `<--print value>` + `\n` + stdin).
  `--sandbox` BEFORE an explicit empty `--print ''` keeps sandbox a real
  flag (verified: "enabling terminal sandbox" log line) and the diff on
  stdin (no ARG_MAX limit). cwd = repo root; large diff →
  `AGY_PRINT_TIMEOUT=15m` (default 5m is short). Never
  `agy --dangerously-skip-permissions` (re-consents high scope, breaks
  headless auth); never the deprecated `gemini --approval-mode plan`.
  **agy is agentic — `--sandbox` does NOT stop it editing files / running
  commands** (first-run: an agy review rewrote tracked files + ran
  pytest). `gemini.sh` therefore prepends an explicit "REVIEW ONLY, do
  not modify any file, do not run commands" preamble to every agy prompt
  (wiki §调用规范 line 185); the preamble is the real read-only guard,
  `--sandbox` is defense-in-depth. cmr-reviewer.md carries the same
  read-only hard-constraint for all vendors.
  **Quota / 429 visibility**: agy routes fatal backend errors
  (RESOURCE_EXHAUSTED / 429 quota, etc.) to its `--log-file`, NOT
  stdout/stderr — a quota-exhausted run looks like a plain empty success
  (rc=0, empty stdout). `gemini.sh` passes `--log-file` and greps it on
  degrade, so the flag names the real cause (e.g. `本轮缺 gemini (empty
  output, agy rc=0; quota/429 — agy individual quota exhausted; Resets
  in 63h…)`) instead of a bare "empty output".
  **agy model-degradation ladder** (the leg's own fallback): agy's
  Gemini quota is a small consumer Code Assist bucket that exhausts. When
  the preferred model **Gemini 3.5 Flash** quota-429s, `gemini.sh` steps
  the agy leg DOWN to **`Claude Sonnet 4.6 (Thinking)` via agy** — a
  SEPARATE quota bucket (verified), and deliberately a DIFFERENT model
  from the squad's Claude-Agent leg (Opus 4.8) for a distinct voice — so
  a third independent read survives. Only when EVERY rung is quota-
  exhausted does the agy leg step down entirely (degrade → `本轮缺
  gemini`). When a fallback rung runs, the round has **no Google voice**;
  `gemini.sh` flags that on stderr (the 3rd voice is then agy-served
  Claude, separate quota). `AGY_MODEL` env pins one explicit model
  (manual / tests). (Cross-family is the ideal, but Gemini is already
  quota-dead either way — a distinct same-family 3rd read beats only
  two; the wiki §降级链 should bless this rung.) **Workspace = the reviewed
  repo, not the skill dir**: agy reads its cwd as the workspace, so
  `gemini.sh` cd's into the **reviewed repo root** (`REVIEW_ROOT` = the
  invocation cwd's `git rev-parse --show-toplevel`), NOT `PROTO_ROOT`
  (the skill's own dir — which lives under `~/.claude/skills/...`, hidden,
  and would make agy refuse the workspace and run diff-only on EVERY
  registered-skill invocation). agy still refuses a workspace whose path
  has a hidden (dot) component ("is hidden: ignore uri"), so if the
  *reviewed repo itself* is under a dot-path (e.g. reviewing from a
  `.claude/worktrees/...` checkout) the Gemini leg is diff-only;
  `gemini.sh` warns (does not degrade). For full agy grep-grounding
  (esp. the 5a completeness audit) review from a non-hidden checkout.
  The backend handles agy's keychain auth-race with warm + retry (4
  attempts total = initial 1 + 3 retries; each attempt pre-warms
  `Antigravity Safe Storage` keychain item). All 4 failing → emit the
  exact flag `本轮缺 gemini (auth race after retry×3)`, do not block
  (§降级链).
  **Intentional divergence from the wiki here**: the wiki's auth-race
  `[!note]` says the 1s-keyring race was fixed upstream in agy 1.0.1
  (#85/#51) and that 1.0.8 needs no warm+retry. The skill **keeps** the
  warm+retry recipe anyway, because the OAuth login page still pops up
  intermittently on 1.0.8 in practice (author-observed) — so the safety
  net stays until that stops recurring. (The wiki note is the one that's
  out of date here; flag it for correction.)
- **Claude reviewer** — the `Agent` tool, full-diff reviewer prompt,
  model = **the current strongest available Claude**. This bullet is the
  ONE authoritative place for the Claude leg's model — flip only it when
  Fable pauses / returns:
  - `fable` (Claude Fable 5) when available;
  - **2026-06-13 Fable is paused → use `opus` (Opus 4.8) now; revert to
    `fable` when it returns** (wiki §操作规程 model table).
  - The model MUST be set **explicitly** on the `Agent` call — it does
    **NOT** inherit the session model. (A dev-tier session would
    otherwise silently drag the reviewer below the strongest-review-model
    rule; you got lucky only if the session itself ran Opus 4.8.)
  - `fable` additionally needs Claude Code v2.1.170+; on an older client
    where it isn't selectable, `opus` is the same current baseline.

  Never the headless `claude -p` path **for the Claude reviewer in this
  (main = Claude) flow** (rate-limit + 25min timeout footgun, plus the
  2026-05-17 capability correction: subagents cannot spawn subagents, so
  here the Claude reviewer MUST be spawned by the main session via
  `Agent`). (Exception — a *different host*: when the main session is
  **Codex**, Step 3, it has no `Agent` tool, so there the Claude reviewer
  legitimately runs via `claude -p`; and the Step 3 Claude-auth
  *live-smoke* is a `claude -p` probe too — both are outside this ban,
  which is only about dispatching the reviewer in the main=Claude flow.)
- Always `2>&1`. Run from the repo root, no `-C`. The backends
  self-time-out (`backends/codex-review.sh`: `CMR_CODEX_TIMEOUT`,
  default 600s, scoped kill of its own pid tree) and degrade
  automatically — you rarely need to intervene. If you must kill a hung
  reviewer, kill ONLY its specific pid; **never a global `pkill -f
  codex`** (msg1 launched N parallel codex reviewers — a global pkill
  takes the siblings down too). rate / quota / limit → the backend
  degrades and flags "本轮缺 X"; do not retry by hand.
- **Huge diff (> 10K lines): segment the prompt** to avoid saturating the
  pipe buffer (wiki §额外硬规则 #3). This is separate from the N-table
  (which scales reviewer *count*) — it is about not shoving a single
  >10K-line payload through one stdin pipe.

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
| gemini | Claude + codex | `本轮缺 gemini` (reason: rate / quota-429 (agy individual quota exhausted, + "Resets in …" from agy's --log-file) / agy auth-race after retry×3 / sandbox write denied). agy hides 429/quota in its --log-file and exits rc=0 empty — `gemini.sh` greps the log so the reason is named, not a bare "empty output". |
| gemini (no repo context) | Claude + codex + Gemini (diff-only) | `gemini WITHOUT repo context` — cmr ran from a hidden (dot) path (e.g. `.claude/worktrees/...`); agy refuses hidden workspace folders. Warn, not a leg drop; rerun from a non-hidden path for full context. |
| 1 of N codex | Claude + (N−1) codex + Gemini | `codex 实例 N→N−1` |
| codex + gemini both | Claude only (fallback, no outside voice) | `本轮无 outside voice — 需人工补 review` |
| **Fable 5 safeguards trigger** (<5% of sessions; security / bio / chem / distillation topics auto-route to Opus 4.8 — Anthropic docs. NOT a leg failure: squad stays 1+1+1, the Claude leg just ran on Opus 4.8; does NOT trigger any other degradation. Flag for finding-consistency transparency — a same-model R1→R2 comparison now has one Opus run mixed in.) | Claude (Opus 4.8) + codex + Gemini | `Claude leg = Opus 4.8 (Fable safeguards trigger)` |
| **Client < Claude Code v2.1.170** (the `fable` alias is not selectable on older clients. NOT a leg failure: dispatch the Claude leg with `model: opus` (Opus 4.8) instead of hard-failing; squad stays 1+1+1. Upgrade the client to restore the strongest Fable tier.) | Claude (Opus 4.8) + codex + Gemini | `Claude leg = Opus 4.8 (client < v2.1.170, no fable)` |

> **Fable paused (2026-06-13):** the Claude leg's current baseline IS
> Opus 4.8 (Step 2 is the authority), so the two Fable-specific rows
> above are **dormant** until Fable returns — Opus 4.8 is the default
> right now, not a degradation. When Fable is back they re-activate as
> Fable→Opus fallbacks.

**If the main session is Codex** (not the wiki's primary scenario, but
symmetric — wiki §降级链 "主 session = Codex"):

| Down (main = Codex) | Continue with | Flag |
|---|---|---|
| Claude (verify by live-smoke first, below) | Codex + Gemini | `本轮缺 claude` |
| Gemini | Codex + Claude | `本轮缺 gemini` |
| Claude + Gemini both | Codex only (fallback, no outside voice) | `本轮无 outside voice` |

When main = Codex, **never** check Claude auth via file/env (false
negatives on keychain / GUI logins) — use a live smoke:
`printf 'Return exactly: CLAUDE_OK\n' | claude -p --output-format json
--disable-slash-commands --tools ""` (`.result == "CLAUDE_OK"` → up,
priority 1; failure / timeout → degrade). After the smoke passes, the
actual Claude **review** call is `claude -p --effort max --output-format
json --disable-slash-commands` — **`--effort max`** (≈5× reasoning depth,
no error on Opus 4.8) and crucially **no `--tools ""`**: the `--tools ""`
kill is ONLY for the auth smoke. A reviewer must keep Read/Grep/Glob to
do grounded review (grep the source, not just the diff) — killing its
tools guts the grounding axis (wiki §调用规范). The outside-voice
reviewer always stays the strongest in range (main = Claude → codex
`gpt-5.5`; main = Codex → current strongest Claude or Gemini), never
dev-tier spark / 5.3-codex / sonnet. See wiki §降级链.

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
- Upgraded-state single-vendor loss (1+N+1):
  - Claude **or** Gemini missing → N+1 reviewers: **(N+1)/(N+1) concur + flag**.
  - **All codex missing** → falls back to 1+0+1 = 2 reviewers (Claude + Gemini): **2/2 concur + flag `升级态缺 codex，已退化`**.
  - codex partial-instance loss (N→N′): **(N′+2)/(N′+2) concur + flag `codex 实例数 N→N′`**.
- Only 1 vendor ran (no outside voice — e.g. codex+gemini both down → Claude only; or claude+gemini both down → codex only): **NOT positive** — no cross-family check; needs human review or wait for vendor recovery.

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
                  → commit → next round (FULL re-review — see below)
  → no P0/P1     → STOP (normal convergence)
  → not converging / drift hit → STOP, architectural/implementation
                  rework (Step 6), not "one more round"
```

**Every round = full re-review (NOT a "did last round's P0/P1 close?"
spot-check)** (wiki §每轮 review = 全量复审). From round 2 on, the reviewer
(and the main session dispatching it) drifts toward narrowing scope to
"is last round's P1 fixed?" — only verifying prior findings, no longer
reading the current full diff. **This repo has hit it repeatedly; refuse
it explicitly.**

The rule: **every round re-reviews the CURRENT full diff in full.**
"Did last round's P0/P1 close" is only a line **appended to the tail** of
the review prompt — not the round's whole scope. Order is fixed: full
review is the body, prior-finding regression-confirm is the tail.

Why narrowing is wrong (all three are structural, not "just try harder"):

1. **The fix is itself new diff and must be reviewed.** A fix touches
   neighbors (change A breaks B); narrowing to "is P1 closed" hides the
   regression the fix introduced. The fix-loop's own "self-check (fix
   introduced a bug?)" is *author* self-check — structurally it cannot
   replace next round's independent reviewer reading the fix diff in full
   (anti-pattern #3: self-check ≠ review).
2. **A reviewer in one round is non-exhaustive.** Last round not raising
   a finding ≠ nothing wrong there — its attention may simply not have
   reached it. A fresh full read (especially a different vendor) catches
   structurally-missed surface; that is the value of multi-round ×
   cross-model.
3. **Narrowing fakes convergence → breaks termination.** Step 5's
   positive termination (N/N concur) and Step 6's drift triple all assume
   **each round covers the same full surface**. Review only last round's
   P1 and the finding count is artificially low → looks converged when it
   just wasn't looked at. A "2/2 concur" under narrowed scope is a bad
   check.

Prompt construction when dispatching a later round:

```
[body] Full-review the CURRENT full diff (including this round's fix),
       per the §Step 1 lens split — emit ALL findings in the
       cmr-reviewer.md schema vocabulary (critical/high/medium/low/
       clarity), not limited to ones raised before. (Reviewers emit the
       severity strings; Step 4 maps them to P0–P4. Do NOT instruct the
       reviewer in P-levels — that yields invalid severities and, by
       dropping low/clarity, silently narrows the "full" re-review.)
[tail] Also confirm these prior findings are correctly closed and the
       fix introduced no regression (name them in the reviewer-schema
       severity, NOT P-levels — same reason as the body):
        - high: <prior finding summary + file:line>
        - critical: <...>
```

❌ Wrong (the degraded spot-check): making `"check that last round's P1
<X> is fixed"` the *entire* prompt — the reviewer returns only
"closed / not", emits no new findings, and the fix's regression + the
surface last round missed are dropped together.

**Full re-review is orthogonal to Step 6 drift, not in tension with it.**
Drift governs *when to stop*; full re-review governs *how wide each round
looks* — and only full re-review makes the drift triple measurable. It is
also the entry-scope floor that must hold *before* Step 6's Coverage-drift
note (a late-convergence optimization) even applies.

**Fix-loop discipline (wiki §修复).** The wiki's ground truth: "findings
are stable, the fix loop is the bottleneck — agent fixes by feel, breaks
neighbors, skips repro / the regression test." So the fix step is gated.

> **Default = non-trivial. The burden of proof is on whoever claims
> "mechanical" (wiki `91a4e1f`).** The FIRST action in the fix loop is to
> **explicitly classify** the fix, in writing, **up front — a
> conversation line BEFORE your first read/edit of the target.** A
> commit-message-only classification is too late: it lets you do the
> whole fix and label it after the fact, which defeats the FIRST-action
> gate and reintroduces the silent skip. No up-front classification =
> non-trivial = you MUST invoke the `/diagnose` skill (via the `Skill`
> tool, in allowed-tools) before reading or editing anything. This makes
> "skip /diagnose" a visible, audited
> decision instead of a silent default — the silent default is exactly
> why real fixes almost never reach /diagnose even though most should.

| Fix kind | Route |
|---|---|
| **Mechanical** — see the hard bar below; **must be explicitly declared + a one-line justification of why it qualifies** | edit directly, no further protocol |
| **Non-trivial** (behavioral / runtime / may-touch-neighbors / not-fully-understood / **anything not explicitly declared mechanical**) | the **first tool call MUST invoke the `/diagnose` skill** (via the `Skill` tool) — not first grep, not first guess, not first write a patch, not first read a file. /diagnose's 6 phases (feedback loop → reproduce → ranked falsifiable hypotheses → one-probe-at-a-time instrument → fix + regression test → cleanup, with a HITL fallback) are an iterative, possibly human-in-the-loop investigation the **main session** drives — it does not collapse into a single fixer-subagent return. Canonical: wiki §修复 + `matt-pocock-skills#/diagnose`. |

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
>    outcome or runtime behavior — and ideally a test or `--selftest`
>    proves it.
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
9. v2 N × Claude (opus / fable) split sections — violates current quota allocation.
10. Treating N/N concur as ship-ready — category error (Step 5).
11. `gemini -p` headless (CLI stopped serving 2026-06-18) or `agy --dangerously-skip-permissions` (re-consents high scope, breaks headless auth) — use `backends/gemini.sh`, which pins `agy --sandbox --print ''` + the warm-retry recipe. Also dead: `agy -p --sandbox` (1.0.7 flag-parse made `-p` swallow `--sandbox` as the prompt value → sandbox never engaged).
12. **A reviewer that writes** — relying on `--sandbox` alone to keep an agentic CLI (agy) read-only. It edits files / runs commands anyway (first-run: rewrote tracked files + ran pytest mid-review). The prompt MUST forbid writes ("REVIEW ONLY, do not modify any file, do not run commands"); a review that mutates the repo under review is the defect, even when the mutation is correct.
13. **Over-claiming "mechanical" to skip /diagnose** — waving a fix through as mechanical on "it's simple / one line / obvious / I'm confident." Default is non-trivial; mechanical is a closed high-bar allowlist that touches zero executing code (Step 7). A changed flag / guard / condition / quoting fix is non-trivial no matter how small. Skipping classification = non-trivial = `/diagnose` required.
14. **Narrowing a later round into a "did last round's P1 close?" spot-check** — every round must full-re-review the current full diff; prior-finding acceptance is only a tail item. Narrowing drops the regression the fix introduced + the surface last round missed, and fakes a low finding count that breaks the Step 5/6 convergence read. See Step 7 "Every round = full re-review."
