# gstack-grounded-review

Multi-reviewer, multi-round external review skill for catching hallucinations and
defects in code or design docs before they reach `APPROVED` / `main`.

**Status**: v0 prototype. Evolving.

## Why this exists

In-session subagent review and `gstack-review` / `gstack-codex` single-pass review
look good on paper but miss a distinct class of defect: **claims in a document
that contradict the actual source code, math that was never computed, CLI flags
that do not exist, APIs that were guessed from memory.**

Evidence from one session that triggered this work: a design doc passed two rounds
of spec-review at 8.0/10, reached `Status: APPROVED`, and was then caught by a
manual post-approval audit with **10 hallucinations across 5 severity levels**,
including a CRITICAL Beta quantile math error that would have made the L3 test
suite red on first implementation.

Spec-review skills cannot grep source, compute math, or shell out `<tool> --help`.
This skill can. It dispatches three independent reviewers in parallel:

- Claude Opus (via `claude -p --model opus`, headless new session — zero context contamination)
- Codex (via `codex exec -s read-only`)
- Gemini (via `gemini -p --approval-mode plan`)

Each reviewer runs the same task prompt against the same target, with full ability
to grep source, spawn `python3` for math verification, and call external CLI
`--help` for flag verification. Findings merge with deterministic severity upgrade
on consensus (2 reviewers agree → high, 3 agree → critical), and a fixer pass
proposes a unified diff to address critical/high findings. The user approves the
diff per round. Multi-round loops until findings converge or a round budget is
hit.

## Origin

This skill exists because of [Akagilnc/ai-blogger-lab#50][i50] and
[garrytan/gstack#973][i973] — the full session 5 / session 7 story is in those
issues. Short version: we tried to add a Grounded Review rule to `CLAUDE.md` as
prose. The rule failed adversarial review three times with structural (not
cosmetic) findings. The meta-conclusion was that prose rules cannot enforce
machine-verifiable artifacts, and the correct form of the rule is a scriptable
skill. This is that skill.

[i50]: https://github.com/Akagilnc/ai-blogger-lab/issues/50
[i973]: https://github.com/garrytan/gstack/issues/973

## Usage

```
/grounded-review <target> [--mode doc|code|auto] [--rounds N]
```

- `target`: path to a markdown doc or code file/directory
- `--mode`: `doc` for design/spec review, `code` for bug-hunting, `auto` detects
  from file extension (default: `auto`)
- `--rounds`: max iteration rounds (default: 3). Each round runs 3 reviewers,
  merges, proposes a fixer diff, asks the user to approve.

### Examples

```bash
# Review a design doc against real code
/grounded-review ~/.gstack/projects/foo/design-20260411.md --mode doc

# Code review a changed file with 2 rounds max
/grounded-review src/billing.ts --mode code --rounds 2
```

## Sibling skill: `/cross-model-review`

This repo also ships `cross-model-review/` — the executable form of the wiki's
`cross-model-review.md` (Step 2.4 / 2.6 of the autonomous TDD loop). It is
**diff-based correctness/invariant review** (not single-file fact-checking),
main-session-orchestrated, dispatching the v3 vendor squad
(**N codex gpt-5.5 + 1 Claude opus Agent + 1 Gemini = N+1+1**) in one parallel
message, with a deterministic drift/termination check (`lib/drift.py`) and the
defer protocol. It reuses `lib/merge.py` (consensus + grounding-density boost)
and `lib/extract_json.py`. Entry: `cross-model-review/SKILL.md`.

```
/cross-model-review [--base BRANCH] [--range A..B] [--scenario per-slice|ship-pre] [--rounds N]
```

## Evaluation

The `eval/` directory contains ground-truth test fixtures:

- **Doc mode**: `eval/session5_fixture.md` — session 5's design doc with the
  post-approval audit section stripped. Ground truth is `eval/ground_truth.json`
  listing the 10 known hallucinations (H1–H10) that the manual audit found.
  Target: recall ≥ 7/10.

- **Code mode**: `eval/code_fixture.ts` — synthetic 40-line TypeScript file with 5
  known bugs spanning logic, defensive programming, comparison, security, and
  silent error handling. Ground truth is `eval/code_ground_truth.json`.
  Target: recall ≥ 4/5.

Run: `eval/run_eval.sh` (doc mode), `eval/run_code_eval.sh` (code mode).

## Architecture

```
/grounded-review entry (via SKILL.md, invoked by Claude Code)
  │
  ├─ Step 0: check claude / codex / gemini / python3 / jq
  ├─ Step 1: detect mode (auto from extension, or explicit flag)
  ├─ Step 2 (per round):
  │   ├─ Dispatch 3 backends in parallel
  │   │   ├─ backends/claude-headless.sh  ──  claude -p --model opus
  │   │   ├─ backends/codex.sh             ──  codex exec -s read-only
  │   │   └─ backends/gemini.sh            ──  gemini -p --approval-mode plan
  │   ├─ Each backend gets prompts/reviewer-{doc|code}.md + target content
  │   ├─ Collect findings JSON from each → outputs/{run-id}/round-{N}/{backend}.json
  │   ├─ lib/merge.py → merged.json (severity upgrade on consensus)
  │   ├─ Present merged findings to user
  │   ├─ Fixer: claude -p with prompts/fixer.md → unified diff
  │   ├─ lib/apply_diff.py: git apply --check, test smoke, user approval
  │   └─ Termination check: all critical/high resolved? round budget? user stop?
  └─ Step 3: final report
```

## Dependencies

- [Claude Code](https://claude.com/claude-code) CLI (`claude`) for Claude Opus headless
- [OpenAI Codex](https://github.com/openai/codex) CLI (`codex`)
- [Google Gemini](https://github.com/google-gemini/gemini-cli) CLI (`gemini`)
- `python3` ≥ 3.11 (for `lib/merge.py`, `lib/strip_audit.py`, `lib/apply_diff.py`)
- `jq` (for shell pipelines)
- Optional: `scipy` installed via disposable venv for numerical verification

All three CLIs are subscription-authed in the author's setup; no API keys needed.

## Limitations (v0)

- **Single agent per model**. The "2 agents per model" idea (see
  [#973][i973]) is deferred to v1.
- **Code mode eval uses a synthetic fixture**. No real-project code-mode eval yet.
- **Fixer does not verify** that applied diffs actually remove the finding in the
  next round — only that `git apply` succeeds and any existing test suite still
  passes. True regression loop (round N finds same finding as round N−1 → fixer is
  broken, stop) is in the termination rules but not tested end-to-end.
- **Not integrated** with `/ship`, `/office-hours`, or `/plan-*`. Standalone skill
  only.
- **Gemini output quality is empirically lower** than Codex (10:1 grounding
  verification call ratio observed in session 7). v0 still runs Gemini as the
  third reviewer but findings may skew lighter.

## License

MIT. See [LICENSE](./LICENSE).
