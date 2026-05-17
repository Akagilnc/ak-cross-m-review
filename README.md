# ak-cross-m-review

Local, pre-PR **cross-model review** skill. Dispatches an independent
multi-vendor reviewer squad against a diff, merges findings with
consensus + grounding-density weighting, runs a deterministic
drift/termination check, and loops a fixer pass until the correctness
lens is exhausted — before code reaches a PR / `main`.

**Status**: v0 prototype. Evolving.

## Why this exists

In-session subagent review and `gstack-review` / `gstack-codex`
single-pass review miss a distinct class of defect: **claims that
contradict the actual source, math that was never computed, CLI flags
that do not exist, APIs guessed from memory, and cross-slice
inconsistencies that no single-pass reviewer sees.**

A single reviewer — even a strong one — shares the author's blind spots.
The fix is *heterogeneous outside voices*: different model families,
each able to grep source, run `python3` for math, and shell out
`<tool> --help`, reviewing the same diff in parallel, with consensus
driving severity and a computed (not felt) termination verdict.

This skill is the executable form of the wiki's
`~/WorkSpace/vault/ak-cc-wiki/wiki/concepts/cross-model-review.md`
(Step 2.4 / 2.6 of the autonomous TDD loop). The wiki is the source of
truth; `SKILL.md` transcribes its hard rules into a loop so every
session runs it the same way instead of re-deciding by feel.

## The vendor squad — N+1+1

In one parallel message, against the same diff:

- **N × Codex** (`gpt-5.5`, via `backends/codex-review.sh`) — N scales
  with diff size (1 / 2 / 3 for `<200` / `200–500` / `500+` changed
  lines); for N≥2 each codex gets a distinct file-section slice.
- **1 × Claude Opus** — spawned via the `Agent` tool as an independent
  subagent (zero context contamination). This is why the skill MUST run
  in the **main session**: Claude Code does not expose `Agent` to
  subagents, so the loop cannot be delegated.
- **1 × Gemini** (via `backends/gemini.sh`, `auto_edit` + retry) — full
  diff.

Findings from every reviewer merge via `lib/merge.py` on two independent
trust axes: **concur** (cross-vendor consensus → severity upgrade) and
**grounding density** (count of real verification tool calls in a
finding → severity floor boost). `lib/drift.py` then computes a
deterministic drift/termination verdict that drives the loop; a fixer
subagent proposes a unified diff per round, which the user approves
before it is applied with `git apply`.

## Usage

```
/ak-cross-m-review [--base BRANCH] [--range A..B] [--diff FILE]
                   [--mode doc|code|auto] [--rounds N]
                   [--scenario per-slice|ship-pre]
```

- `--base` — base branch for the cumulative diff (default `main`,
  fallback `master`).
- `--range` — explicit `A..B` commit range (e.g. one slice's commits);
  overrides `--base`.
- `--diff` — review a pre-computed diff file instead of computing one.
- `--mode` — `auto` (default): `doc` if the diff is >70% `.md`, else
  `code`.
- `--rounds` — max reviewer→fixer iterations (default `3`; the wiki
  3-round cap).
- `--scenario` — `ship-pre` (default; cumulative diff vs base) or
  `per-slice` (one slice's range, within-slice lens).

### Examples

```bash
/ak-cross-m-review                                   # ship-pre, diff vs main, 3 rounds
/ak-cross-m-review --range HEAD~3..HEAD --scenario per-slice
/ak-cross-m-review --base develop --rounds 2
/ak-cross-m-review --diff /tmp/change.diff --mode code
```

## Architecture

```
/ak-cross-m-review entry (SKILL.md, main session only)
  │
  ├─ Step 0: arg/env check + lib & backend selftests
  ├─ Step 1: build diff vs base/range, size it → N table (N+1+1)
  ├─ Step 2 (per round, ONE parallel message):
  │   ├─ 1 × Agent (Claude opus reviewer)  ── independent subagent
  │   ├─ N × backends/codex-review.sh       ── corrected codex invocation
  │   ├─ 1 × backends/gemini.sh             ── gemini auto_edit
  │   ├─ lib/extract_json.py → per-vendor findings JSON
  │   ├─ lib/merge.py        → merged.json (concur + grounding boost)
  │   ├─ lib/drift.py        → computed drift/termination verdict
  │   ├─ fixer subagent (prompts/cmr-fixer.md) → unified diff + deferrals
  │   └─ user approves → git apply; deferrals persisted (PR body / DEFERRED.md)
  └─ Step 3: final report (+ "concur ≠ done" gate-lens reminder)
```

Prompts: `prompts/cmr-reviewer.md`, `prompts/cmr-fixer.md`.
Run artifacts: `outputs/cmr-<timestamp>/round-<N>/`.

## Origin

This repo began as a *grounded-review* prototype:
[Akagilnc/ai-blogger-lab#50][i50] and [garrytan/gstack#973][i973] —
an attempt to add a Grounded Review rule to `CLAUDE.md` as prose. The
rule failed adversarial review three times with structural findings; the
meta-conclusion was that prose rules cannot enforce machine-verifiable
artifacts, and the correct form is a scriptable skill. That work evolved
into the v3 vendor-squad cross-model review skill this repo now ships.

[i50]: https://github.com/Akagilnc/ai-blogger-lab/issues/50
[i973]: https://github.com/garrytan/gstack/issues/973

## Dependencies

- [Claude Code](https://claude.com/claude-code) CLI (`claude`) — the
  Claude reviewer/fixer run via the `Agent` tool
- [OpenAI Codex](https://github.com/openai/codex) CLI (`codex`)
- [Google Gemini](https://github.com/google-gemini/gemini-cli) CLI (`gemini`)
- `python3` ≥ 3.11 — `lib/merge.py`, `lib/drift.py`,
  `lib/extract_json.py` (the main loop's core; `lib/apply_diff.py` is
  retained but intentionally not used by the v3 loop — see SKILL.md 2f)
- `jq` — shell pipelines

All three CLIs are subscription-authed in the author's setup; no API
keys needed.

## Limitations / boundary (v0)

- **Layer 1 only** (local, pre-PR). It does not replace Layer 3
  (`pr-review-loop`, the post-push bot review) or the ship Red Team.
  `concur ≠ done` — N/N concurrence means the correctness lens is
  exhausted, not "ship-ready".
- **No grounded single-file fact-gate.** Cross-model reviewers share
  training bias and can rubber-stamp shared hallucinations; this lens
  cannot catch that. Content PRs with user-facing fact claims
  (dates/names/stats/security) still need an independent grounded
  fact-check first — that gate is **not** implemented in this repo.
- **Gemini output skews lighter** than Codex (≈10:1 grounding
  verification-call ratio observed); it still runs as a squad member but
  weight its findings accordingly.
- It does not commit, push, or open a PR — it only edits the working
  tree on the current branch. One change set per invocation.

## License

MIT. See [LICENSE](./LICENSE).
