# ak-cross-m-review

Local, pre-PR **cross-model review** skill. `SKILL.md` together with its
disclosed file `DOC-MODE.md` is the standalone authority. It dispatches
an independent multi-vendor
reviewer squad against a diff — **ship-pre** in a **two-phase 顺机理
dispatch** (msg1 = all CLI Bash reviewers in the background; msg2 = the
Claude Agent), **per-slice** as just the Bash CLIs (main=Claude:
`codex + agy`; the host minimum-leg guarantee applies — `SKILL.md`
Step 1) — then merges, grades, drift-checks and loops through **agent
judgment** — before code reaches a PR / `main`.

**Status**: v0 prototype. Evolving.

## Why this exists

An agent following cross-model-review prose by hand drifts:
it serializes the parallel launch, picks a dev-tier reviewer model,
silently degrades when a vendor is down, or rationalizes "one more
round" past a drift signal. This skill keeps the procedure tight so the
agent runs it the **same way every time**
instead of re-deciding by feel.

It is **not** a deterministic review program. Merge / grade / drift /
termination remain agent *judgment* (numeric thresholds are
proto-calibrated, non-portable): prose procedure + thin invocation guards
for the real CLI footguns, nothing more. The historical origin is
`~/WorkSpace/vault/ak-cc-wiki/wiki/concepts/cross-model-review.md`
(with defer + cross-slice discipline from `tdd-autonomous-dev.md`). There
is no automatic sync since 2026-07-13 (ADR 0002), and both sides may
diverge. Blocks marked ⚠ RECORDED RULE / RECORDED divergence are the
user-adjudication ledger; only the user may change them.

## The vendor squad — N+1+1 (ship-pre) / N+1 (per-slice)

The squad depends on the trigger point (recorded decision, 2026-06-18;
its old credit rationale is superseded 2026-07-14 by the **host
minimum-leg guarantee**, `SKILL.md` Step 1): **ship-pre** = the full
`N codex + Claude + agy` (N+1+1), dispatched two-phase by the main
session; **per-slice** = `N codex + agy` (2-vendor **by design** — the
codex leg satisfies the main=Claude minimum). Every squad must carry at
least one strong other-family leg: main=Claude → a codex `gpt-5.6-sol`
leg; main=Codex → a Claude `opus` leg (headless `claude -p` in nested
contexts — so main=Codex per-slice / Step-6 correctness is 1+1+1, no
longer `codex + agy`); any other host → at least one of codex / Claude.
**agy unavailable → the Gemini leg is substituted by grok** (`grok-4.5`,
`--reasoning-effort high`, local `grok` CLI; xAI, not Google-family
diversity — `SKILL.md` Step 3). Against the same diff:

- **1 × Claude reviewer** (**ship-pre via `Agent`**; main=Codex also
  carries a per-slice Claude leg in the headless `claude -p` Bash form —
  `SKILL.md` 宿主替换表) — via the `Agent` tool as
  an independent subagent (zero context contamination), model =
  **`claude-opus-4-8`** (Opus 4.8). **cmr does not use Fable** (quota
  scarcity) — a user-adjudicated rule recorded in `SKILL.md` Step 2
  (historically a skill-vs-wiki divergence). Set the model explicitly —
  it does not inherit the session
  model. This is why the skill MUST run in the
  **main session**: Claude Code does not expose `Agent` to subagents.
- **N × Codex** (`gpt-5.6-sol`, via `backends/codex-review.sh`) — N scales
  with the diff's **effective** (core-logic) line count, excluding
  test/fixture/lock/doc noise (1 / 2 / 3 for `<500` / `500–1500` /
  `1500+`; thresholds raised ×2.5–3 on 2026-06-18); for N≥2 each codex
  takes a distinct file-section slice. Operational authority:
  `SKILL.md` Step 2 **Reasoning-effort contract**. To override, set
  `CMR_CODEX_EFFORT=<value>`.
