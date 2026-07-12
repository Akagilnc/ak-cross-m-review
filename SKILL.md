---
name: ak-cross-m-review
description: Local pre-PR cross-model review — the executable form of the wiki's cross-model-review.md (tdd-autonomous-dev spine step 4 per-slice / step 5–6 ship-pre, Layer 1). The squad depends on the trigger point — ship-pre uses N codex gpt-5.6-sol + 1 Claude Agent + 1 Gemini via agy = N+1+1, dispatched two-phase (msg1 = all CLI Bash run-in-background, msg2 = Claude Agent, no-peek between); per-slice uses N codex + agy = N+1 (no Claude — credit; run by the slice's own subagent, no two-phase). N by effective (core-logic) diff lines. Then merge / grade / drift-check / loop as the agent judgment the wiki prescribes. Use every dev cycle before a PR, so the agent runs the wiki step the same way instead of re-deciding by feel.
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
wiki ever disagree, the wiki wins; re-sync, do not fork behavior — with
ONE exception: blocks marked **⚠ RECORDED RULE / RECORDED divergence**
are deliberate, user-decided divergences (or same-day-upstreamed rules a
stale wiki checkout may not show yet). Reconcile those against their
decision record; never silently overwrite them wiki-ward.

It is **Layer 1** (local, pre-PR). It does not replace Layer 3
(`pr-review-loop`). It does not commit / push / open a PR — the caller
(or `gstack-ship`) does. One change set per invocation.

## Step 0 — scenario, scope, pre-flight

Invocation:

```
/ak-cross-m-review [--base BRANCH] [--range A..B] [--diff FILE]
                    [--scenario per-slice|ship-pre]
                    [--lens completeness|correctness]
```

> **Prefer the two named gate skills, not `--lens` by hand.** Each gate is
> its own one-line skill that just calls this engine with the right lens:
> **`ak-cmr-completeness`** (Step-5 completeness) and **`ak-cmr-correctness`**
> (per-slice / Step-6 correctness). Pick the skill that names what you
> mean — that is how the lens stays explicit and never gets forgotten,
> mis-set, or merged into the other pass. `--lens` here is the **internal
> switch** those wrappers pass; invoke it directly only for advanced use.
> **One invocation runs ONE lens** (no auto-both); a finished change runs
> **`ak-cmr-completeness` first** (must pass), **then `ak-cmr-correctness`**.

