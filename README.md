# ak-cross-m-review

Local, pre-PR **cross-model review** skill — the executable form of the
wiki's `cross-model-review.md`. Dispatches an independent multi-vendor
reviewer squad against a diff — **ship-pre** in a **two-phase 顺机理
dispatch** (msg1 = all CLI Bash reviewers in the background; msg2 = the
Claude Agent), **per-slice** as just the Bash CLIs (`codex + agy`, no
Claude) — then merges, grades, drift-checks and loops **as the agent
judgment the wiki prescribes** — before code reaches a PR / `main`.

**Status**: v0 prototype. Evolving.

## Why this exists

The agent following the wiki's cross-model-review prose by hand drifts:
it serializes the parallel launch, picks a dev-tier reviewer model,
silently degrades when a vendor is down, or rationalizes "one more
round" past a drift signal. This skill is a tight, faithful transcription
of that wiki step so the agent runs it the **same way every time**
instead of re-deciding by feel.

It is **not** a re-implementation of the wiki as a program. The wiki
explicitly frames merge / grade / drift / termination as agent
*judgment* (any numeric thresholds are proto-calibrated, non-portable).
The skill keeps it that way: prose procedure + thin invocation guards
for the real CLI footguns, nothing more. Single source of truth:
`~/WorkSpace/vault/ak-cc-wiki/wiki/concepts/cross-model-review.md`
(defer + cross-slice discipline in `tdd-autonomous-dev.md`). If skill
and wiki disagree, the wiki wins — except blocks marked ⚠ RECORDED RULE
/ RECORDED divergence (deliberate, user-decided divergences; reconcile
those by their decision record, never silently overwrite them wiki-ward).

## The vendor squad — N+1+1 (ship-pre) / N+1 (per-slice)

The squad depends on the trigger point (wiki §谁跑 cmr, 2026-06-18):
**ship-pre** = the full `N codex + Claude + agy` (N+1+1), dispatched
two-phase by the main session; **per-slice** = `N codex + agy` (2-vendor,
**no Claude** — `claude -p` credit is too tight for the high-frequency
per-slice gate, so Claude is concentrated to the single ship-pre run).
Against the same diff:

- **1 × Claude reviewer** (**ship-pre only**) — via the `Agent` tool as
  an independent subagent (zero context contamination), model =
  **`claude-opus-4-8`** (Opus 4.8). **cmr does not use Fable** (quota
  scarcity) — a deliberate skill-vs-wiki divergence recorded in SKILL.md
  Step 2. Set the model explicitly — it does not inherit the session
  model. This is why the skill MUST run in the
  **main session**: Claude Code does not expose `Agent` to subagents.
- **N × Codex** (`gpt-5.6-sol`, via `backends/codex-review.sh`) — N scales
  with the diff's **effective** (core-logic) line count, excluding
  test/fixture/lock/doc noise (1 / 2 / 3 for `<500` / `500–1500` /
  `1500+`; thresholds raised ×2.5–3 on 2026-06-18); for N≥2 each codex
  takes a distinct file-section slice. Reasoning effort is uniformly
  `medium` for ship-pre and per-slice.
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

There is no `--rounds` cap: the wiki's drift detection decides when to
stop, not a round counter.

```bash
/ak-cross-m-review --scenario ship-pre
/ak-cross-m-review --range HEAD~3..HEAD --scenario per-slice
/ak-cross-m-review --diff /tmp/change.diff
```

## What ships in this repo

```
SKILL.md                  the engine — the executable wiki transcription
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
agent reads / merges / drift-checks / terminates per the wiki signals —
there is intentionally no deterministic engine: no `merge.py` / `drift.py`
(removed in 0.2.0.0) and, since 0.3.9.0, no `lib/extract_json.py`
sentinel-JSON parser either. That parser demanded the strongest
reviewer's prose be a JSON shape and dropped it as a phantom outage when
it wasn't — the same over-formalization, one layer down, that the wiki
warns against ("this is judgment, thresholds are non-portable").

## Origin

This repo began as a *grounded-review* prototype:
[Akagilnc/ai-blogger-lab#50][i50] and [garrytan/gstack#973][i973] — an
attempt to add a Grounded Review rule to `CLAUDE.md` as prose. It
evolved, over-built into a deterministic review engine, then was cut
back to what it should always have been: a faithful, compact executable
of the wiki's cross-model-review step.

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
- `jq` — shell pipelines
- `python3` ≥ 3.11 — **tests only** (`pytest`); the backends no longer
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
- **Reviewer read-only is prompt-enforced, not sandbox-hard.** Reviewers
  are told (in `cmr-reviewer.md` + the agy prompt preamble) not to modify
  files or run commands, but `agy --sandbox` does not actually block
  workspace writes — agy is agentic. First run (before the preamble) it
  rewrote tracked files + ran pytest mid-review. The preamble lowers the
  odds but cannot guarantee it (same ceiling as the two-phase no-peek
  invariant — prompt discipline, not a hard lock). Observed since: a
  couple of clean runs with no stray writes — a positive signal, not
  proof. Practical guard: glance at `git status` after a review; an
  unexpected tracked change is the preamble failing, and the real fix
  would be an upstream agy write-blocking sandbox (out of skill scope).

## License

MIT. See [LICENSE](./LICENSE).