- **1 × Gemini** (via `backends/gemini.sh`, which internally calls
  `agy --sandbox --print ''` — Antigravity CLI, the in-kind replacement
  after the original `gemini` CLI's 2026-06-18 EOL; locked to Gemini
  3.5 Flash, the explicit exception to "strongest review model") —
  full diff. (Not the old `agy -p --sandbox`: agy 1.0.7 made `-p`
  swallow `--sandbox` as the prompt value, so sandbox never engaged.)

The dispatch is **two-phase**: msg1 sends every CLI Bash reviewer in one
assistant message, all `run_in_background: true`; msg2 (immediately,
first content) sends the Claude `Agent`. No peeking at CLI output
between — the orchestrating session has zero results in hand when the
Claude reviewer is dispatched, preserving both concurrency and
independence. The older "all reviewers in one message" rule fought the
Agent / Bash tool asymmetry (Agent is foreground / blocking, Bash with
`run_in_background` is async) and kept silently serializing in practice.

The agent then **merges + grades** (group same issue across reviewers;
concurrence → severity up; grounding density → trust weight, only up),
checks the **drift triple** (count not decreasing / new class / off-core
→ STOP and rework, not patch), and loops fix → narrow self-check →
commit until `concur` or a drift stop. `concur ≠ done` — it means the
correctness lens is exhausted, not ship-ready. No deterministic merge or
drift engine: that was the over-formalization this skill deliberately
does not carry.

## Usage

There are **two named gate skills** — pick the one that names what you
mean, so the lens is always explicit:

- **`ak-cmr-correctness`** — the correctness gate (find real defects, P0–P4).
  Per-slice, and the second ship-pre gate.
- **`ak-cmr-completeness`** — the completeness gate (was the spec fully
  delivered? + exercise the behavioral keys). The first ship-pre gate
  (Step 5), and design-doc review.

On a finished change run `ak-cmr-completeness` first (it must reach
`CMR-VERDICT: complete`), then `ak-cmr-correctness`. Each is a thin wrapper
over the engine below; install all three with `scripts/install-skills.sh`.

The engine itself:

```
/ak-cross-m-review [--base BRANCH] [--range A..B] [--diff FILE]
                   [--scenario per-slice|ship-pre]
                   [--lens completeness|correctness]
```

- `--base` — base branch for the cumulative diff (default `main`,
  fallback `master`).