- **`per-slice`** (tdd spine step 4, after a slice's baseline commit) —
  within-slice lens: local logic / naming / test coverage / single-slice
  spec-impl consistency. Scope = that slice's commit range. Lens =
  **correctness** (via `ak-cmr-correctness`).
- **`ship-pre`** (tdd spine step 5–6, all slices done) — cross-slice.
  Scope = whole-PR cumulative diff vs base (default `main`, fallback
  `master`). **Two gates, run as two skills in order**: `ak-cmr-completeness`
  (Step 5 — must reach `CMR-VERDICT: complete`), then `ak-cmr-correctness`
  (Step 6). Never one merged prompt (§«严禁合一», below).

If `--scenario` is omitted, default to **ship-pre** (the wider, safer
scope — reviewing more than a slice is fail-safe; reviewing less is not).

- **`--lens`** (internal switch the gate skills set) picks which prompt the
  squad is fed: **`correctness`** (default) feeds `cmr-reviewer.md` (find
  defects, P0–P4); **`completeness`** feeds `cmr-completeness.md` (was the
  spec fully delivered? + exercise the behavioral keys). One invocation =
  one lens. (Before 0.3.14.0 the completeness lens had no prompt file at
  all — only prose — so ship-pre could dispatch nothing but correctness and
  the Step-5 gate silently never ran. See §Step 1 "Prompt templates".)

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
  run a reduced **cross-family 2-vendor** instead of the full default,
  scoped to who runs it (per §Step 1 / orchestration law): **ship-pre /
  main-session** = `Claude Agent + codex`; **per-slice** = `codex + agy`
  (still cross-family — a slice subagent cannot spawn the Claude `Agent`,
  and per-slice has no Claude anyway). You MUST annotate the eventual
  commit message `"小 diff 例外，跑 2-vendor 不跑 v3 default"`. Silent
  degrade is an anti-pattern.
- **Design docs (ADR / spec / contract) get cmr too — same rigor as
  code** (wiki §设计文档). A design doc carries decisions *more
  upstream* than code (a wrong spec → the whole implementation is built
  on a wrong premise; TDD-green ≠ spec-correct — code can perfectly
  implement a wrong design). So an ADR / spec / contract **MUST run a
  full cmr in `doc` mode** — not "written → approved → done" — and when
  you *produce* such a doc you **proactively remind the user to review
  it**, without waiting to be asked. Doc-mode dispatches the same way as
  code (per §Step 1 / wiki §谁跑 cmr — per-slice runner = all Bash CLI;
  ship-pre / main-session runner = two-phase + Claude via `Agent`);
  concretely: feed **`prompts/cmr-completeness.md`** (the completeness
  lens — NOT the correctness `cmr-reviewer.md`) + the doc, dispatched the
  same way (per-slice runner = all Bash CLI; ship-pre = two-phase + Claude
  via `Agent`). For a design doc the completeness lens reads as: contract
  holes / state-machine deadlocks / uncovered boundary cases / undefined
  invariants / contradictions with existing ADRs. (Evidence:
  ming-salvage-sim ADR 0008 — a *design doc* — took multiple cmr rounds
  to converge, each catching a real spec-level hole like a
  poison-payload soft-lock that no code read would surface.) Doc mode
  ALSO carries its own loop discipline — **§Doc mode discipline** below
  (constitution kill-axis, fix-classification ledger, bloat audit line,
  full confirmation-round early stop, round-10 escalation gate) — the
  additive-runaway defense. Code-diff mode is untouched by that section
  — EXCEPT its ①: the constitution packet + kill-axis applies to EVERY
  review mode, code-diff included (owner decision 2026-07-12).
- **The completeness gate (ship-pre Step 5) is its own EXECUTABLE lens —
  `prompts/cmr-completeness.md`** (before 0.3.14.0 it was only prose here,
  so a ship-pre run could dispatch nothing but the correctness prompt and
  the completeness gate silently never ran). It checks *was the spec fully
  delivered?* clause by clause — DONE/PARTIAL/NOT-DONE for features +
  CONFORMS/VIOLATES/UNVERIFIED-GAP for constraints/delegations/exemptions —
  **chasing the reference chain** (ground against the authority the spec
  names, not just the local plan-file) and **exercising** behavioral keys
  (gate / fix-loop / guard / state-machine: RUN them with an injected
  defect; anti-pattern #15). **Green tests / a pipeline that runs are NOT
  completeness evidence** (#244: S8 + 612 tests green, yet the mandated
  discipline was never wired). The full rubric IS that prompt; spine
  source: wiki [[tdd-autonomous-dev]] §Step 5 + [[verification-scope-vacuum]].
- **The two ship-pre gates are SEPARATE sequential passes — never merge
  them (wiki a70f97b «严禁合一次 cmr 闸»):** completeness (Step 5,
  spec-delivered lens) runs **first and must pass**, *then* correctness
  (Step 6, defect lens) runs on the now-complete diff. Do NOT run both
  lenses in one cmr / one prompt — conflating them makes **both** shallow
  (the completeness lens stops looking for "what's missing" and the
  correctness lens stops grounding each defect; see wiki
  [[gate-lens-heterogeneity]]). Different lens, different prompt, in order.

## Step 1 — setup: who runs it decides the squad + the N table

**The squad depends on the trigger point** (wiki §谁跑 cmr, 2026-06-18 —
Claude is concentrated to ship-pre because `claude -p` credit is too
tight to run Claude on the high-frequency per-slice gate):

- **per-slice** (after each slice's baseline commit — within-slice lens):
  **`N codex + agy` = 2-vendor, NO Claude.** Run by the slice's own
  implementing subagent (both legs are Bash CLIs, so no nested-Agent
  problem). codex effort = **`medium`** (`CMR_CODEX_EFFORT=medium`). Convergence =
  (N+1)/(N+1) + flag `per-slice 不用 Claude (credit)`.
- **ship-pre** (after all slices done — cross-slice cumulative-diff
  lens): **+Claude → 1+1+1 (N+1+1).** The **main session** orchestrates;
  the Claude leg runs via the **`Agent` subagent** (cheap, never
  `claude -p`). codex effort = **`medium`**, the same as per-slice. This is the two-phase
  dispatch (Step 2).

Strongest review model (both scenarios): Claude leg = `opus` (Opus 4.8) —
cmr does not use Fable (Step 2 recorded rule; ship-pre only); codex
`gpt-5.6-sol`; Gemini = `agy` locked to
3.5 Flash (the documented exception). Only codex instantiates by diff
size (the agy/Claude legs are always ×1 on the full diff).

> **N is by *effective lines*, not raw lines** (wiki §N 取值表,
> 2026-06-18 — hypothesis). Raw line count lies (500 lines of test
> fixture ≠ 500 lines of settlement logic). Before computing N, split
> `git diff --numstat` into two buckets: **noise** (reviewers still see
> it, but it does NOT raise N) = `*test*` / `*spec*` / `__tests__/` /
> `__snapshots__` / `*.snap` / `fixtures/` / `testdata/` / `*.lock` /
> `package-lock.json` / `go.sum` / generated / `*.md` / `docs/`; **core**
> (raises N) = the rest (typically `src/`). `effective_lines = core`.
> Unusually dense core (settlement / concurrency / security / tight
> algorithm) → bump N one tier with a one-line up-front justification
> (same "declare + justify" pattern as the fix-loop). Density itself
> isn't reliably quantifiable (needs AST/cyclomatic per-language tools,
> brittle in polyglot) → left to explicit declaration, not faked as a
> formula.

| Diff size (effective lines) | codex N | total reviewers (ship-pre) | lens split |
|---|---|---|---|
| Small/Tiny (< 500 lines / 1 section) | 1 | 3 (1+1+1) | all full diff |
| Medium (500–1500 / 2 sections) | 2 | 4 (1+2+1) | 2 codex split 1/2 within-section; Claude+Gemini full |
| Large (1500+ / 3+ sections) | 3 | 5 (1+3+1) | 3 codex split 1/3 within-section; Claude+Gemini full |

> **Thresholds raised ×2.5–3 on 2026-06-18** (hypothesis, not yet
> validated): the old 200/500 triggers split too eagerly — one `gpt-5.6-sol`
> handles 500 lines fine, and premature splitting hits anti-pattern #1
> (N codex all on the full diff = duplicate coverage, no gain). New:
> 500 / 1500. Roll back to the old values if findings start slipping.
> (For per-slice the totals lose the Claude leg → `N+1` not `N+1+1`; a
> small per-slice diff = codex(full) + agy.)

**Strongest review model only** — Anthropic = **`claude-opus-4-8`**
(Opus 4.8; Step 2 is the authority — **cmr does not use Fable**, recorded
rule there), OpenAI `gpt-5.6-sol`;
**Gemini is the documented exception** (locked to 3.5 Flash via `agy` —
wiki trade-off: keep 3-vendor cross-family coverage over dropping the
Gemini leg entirely after the `gemini` CLI EOL).
**Never** dev-tier `gpt-5.3-codex-spark` / `claude sonnet-4.6` as a
reviewer (coding-tier model choice is a separate matter; do not carry
it into review).

> Orchestration law (2026-06-18, split by trigger point): the **Claude
> `Agent` leg can only be spawned by the main session** — a subagent
> cannot spawn the `Agent` tool (Claude Code does not expose it to
> subagents). So **ship-pre** review (which includes the Claude leg) is
> run by the **main session** as `N codex + Claude(Agent) + agy` =
> N+1+1. **per-slice** review is **NOT** run by the main session and has
> **no Claude**: every slice is implemented by a clean-context subagent
> (2026-06-19: the old main-session-self-run-small-slices exception is
> removed), so per-slice review **always** runs inside that subagent — a
> **nested layer** — as `N codex + agy` (N+1) with **every leg a Bash
> CLI** (nested Agent / native-subagent spawning is forbidden on both
> hosts). The native codex-subagent path exists **only for ship-pre** (the
> main-session top level). See Step 1 / wiki §谁跑 cmr.

## Step 2 — two-phase dispatch (wiki §并行启动, 2026-05-18 顺机理 reorder)

> **Two-phase applies ONLY to ship-pre** (main session orchestrates,
> Claude leg via the `Agent` tool). **per-slice does NOT use two-phase**
> — it is `N codex + agy` = 2-vendor, no Claude / no `Agent`, just the
> Bash CLIs run concurrently in the background (wiki §谁跑 cmr). For
> per-slice, do msg1 only (the bg Bash batch); there is no msg2.

The old "all reviewers in ONE assistant message" rule **fights the tool
mechanics** — Agent is synchronous foreground, Bash + `run_in_background:
true` is async background; mixing both in one message kept failing
(missed Gemini, accidental serialization, bg-Bash not actually
dispatched). Replaced with **two-phase 顺机理** that flows WITH the
mechanics (for the ship-pre / main-session-orchestrated case):

**msg1 — homogeneous async batch.** ONE assistant message containing
every Bash CLI reviewer tool call, ALL with `run_in_background: true`:

- Default (N=1): 1 × `Bash` (`backends/codex-review.sh`) + 1 × `Bash`
  (`backends/gemini.sh` — which calls `agy --sandbox --print ''`
  internally, see invocation forms) = **2 bg jobs**.
- Upgraded (N codex): N × `Bash` codex (section k/N, non-overlapping
  diff slices) + 1 × `Bash` `gemini.sh` (full diff) = **N+1 bg jobs**.

**msg2 — the very next message; first content MUST be the Agent call.**
1 × `Agent` tool call (Claude reviewer subagent, model = `opus` (Opus
4.8) per the Claude-reviewer invocation form below — cmr does not use
Fable; full-diff reviewer prompt). The Agent runs
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

> **Reasoning-effort reality, per leg** (wiki §调用规范) — the legs run
> at very different reasoning depths:
> - **codex** = `medium` uniformly for **ship-pre completeness/correctness
>   (spine Step 5/6)** and **per-slice** (user decision 2026-07-12;
>   `CMR_CODEX_EFFORT`, pinned via `-c` so host config cannot drift).
> - **Claude reviewer Agent** (ship-pre, main=Claude) = Opus 4.8 adaptive
>   default and **cannot be dialed up** — the `Agent` tool exposes no
>   effort param, and `ultrathink` in a subagent prompt is inert literal
>   text (claude-code#25669).
> - **Claude `claude -p`** (only main=Codex completeness one-pass, spine Step 5, now) = default
>   effort. **`--effort max` was RETRACTED** (2026-06-18): it does give
>   ≈5× depth, but `claude -p` billing on isolated/capped credit (the
>   6/15 policy is paused but may restart) burns 5× tokens too fast.
> - **agy / Gemini** = 3.5 Flash, no knob.
>
> Codex is explicitly pinned rather than inheriting host config.

- **Codex** — only via `backends/codex-review.sh` (pins `printf %s
  "$PROMPT" | codex exec --ephemeral -c
  model_reasoning_effort=medium --model gpt-5.6-sol - 2>&1`).
  **`--ephemeral` is mandatory** — cmr runs N codex in parallel; without
  it concurrent instances collide on `~/.codex/session` → cross-talk
  (prompt A surfaces in instance B's context). Wiki §额外硬规则 #6 /
  codex#11435. **The reasoning-effort pin is mandatory and uniform**
  (`CMR_CODEX_EFFORT=medium` for ship-pre and per-slice) —
  codex would otherwise inherit the machine's `~/.codex/config.toml`
  value and silently drift; `--selftest` guards the form. Never
  `codex exec "$(...)"` (hangs → pkill), never `-C <dir>` (wrong
  workdir), never `codex review --base B "PROMPT"` (can't pass both).
  *(main=Codex host only: the codex leg runs as a Codex **native
  subagent** with per-agent `model`/`model_reasoning_effort`/
  `developer_instructions`, NOT `codex exec` — but this native-subagent
  path is **ship-pre only** (top level); per-slice slices are always
  implemented by a clean-context subagent (nested, 2026-06-19), where
  subagent-spawning is forbidden, so the per-slice codex leg always falls
  back to `codex exec`. Wiki §主=Codex codex reviewer 腿走原生
  subagent, hypothesis. This skill executes main=Claude, where the codex
  leg is always `codex exec` via this backend.)*
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
  (esp. the completeness audit, spine Step 5) review from a non-hidden checkout.
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
  model = **`opus` (Claude Opus 4.8)**. This bullet is the ONE
  authoritative place for the Claude leg's model.
  - The model MUST be set **explicitly** on the `Agent` call — it does
    **NOT** inherit the session model. (A dev-tier session would
    otherwise silently drag the reviewer below the strongest-review-model
    rule; you got lucky only if the session itself ran Opus 4.8.)

  > **⚠ RECORDED RULE — cmr does NOT use Fable on any leg; the Claude leg
  > is Opus 4.8, period (user decision 2026-06-24).** Even when Claude
  > Fable 5 is available, cmr will not dispatch it: Fable's quota is too
  > scarce for a high-frequency review gate. This is a **deliberate
  > skill-vs-wiki divergence** — the wiki (§操作规程 model table) says "use
  > the strongest available Claude = Fable when up", which is the *ideal*;
  > the skill's *operational decision* is Opus 4.8. **Do NOT re-add Fable
  > on a wiki re-sync** (same standing-divergence handling as the agy
  > warm+retry). Revisit only if the user changes the decision.

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
  self-time-out on an **idle/hang** (`backends/codex-review.sh`:
  `CMR_CODEX_TIMEOUT` = seconds of NO output before kill, default 900s =
  15min — **not** a total wall-clock cap, so a codex still streaming runs
  as long as it needs; scoped kill of its own pid tree) and degrade
  automatically — you rarely need to intervene. If you must kill a hung
  reviewer, kill ONLY its specific pid; **never a global
  `pkill -f codex`** (msg1 launched N parallel codex reviewers — a global pkill
  takes the siblings down too). **Hang judgment = > 15min** of no
  stdout/stderr (user decision 2026-07-06; escalation history 3min →
  8min → 15min — deep reasoning / large diffs think silently for many
  minutes before the first byte, and an xhigh codex was false-killed at
  the 8min threshold too, twice. Wiki §额外硬规则 #4 was updated to
  15min the same day (vault `b5495e8`) — skill and wiki are in sync; do
  not regress either side on a re-sync. 900s matches agy's
  `--print-timeout 15m`, which gemini.sh already passes for the same
  reason). rate / quota / limit → the backend degrades and flags
  "本轮缺 X"; do not retry by hand.
- **Huge diff (> 10K lines): segment the prompt** to avoid saturating the
  pipe buffer (wiki §额外硬规则 #3). This is separate from the N-table
  (which scales reviewer *count*) — it is about not shoving a single
  >10K-line payload through one stdin pipe.

Findings channel: reviewers return their review as **prose** (the wiki
model — §「.result 是 review 文本」: a reviewer returns review text and
the orchestrator, an agent, reads it with judgment). There is **no
sentinel-JSON wrapper and no `extract_json` parse** — that gate was a
divergence from the wiki: it demanded the strongest reviewer's prose be a
JSON shape, and when codex/agy naturally answered in prose it was dropped
as "本轮缺 X", indistinguishable from an outage (the best reviewer
repeatedly lost over format). `prompts/cmr-reviewer.md` asks for grounded
prose ending in a `CMR-VERDICT: converged|findings` line. The backends
(`backends/codex-review.sh` / `gemini.sh`) pass a successful review
through and degrade (synthetic empty findings + nonzero exit + visible
"本轮缺 X" flag) **only on a true outage** — timeout, empty output, the
CLI exiting non-zero (auth/quota/crash), or agy keychain auth-race (after
4 attempts). codex-review.sh emits codex's **final message only** (via
`-o`/`--output-last-message`): codex's stdout is the full prompt echo +
reasoning trace (~1.5MB on a real diff), so we take its native
last-message file — a few KB, complete, no parser. (agy's `--print`
output has no such echo, so the Gemini leg needs no trimming.) A real prose review and a missing vendor
are thus cleanly distinguished; a failed vendor is always detectable,
never a silent zero-finding pass, and a real review is never dropped for
its format.

Prompt templates — **the lens you feed IS an executable prompt file, not
a prose instruction to improvise** (the earlier gap: the completeness lens
existed only as prose here, so a ship-pre run could only ever dispatch the
correctness prompt → the Step-5 completeness gate silently never ran):

- **`prompts/cmr-reviewer.md`** = the **correctness** lens (find real
  defects, P0–P4). Feed it for **per-slice** and the **ship-pre Step 6
  correctness gate**.
- **`prompts/cmr-completeness.md`** = the **completeness** lens (was the
  spec fully delivered? clause-by-clause DONE/PARTIAL/NOT-DONE +
  CONFORMS/VIOLATES/UNVERIFIED-GAP, chase the reference chain, **exercise
  behavioral keys**). Feed it for the **ship-pre Step 5 completeness gate**
  and for **design-doc (ADR/spec) review** (`mode doc`).
- **`prompts/cmr-fixer.md`** = the fixer (Step 7, the defer protocol).

Each is fed verbatim + the diff (+ the spec for the completeness lens).
They are templates, not control logic. A single invocation feeds **one**
lens (set by `--lens`, which the gate skills `ak-cmr-completeness` /
`ak-cmr-correctness` pass). A finished change runs the two gates as **two
skill invocations in order** — `ak-cmr-completeness` first (must reach
`CMR-VERDICT: complete`), then `ak-cmr-correctness` (§Step 0 «严禁合一»);
per-slice is correctness only.

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

> **No Fable rows here (decision 2026-06-24):** the Claude leg is Opus 4.8
> by decision — cmr never dispatches Fable (Step 2 is the authority, see
> the recorded rule there). So the old Fable-specific degrade rows (Fable
> safeguards auto-routing to Opus; the `fable` alias needing client
> v2.1.170+) no longer apply — there is no Fable leg to fall back FROM.
> Opus 4.8 is simply the Claude leg, not a degradation.

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
actual Claude **review** call (the main=Codex completeness one-pass, spine Step 5) is
`cat "$PROMPT_FILE" | claude -p --model claude-opus-4-8 --output-format
json --disable-slash-commands` — note three things: **(a)** pin
`--model claude-opus-4-8` (the Claude leg; cmr does not use Fable — Step 2
recorded rule) so a default-model drift can't
quietly downgrade the reviewer; **(b) NO `--effort max`** — it was
retracted (it gives ≈5× depth but `claude -p` billing on isolated/capped
credit burns too fast); **(c) NO `--tools ""`** — the tool-kill is ONLY
for the auth smoke; a reviewer must keep Read/Grep/Glob for grounded
review (one agy over-step in hundreds of reviews doesn't justify gutting
the grounding axis for all three — wiki §调用规范). The outside-voice
reviewer always stays the strongest in range (main = Claude → codex
`gpt-5.6-sol`; main = Codex → current strongest Claude or Gemini), never
dev-tier spark / 5.3-codex / sonnet. See wiki §降级链.

## Step 4 — merge + grade (agent judgment, not a deterministic engine)

Collect every reviewer's review by **reading each CLI's stdout directly**
— it is prose (or whatever the reviewer wrote); read it the way you would
a human reviewer's comment, taking its `CMR-VERDICT:` line and its
grounded findings. A backend that degraded (nonzero exit + "本轮缺 X")
is a MISSING vendor for this round, not an approve — do not count it as a
zero-finding concur. Then, as judgment:

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

**concur = no blocking finding.** A leg counts as approving
(`converged` / `complete`) iff it raised **no blocking finding** this
round — blocking = **P0 / P1 / P2** (correctness/per-slice and the
ship-pre completeness gate on code), **doc mode also P3** (only P4
exempt). A leg may still have raised — and MUST still report (交卷契约) —
**non-blocking** findings (P3/P4 in correctness/code mode; **P4 only** in
doc mode); those go to Deferred and do **not** cost its concur vote. In
doc mode P3 **is** blocking and **does** cost the concur vote (see the
first half of this paragraph — only P4 is exempt there). **P4 never
blocks in any mode.**

**Positive termination = two consecutive clear rounds** (ALL modes, not
just doc — 2026-07-12 user ratification). A round is **clear** when it
has no blocking finding, i.e. every non-degraded leg concurs by the
fractions below. One clear round no longer converges on its own: it is
the **qualifying round**, and the next round is a **full re-review
confirmation round**. Two consecutive clear rounds (qualifying +
confirmation) → converged, stop. A blocking finding in the confirmation
round → NOT converged: fix it and the early-stop arm **re-qualifies from
scratch** (a single clear round again becomes merely qualifying). The
fractions below describe what **one fully-concurring (clear) round**
requires by squad shape:

> **Doc mode is the explicit exception to all-legs-concur.** In
> correctness / code modes a round is clear only when **every** non-degraded
> leg concurs — no blocking finding from **any** leg. **Doc mode does NOT
> require all-legs-concur**: a doc-mode round is clear on **majority of
> legs judge `complete` AND the ledger — aggregating ALL legs' findings,
> including any leg that dissented from the majority-complete vote — shows
> zero blocking (P0/P1/P2/P3) findings of any classification
> (original-defect / fix-fix / invention all count toward blocking; the
> split is the bloat-line/ledger-audit trigger only, never the clear
> gate)**. Because the ledger clause
> spans **every** leg, a single dissenting leg's blocking finding keeps the
> ledger non-zero → the round is **NOT clear**, even under a majority-complete
> vote; the dissent cannot be swallowed. Both forms still need the two
> consecutive clear rounds above (doc mode's per-round form is defined in
> §Doc mode discipline ②(c)); the two forms are stated so they do not
> contradict.

- ship-pre / main=Claude default: **3/3 concur** (all reviewers approve).
- Upgraded 1+N+1, 3 vendors present: **(N+2)/(N+2) concur**.
- One vendor degraded (1+1+1 → 2 reviewers): **2/2 concur + flag**.
- **By-design 2-vendor (no Claude)**: **per-slice (both hosts)** and the
  **main=Codex correctness (spine Step 6)** are fixed `codex + agy` (Claude dropped for credit,
  Step 1 / wiki §谁跑 cmr) → **(N+1)/(N+1) concur + flag `不用 Claude
  (credit)`**, scored the same as a "missing 1 vendor" round. (ship-pre
  completeness (Step 5) and main=Claude correctness (Step 6) are still 1+1+1, not this row.)
- Upgraded-state single-vendor loss (1+N+1):
  - Claude **or** Gemini missing → N+1 reviewers: **(N+1)/(N+1) concur + flag**.
  - **All codex missing** → falls back to 1+0+1 = 2 reviewers (Claude + Gemini): **2/2 concur + flag `升级态缺 codex，已退化`**.
  - codex partial-instance loss (N→N′): **(N′+2)/(N′+2) concur + flag `codex 实例数 N→N′`**.
- Only 1 vendor ran (no outside voice — e.g. codex+gemini both down → Claude only; or claude+gemini both down → codex only): **NOT positive** — no cross-family check; needs human review or wait for vendor recovery.
  - > **Explicit exception: main=Codex per-slice / correctness (Step 6) + agy down → codex solo is POSITIVE, don't block.** Those scenarios are already Claude-less (`codex + agy`), and agy's small quota frequently 429s; when agy is the only one left and it drops, run **codex solo**, count it as positive termination, and flag `单腿 codex (agy down)，无 cross-vendor，质量降级` (optionally re-run when agy recovers, but do not stall the dev loop — waiting on agy isn't worth it). **This relaxation is ONLY here** — not for main=Claude / completeness (Step 5) / or when another cross-family vendor is still available.

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
blocking finding (P0/P1/P2; doc mode also P3)
  → FIX → MANDATORY self-check二连 (see below) → commit
          (note "自查二连 done") → next round (FULL re-review)
no blocking finding (round is CLEAR)
  → confirmation round (FULL re-review); two consecutive clear rounds
    (this one + the confirmation) → STOP (normal convergence).
    A blocking finding in the confirmation round → re-qualify from
    scratch (FIX, then a fresh clear round is needed again).
P3/P4 only  → do NOT block, do NOT by themselves trigger another fix
              round — a round with only P3/P4 (P4 in doc mode) counts as
              CLEAR regardless. That CLEAR status is ORTHOGONAL to whether
              they get FIXED: cheap/low-risk P3/P4 should still be FIXED
              now (fixer's SHOULD-fix-by-default rule, cmr-fixer.md; then
              self-check二连), NOT banked as backlog debt. Deferred is the
              narrow exception — the genuinely out-of-scope / needs-design
              / high-risk subset — and the 交卷契约 requires every P3/P4
              stay reported either way.
not converging / drift hit → STOP, architectural/implementation
              rework (Step 6), not "one more round"
```

> **After every fix, before the next round: the mandatory self-check
> 二连** (wiki §修复, 2026-06-18 — it used to be just a flowchart arrow
> and got skipped). Do NOT `commit → next round` straight from the fix;
> first do two checks and write a one-line "自查二连 done" in the commit
> msg (or the fix's closing line) so the decision is visible in the
> tool-call stream:
> 1. **Same-type check** — does the same error *pattern* appear elsewhere
>    in the current diff? (Reviewers aren't exhaustive in one round; the
>    same pattern is usually multi-site. Fix only the named site → the
>    next round trips on another → wasted rounds + codex credit.)
> 2. **Fix-introduced-bug check** — did the fix break a neighbor? (Change
>    A breaks B; a narrow fix most easily leaves a regression out of view.)
>
> This is a **cheap pre-filter before** the next round's independent
> review — it does NOT replace it (self-check < independent subagent,
> anti-pattern #3); it just picks the low-hanging fruit you can catch
> yourself instead of paying a whole round for it. **Mechanical fixes do
> it too** (esp. the same-type check — a typo'd label is usually typo'd
> elsewhere). Canonical: tdd-autonomous-dev §切片内纪律.

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
> non-trivial = you MUST invoke the `/diagnosing-bugs` skill (via the `Skill`
> tool, in allowed-tools) before reading or editing anything. This makes
> "skip /diagnosing-bugs" a visible, audited
> decision instead of a silent default — the silent default is exactly
> why real fixes almost never reach /diagnosing-bugs even though most should.

| Fix kind | Route |
|---|---|
| **Mechanical** — see the hard bar below; **must be explicitly declared + a one-line justification of why it qualifies** | edit directly, no further protocol |
| **Non-trivial** (behavioral / runtime / may-touch-neighbors / not-fully-understood / **anything not explicitly declared mechanical**) | the **first tool call MUST invoke the `/diagnosing-bugs` skill** (via the `Skill` tool) — not first grep, not first guess, not first write a patch, not first read a file. /diagnosing-bugs's 6 phases (feedback loop → reproduce → ranked falsifiable hypotheses → one-probe-at-a-time instrument → fix + regression test → cleanup, with a HITL fallback) are an iterative, possibly human-in-the-loop investigation the **main session** drives — it does not collapse into a single fixer-subagent return. Canonical: wiki §修复 + `matt-pocock-skills#/diagnosing-bugs`. |

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
breaks neighbors — exactly what /diagnosing-bugs exists to prevent. The
`cmr-fixer.md` subagent therefore produces **mechanical** diffs only
(by the hard bar above); non-trivial defects go back to the main session
for /diagnosing-bugs.

Self-check is mandatory and is NOT review — they are not
interchangeable (anti-pattern #3). The author scanning their own change
misses far more than an independent reviewer; the self-check only adds
the narrow "did my own fix regress / repeat a pattern" pass on top of
review, never instead of it.

**Defer protocol** (tdd-autonomous-dev §切片内纪律). Deferral is ONLY for
the **non-blocking tier** — **P3/P4** in correctness/code mode, **P4 only**
in doc mode (P3/low is blocking there). Three parts, none optional: ①
explicit **P3/P4** (doc mode: **P4** only) — not "minor" ② a specific 1–2
sentence reason (not generic) ③ accumulate to deferred staging;
`gstack-ship` lands it into the PR body `## Deferred Findings`
(`- [ ] [P3] <summary> — <reason> — <expected timing>`). A **blocking**
finding (P0/P1/P2; doc mode also P3) is NEVER deferred: it is
must-fix-or-route — mechanical fixes land now, non-trivial ones route to
the main session (`/diagnosing-bugs`). Trying to defer a blocking finding
= **not converged**: escalate to the user, do not silently stage it as
converged (P2→P3 down-ranking to escape is the same anti-pattern as
critical/high→medium).

## Doc mode discipline (design-text reviews — the additive-runaway defense)

> **⚠ RECORDED RULE — upstreamed to the wiki 2026-07-06 (user decision
> same day; vault `b5495e8` / `da04ff5` / `e06bcfe`).** Do
> NOT drop this section on a wiki re-sync (a re-sync from a stale wiki
> checkout would erase it; the golden-hash test enforces this). The
> round-gate value **10** restores cmr's original founding setting (it
> had been silently forgotten by later versions — which is exactly why
> these tests-pinned rules exist).

Applies **ONLY when the thing under review is a design text** (ADR /
spec / contract / plan — the Step 0 doc-mode bullet, completeness lens)
— **with ONE exception: ① (constitution packet + kill-axis) applies to
EVERY review mode, code-diff included (owner decision 2026-07-12; the
doc-ONLY scoping was an unratified editorial narrowing — the #604
closure machines entered a code-diff review exactly through the
unguarded suggestion channel and killed live family runs on
2026-07-12).** Code-diff mode keeps every OTHER rule unchanged.

**Why doc mode needs its own defense (evidence: #440).** A review of a
DESIGN TEXT is structurally **additive** — every finding suggests adding
text, every fix grows the reviewable surface. #440 ran 34 rounds: of 121
fixes, 7% fixed the original design, **58% fixed the review's own
earlier fixes**, 23% were mechanisms the review itself invented; the
text bloated 2.4×; at round 3, 3/4 legs had already judged `complete`
and the loop still ran ~30 more full rounds. **The Step 6 drift triple
never fired once in 34 rounds** — quantity drift watches "findings count
not decreasing", and a runaway doc review *resolves* findings every
round (count keeps falling) while the text grows and fixes fix fixes.
The triple is structurally blind to additive-text runaway, so doc mode
adds the defenses below. 标 vs 本: ①③ + the ledger are the **root**
fixes (they stop the runaway from being generated); the bloat line and
the round gate are **backstops** for when the roots fail.

### ① Constitution packet + kill-axis (root fix — ALL modes, not just doc)

Before round 1 of ANY review (doc mode AND code-diff mode — owner
decision 2026-07-12) the dispatcher MUST collect a **constitution
list** — the project's already-decided ADRs + the user's explicitly
stated principles — and put it on **page one of the review packet**.
For a code diff the check reads as: a finding or suggested fix that adds
a mechanism violating a ratified ADR (e.g. runner-side parsing /
validation / auditing of worker output content, against ADR 0062's
three-signal envelope) gets a **DELETE** recommendation, not a patch.
Every leg's prompt then carries a **second mission** (the doc-mode
addendum in `prompts/cmr-completeness.md`): besides finding what is
missing, find **mechanisms that violate the constitution or should not
exist at all** and recommend **DELETE**. A DELETE finding **outranks a
patch finding** on the same mechanism. Rationale: a completeness lens is
structurally add-only; subtraction must be explicitly licensed or the
review can only ever make the text longer.

### ② Fix-classification ledger + stop signals

- **(a) Ledger — the measuring instrument, lands first.** Every round
  intro MUST carry the previous round's fix classification:
  **original-defect / fix-fix / invention** (原始缺陷 / fix修fix / 加戏).
  Without the ledger none of the signals below is measurable.
- **(b) Bloat line = audit trigger, NOT a death line.** Reviewed text
  grows past **1.5×** its round-1 size → audit the ledger. Growth driven
  by original-defect fixes → legitimate: note it in the round report and
  continue (a genuinely complex design may lawfully grow). Growth driven
  by fix-fix / invention → STOP, escalate to the user with the ledger.
- **(c) Early stop via a FULL confirmation round (no #14 exception).**
  A round where the **majority of legs judge `complete`** AND the ledger —
  **aggregating ALL legs' findings, including any leg dissenting from the
  majority-complete vote** — shows **zero blocking (P0/P1/P2/P3) findings
  regardless of classification** (any classification — original-defect,
  fix-fix, or invention all count toward blocking; the
  original-defect/fix-fix/invention split is for ②(b)'s
  bloat-line/ledger-audit trigger only, never for filtering the
  clear/convergence gate) (only P4 exempt; P4 clarity
  reported-but-Deferred, doesn't block the confirmation round) → the next
  round is a **confirmation round that is still a FULL re-review**
  (anti-pattern #14 stays fully intact — the spot-check variant was
  considered and rejected: one full round costs nothing against the ~30
  wasted ones it prevents, and it keeps the fresh-full-read guarantee).
  Confirmation round again majority-complete **AND the ledger (again
  spanning ALL legs, dissenters included) again showing zero blocking
  (P0/P1/P2/P3) findings regardless of classification** (any
  classification — original-defect, fix-fix, or invention all count toward
  blocking; the split is ②(b)'s bloat-line/ledger-audit trigger only, never
  the clear/convergence gate) (only P4 exempt; P4 clarity
  reported-but-Deferred, doesn't block the confirmation round) →
  **converged, stop**. Because the zero-blocking check spans every leg AND
  counts blocking findings of every classification, a single dissenting
  leg's blocking finding (original-defect, fix-fix, or invention — all
  count) keeps the ledger non-zero → NOT converged **regardless of the
  majority-complete vote**:
  fix it and the loop continues (the early-stop arm must re-qualify from
  scratch — bare majority-complete never converges on its own, or the
  dissenting leg's real finding gets swallowed).
- **(d) Round gate at 10 — an escalation checkpoint, NOT a hard cap.**
  Doc mode reaching **round 10** without convergence → stop dispatching
  and **escalate to the user with the ledger + current state**; the user
  rules "genuinely complex — continue" (the loop resumes, next window)
  or "runaway — close". Never a silent stop, never auto-terminate. A
  #440-style ledger (58% fix-fix) indicts itself; a genuinely complex
  design is not framed by the number. Code/correctness mode keeps the
  no-cap rule (`3 rounds is not a hard cap`, Step 6) unchanged — there
  the drift triple CAN see runaway; here it demonstrably cannot.

### ③ Anti-minutes-ification (fix output discipline)

A design-text fix **changes the conclusion** — it does not append
per-round argumentation to the doc/issue body. Argumentation and history
go to comments or the review ledger. Body length defaults to
**decrease-only**; an increase requires a stated justification in the
round report. (#440's bloat engine was exactly per-fix mechanism prose
appended to the body — every append enlarged the attackable surface.)

### ④ Dead-leg standing degrade

A leg returning empty / 429 / an error pattern is DEGRADED for the round
(Step 3 flag + out of the concur denominator — already the rule). Doc
mode adds: **2 consecutive dead rounds → stop re-dispatching that leg**;
mark **`standing-DEGRADED`** in every subsequent round report (never
counted as a zero-finding approve); re-probe it once at the ②(d)
escalation checkpoint — recovered → rejoin. (Evidence: #440's gemini leg
429'd empty for six late rounds and was re-dispatched and awaited every
single time.)

### ⑤ Fix self-check becomes 三连

Doc mode extends Step 7's mandatory self-check 二连 with a third check
before commit: **does the fix's mechanism itself actually hold, and does
it introduce no new contradiction with sibling issues / other fixes?**
(#440 round 33: 3 of 4 findings were bugs in previous rounds' fixes —
the cheapest whole-round saver in the set.)

## Anti-patterns (wiki §反模式 — refuse these)

1. N codex all on the full diff (N>1 must split sections — duplicate findings, no coverage gain).
2. No cross-family reviewer (only Claude / only codex) — single family cannot break section silos.
3. Self-scan instead of an independent subagent — author bias, high miss rate. Self-check ≠ review.
4. Same-family different-size as "outside voice" (Opus + Sonnet) — not cross-vendor.
5. Hardcoded N=3 ignoring diff size.
6. **Two-phase dispatch violations** (**ship-pre only** — the two-phase rule governs the main-session-orchestrated case where Claude runs via `Agent`; per-slice is `codex + agy` 2-Bash with no Agent, so it doesn't apply) — peeking at any CLI output between msg1 and msg2, or emitting anything other than the Agent call as msg2's first content, or mixing Agent + Bash in a single message (the old 逆机理 rule the two-phase replaced). All collapse to silent serialization.
7. Drift hit → rationalize "one more round" — the infinite-loop entrance.
8. Silent vendor degrade — always flag "本轮缺 X".
9. v2 N × Claude (opus) split sections — violates current quota allocation.
10. Treating N/N concur as ship-ready — category error (Step 5).
11. `gemini -p` headless (CLI stopped serving 2026-06-18) or `agy --dangerously-skip-permissions` (re-consents high scope, breaks headless auth) — use `backends/gemini.sh`, which pins `agy --sandbox --print ''` + the warm-retry recipe. Also dead: `agy -p --sandbox` (1.0.7 flag-parse made `-p` swallow `--sandbox` as the prompt value → sandbox never engaged).
12. **A reviewer that writes** — relying on `--sandbox` alone to keep an agentic CLI (agy) read-only. It edits files / runs commands anyway (first-run: rewrote tracked files + ran pytest mid-review). The prompt MUST forbid writes ("REVIEW ONLY, do not modify any file, do not run commands"); a review that mutates the repo under review is the defect, even when the mutation is correct.
13. **Over-claiming "mechanical" to skip /diagnosing-bugs** — waving a fix through as mechanical on "it's simple / one line / obvious / I'm confident." Default is non-trivial; mechanical is a closed high-bar allowlist that touches zero executing code (Step 7). A changed flag / guard / condition / quoting fix is non-trivial no matter how small. Skipping classification = non-trivial = `/diagnosing-bugs` required.
14. **Narrowing a later round into a "did last round's P1 close?" spot-check** — every round must full-re-review the current full diff; prior-finding acceptance is only a tail item. Narrowing drops the regression the fix introduced + the surface last round missed, and fakes a low finding count that breaks the Step 5/6 convergence read. See Step 7 "Every round = full re-review."
15. **Static-reading a behavioral gate counts as reviewing it** (wiki §反模式 #11, 2026-06-23) — for a load-bearing **gate / fix-loop / guard / state-machine**, "looks right / matches spec / tests pass" CANNOT tell a real gate from a **hollowed-out** one (same-looking code, both return `converged`). Such mechanisms MUST be **exercised**: run it, inject a known defect, and assert the mechanism actually fires (a cmr gate: a planted cross-slice bug must drive **catch → fix → re-cmr → concur**; if it still returns `converged` with the poison in, the gate is fake). The author's green tests are NOT evidence (coding-author blind spot). Worst case — 2-3 reviewers sharing one "review the diff" prompt all do static reads and all miss the behavioral defect (input-bias; cross-model can't fix it — change the prompt to "run the gate / verify behavior", not "read the diff"). Evidence: #330 (an orchestrator's integration cmr hollowed to a single no-loop pass slipped past a 2-3-model Step 5). Wiki [[verification-scope-vacuum]] + [[reviewer-as-system-under-test]].
