# ak-cross-m-review

Local, pre-PR **cross-model review** skill — the executable form of the
wiki's `cross-model-review.md`. Dispatches an independent multi-vendor
reviewer squad against a diff in a **two-phase 顺机理 dispatch** (msg1 =
all CLI Bash reviewers in the background; msg2 = the Claude Agent), then
merges, grades, drift-checks and loops **as the agent judgment the wiki
prescribes** — before code reaches a PR / `main`.

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
and wiki disagree, the wiki wins.

## The vendor squad — N+1+1

Dispatched **two-phase** (wiki §并行启动, 2026-05-18 顺机理 reorder),
against the same diff:

- **1 × Claude Opus** — via the `Agent` tool as an independent subagent
  (zero context contamination). This is why the skill MUST run in the
  **main session**: Claude Code does not expose `Agent` to subagents.
- **N × Codex** (`gpt-5.5`, via `backends/codex-review.sh`) — N scales
  with diff size (1 / 2 / 3 for `<200` / `200–500` / `500+` lines); for
  N≥2 each codex takes a distinct file-section slice.
- **1 × Gemini** (via `backends/gemini.sh`, which internally calls
  `agy -p --sandbox` — Antigravity CLI 1.0.0, the in-kind replacement
  after the original `gemini` CLI's 2026-06-18 EOL; locked to Gemini
  3.5 Flash, the explicit exception to "strongest review model") —
  full diff.

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

```
/ak-cross-m-review [--base BRANCH] [--range A..B] [--diff FILE]
                   [--scenario per-slice|ship-pre]
```

- `--base` — base branch for the cumulative diff (default `main`,
  fallback `master`).
- `--range` — explicit `A..B` commit range (one slice's commits).
- `--diff` — review a pre-computed diff file.
- `--scenario` — `per-slice` (tdd spine step 4, within-slice lens) or
  `ship-pre` (step 5, cross-slice cumulative diff vs base).

There is no `--rounds` cap: the wiki's drift detection decides when to
stop, not a round counter.

```bash
/ak-cross-m-review --scenario ship-pre
/ak-cross-m-review --range HEAD~3..HEAD --scenario per-slice
/ak-cross-m-review --diff /tmp/change.diff
```

## What ships in this repo

```
SKILL.md                  the executable wiki transcription (the skill)
backends/codex-review.sh  pins the correct `codex exec` invocation
                          (no -C, stdin pipe, 2>&1) + clean degrade;
                          --selftest is its regression guard
backends/gemini.sh        calls `agy -p --sandbox` (post-EOL gemini
                          replacement) + warm + retry × 4 around agy's
                          keychain auth-race; visible degrade flag
lib/extract_json.py       salvage findings JSON from noisy CLI stdout
prompts/cmr-reviewer.md   reviewer prompt template
prompts/cmr-fixer.md      fixer prompt template (3-part defer protocol)
```

That is the whole surface. Merge / drift / termination are performed by
the agent per the wiki signals — there is intentionally no `merge.py` /
`drift.py` deterministic engine (removed in 0.2.0.0; it was the source
of the recurring orchestration bugs and contradicted the wiki's
"this is judgment, thresholds are non-portable").

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
  CLI (`agy` 1.0.0) — Gemini leg, the in-kind replacement after Google's
  `gemini` CLI 2026-06-18 EOL. Locked to Gemini 3.5 Flash; has a
  documented keychain auth-race the backend works around with warm +
  retry × 4 (upstream issue google-antigravity/antigravity-cli#51).
- `python3` ≥ 3.11 — `lib/extract_json.py`
- `jq` — shell pipelines

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

## License

MIT. See [LICENSE](./LICENSE).