- `--range` — explicit `A..B` commit range (one slice's commits).
- `--diff` — review a pre-computed diff file.
- `--scenario` — `per-slice` (tdd spine step 4, within-slice) or
  `ship-pre` (step 5–6, cross-slice cumulative diff vs base).
- `--lens` — `correctness` (default) or `completeness`; the **internal**
  switch the two gate skills set. One invocation runs one lens. Prefer the
  named gate skills over setting this by hand.

There is no `--rounds` cap: the skill's drift procedure decides when to
stop, not a round counter.

```bash
/ak-cross-m-review --scenario ship-pre
/ak-cross-m-review --range HEAD~3..HEAD --scenario per-slice
/ak-cross-m-review --diff /tmp/change.diff
```

## What ships in this repo

```
SKILL.md                  the engine — standalone authority together with
                          its disclosed file DOC-MODE.md
DOC-MODE.md               doc-mode ②–⑤ discipline (SKILL.md Step 0 requires
                          Read before doc-mode dispatch)
skills/ak-cmr-completeness/  the completeness gate (thin named wrapper →
                          engine with --lens completeness)
skills/ak-cmr-correctness/   the correctness gate (thin named wrapper →
                          engine with --lens correctness)
scripts/install-skills.sh symlinks all three into ~/.claude/skills/
backends/codex-review.sh  pins the correct `codex exec` invocation
                          (--ephemeral, no -C, stdin pipe, 2>&1) via a
                          single CODEX_CMD array; emits codex's final
                          message only (via -o/--output-last-message — a
                          few KB, not the ~1.5MB stdout echo+trace),
                          degrades only on a true outage; --selftest is
                          its regression guard
backends/gemini.sh        calls `agy --sandbox --print ''` (post-EOL
                          gemini replacement) + warm + retry × 4 around agy's
                          keychain auth-race; passes the review through,
                          visible degrade flag on outage only
prompts/cmr-reviewer.md   correctness lens — find real defects (P0–P4);
                          per-slice + ship-pre Step 6
prompts/cmr-completeness.md  completeness lens — was the spec fully
                          delivered? clause-by-clause DONE/PARTIAL +
                          CONFORMS/VIOLATES/UNVERIFIED-GAP, chase the
                          reference chain, exercise behavioral keys;
                          ship-pre Step 5 + design-doc review
prompts/cmr-fixer.md      fixer prompt template (defer protocol)
```

That is the whole surface. Reviewers return a **prose** review and the
agent reads / merges / drift-checks / terminates per the skill's signals —
there is intentionally no deterministic engine: no `merge.py` / `drift.py`
(removed in 0.2.0.0) and, since 0.3.9.0, no `lib/extract_json.py`
sentinel-JSON parser either. That parser demanded the strongest
reviewer's prose be a JSON shape and dropped it as a phantom outage when
it wasn't — the same over-formalization, one layer down, that this skill
rejects ("this is judgment, thresholds are non-portable").

## Origin

This repo began as a *grounded-review* prototype:
[Akagilnc/ai-blogger-lab#50][i50] and [garrytan/gstack#973][i973] — an
attempt to add a Grounded Review rule to `CLAUDE.md` as prose. It
evolved, over-built into a deterministic review engine, then was cut
back to what it should always have been: a compact standalone skill whose
lineage is the wiki's cross-model-review step.

[i50]: https://github.com/Akagilnc/ai-blogger-lab/issues/50
[i973]: https://github.com/garrytan/gstack/issues/973

## Dependencies

- [Claude Code](https://claude.com/claude-code) CLI (`claude`) — the
  Claude reviewer runs via the `Agent` tool
- [OpenAI Codex](https://github.com/openai/codex) CLI (`codex`)
- [Google Antigravity](https://github.com/google-antigravity/antigravity-cli)
  CLI (`agy`) — Gemini leg, the in-kind replacement after Google's
  `gemini` CLI 2026-06-18 EOL. Locked to Gemini 3.5 Flash; has a
  documented keychain auth-race the backend works around with warm +
  retry × 4 (upstream issue google-antigravity/antigravity-cli#51).
- `python3` ≥ 3.12 — **tests only** (`pytest`); the backends no longer
  call Python at runtime (the `extract_json.py` parser was removed)

All three CLIs are subscription-authed in the author's setup; no API
keys needed.

## Limitations / boundary

- **Layer 1 only** (local, pre-PR). Does not replace Layer 3
  (`pr-review-loop`) or the ship Red Team. `concur ≠ done`.
- **No grounded single-file fact-gate.** Cross-model reviewers share
  training bias and rubber-stamp shared hallucinations. Content PRs with
  user-facing fact claims (dates/names/stats/security) need an
  independent grounded fact-check FIRST — that gate is **not** in this
  repo.
- Does not commit / push / open a PR — the caller (or `gstack-ship`)
  does. One change set per invocation.
- **Reviewer no-modify/no-fix is prompt-enforced, not sandbox-hard.** Reviewers
  are told (in both lens prompts + the agy prompt preamble) not to modify
  the reviewed repo or fix findings themselves; they may run inspection and
  verification commands. `agy --sandbox` does not actually block
  workspace writes — agy is agentic. First run (before the preamble) it
  rewrote tracked files mid-review. The preamble lowers the
  odds but cannot guarantee it (same ceiling as the two-phase no-peek
  invariant — prompt discipline, not a hard lock). Observed since: a
  couple of clean runs with no stray writes — a positive signal, not
  proof. Practical guard: glance at `git status` after a review; an
  unexpected tracked change is the preamble failing, and the real fix
  would be an upstream agy write-blocking sandbox (out of skill scope).

## License

MIT. See [LICENSE](./LICENSE).
