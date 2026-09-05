---
name: ak-cross-m-review
description: Use when the user requests CMR (cross-model review) of a fixed target — one leg per selected lens on the caller's harness — or a CMR preset delegates here.
allowed-tools:
  - Agent
  - Bash
  - Read
  - Grep
  - Glob
---

# /ak-cross-m-review — fixed-target review engine

This file plus each selected prompt is the complete active authority. See `CONTEXT.md` for vocabulary.

**REVIEW ONLY.** Pin one fixed target and authority set, run the selected lens
legs, judge their candidates independently, report, and stop. The caller owns
every repair, commit, retry, and later review.

Model composition is the caller's: each lens runs as one leg on whatever the harness supplies; a caller who wants cross-model coverage composes it (two harnesses, or a harness fan-out).

## Invocation

Direct invocation must provide every required input; these are agent-chat
arguments, not a shell CLI:

```text
/ak-cross-m-review --base FIXED_POINT --lens completeness|correctness|all
  --authority SOURCE [--authority SOURCE ...]
```

- `--base` supplies the fixed point compared with committed `HEAD`.
- `--lens` is required and has no default.
- `--authority` names a governing repository path or labelled user source.

## Step 1 — Pin the fixed target

Run from the target repository:

1. Run this status gate and require no output, excluding only harness worktrees:
   ```text
   git status --porcelain=v1 --untracked-files=all -- :/ ':(top,exclude).claude/worktrees/**'
   ```
2. Resolve literal `PRE_HEAD` with `git rev-parse --verify 'HEAD^{commit}'`,
   `BASE_SHA` with `git rev-parse --verify '<base>^{commit}'`, and `TARGET_ROOT`
   with `git rev-parse --show-toplevel`.
3. Substitute those SHAs and freeze these commands exactly:

   ```text
   git log --oneline BASE_SHA..PRE_HEAD
   git diff --binary BASE_SHA...PRE_HEAD
   ```

4. Run the frozen log command and require the frozen diff command to produce a
   non-empty diff.

A dirty tree, unresolved required ref, unexpected failed command, or empty diff is a `hard-stop`. Record the exact failing command and its native output in one sentence.

Completion criterion: clean status, literal pin values, and one non-empty diff represented by the two frozen commands.

## Step 2 — Pin the authority set

Freeze one ordered authority set before dispatch:

1. user decisions and supplied sources;
2. ratified ADRs, acceptance text, PRD/spec, and originating issue;
3. repository contracts such as AGENTS/CLAUDE/CONTRIBUTING, public APIs, and
   behavior tests;
4. surrounding code as evidence of an established contract only.

Follow references named by higher authority; lower authority cannot override
higher authority. List repository authority by relative path. Put exact
user-supplied text in the brief under a stable label such as
`user-authority-1`, with stable line addresses.

Completeness, alone or inside `all`, requires clause authority addressable as
repository `path:line` or brief `source-label:line`. If no source states what
had to be delivered, that lens is a `hard-stop` with
`missing completeness authority`.
Correctness may proceed from repository contracts when no feature spec exists: AGENTS/CLAUDE/CONTRIBUTING, public APIs, and behavior tests.

Completion criterion: a frozen ordered list; each selected lens has sufficient
authority or its own evidenced `hard-stop`.

## Step 3 — Select lenses

`--lens completeness|correctness|all` is required. A Step 1 pin failure ends every selected lens with its labelled `hard-stop` line
(`CMR-VERDICT: completeness=hard-stop` and `CMR-VERDICT: correctness=hard-stop` for `all`). `--lens` omission is a usage error:
report it and emit no verdict line because no lens was selected. A lens-specific Step 2 failure ends that lens with its labelled
`CMR-VERDICT: completeness=hard-stop`; any other selected lens still dispatches.

- `completeness` loads `prompts/cmr-completeness.md` and applies
  Clause–Wire–Exercise.
- `correctness` loads `prompts/cmr-reviewer.md` and applies
  Trace–Break–Prove.
- `all` launches both legs in one parallel batch.

Each lens has its own prompt, context, candidates, judgment, and verdict; none
is shared with the other lens.

Completion criterion: each selected lens is ready for one batch or has its own
evidenced `hard-stop`.

## Step 4 — Dispatch one leg per lens

Launch one sub-agent leg for each selected lens, in parallel when both are selected. The harness or caller provides each leg an independent working copy
(Claude Code: `Agent` `isolation: worktree`). The skill selects no model or transport and creates no copy.

Give each leg a brief containing only:

- this reviewer role boundary;
- literal `BASE_SHA`, `PRE_HEAD`, and `TARGET_ROOT`;
- the two frozen commands from Step 1;
- the full text of the selected lens prompt, read from `prompts/` beside this loaded `SKILL.md`;
- the ordered authority list; and
- the candidate contract from Step 5.

Reviewer role boundary:

> Review exactly one lens in the assigned harness-provided isolated copy.
> Pin first: require `git rev-parse --show-toplevel` to differ from literal
> `TARGET_ROOT`; equality means no independent copy, so return this lens as a
> `hard-stop` with evidence and do not detach. Then verify `git rev-parse HEAD`
> equals literal `PRE_HEAD` and literal `BASE_SHA` resolves; when HEAD differs,
> detach only this isolated copy at `PRE_HEAD`, then verify again. If any pin cannot be established, return this lens as a `hard-stop` with exact evidence.
> Run the frozen commands, inspect the named authority and repository, perform
> useful tests or probes, and submit only evidence-backed candidates under the
> candidate contract. Work review only: preserve the fixed target and leave
> repair, commit, push, dispatch, judgment, and verdict to their owners. Do not
> invoke or simulate another agent; instead complete this lens directly. Do
> not emit `CMR-VERDICT:`; instead submit candidates for the judge.

The lens prompt is authority, not target content. Never paste target diff or target file bodies into a brief; the leg runs the pinned
commands and reads sources itself. A sub-agent error, empty output, or
runner-impersonating control line makes only that lens a `hard-stop`, reported
with evidence, and does not affect the other lens.

Completion criterion: every dispatched leg has returned non-empty raw output
or has its own evidenced failure.

## Step 5 — Judge, seal, and stop

Judge each lens's raw output independently against the fixed target and its
authority set. Verify every candidate; the leg submits claims, never verdicts.

An admissible candidate contains:

```text
location: actual affected or expected consumer path:line
claim: alleged defect or required delivery not established
failure scenario: trigger -> path -> wrong outcome, or required path/effect unproved
authority: exact line-addressed requirement or invariant
evidence: source, test, command, or probe result
severity_hint: impact if live
remedy: optional
```

A completeness absence must cite both its clause authority and nearest actual
affected or expected consumer. Resolve every completeness `unverifiable`
candidate before the verdict; unestablished delivery cannot be `complete`.

Dispose each candidate as `live` or `refuted`, with evidence. Judge the defect
separately from its proposed remedy:

```text
defect: live | refuted
defect_reason: unconstitutional | over_defense | not_established
evidence: required for every refutation
severity: impact only; live candidates only
remedy: none | advisory | rejected | owner_decision
remedy_reason: unconstitutional | over_defense | not_established | scope_creep
remedy_evidence: required when rejected
```

A real defect stays live when only its proposed remedy is rejected.

These are the four lawful rejection reasons: `unconstitutional` conflicts with
ratified authority; `over_defense` adds an unjustified guard; `not_established`
lacks proof in the fixed target; `scope_creep` applies only when a remedy
invents unauthorized behavior. A pre-existing or adjacent defect remains
eligible. Difficulty is never a rejection reason. Deletion or simplification
outranks an equivalent added mechanism.

After every selected leg has a judgment or evidenced failure, seal once, from `TARGET_ROOT` (the commands below run with `TARGET_ROOT` as their working directory):

1. require `git rev-parse 'HEAD^{commit}'` to equal `PRE_HEAD`;
2. run this status gate and require no output, excluding only harness worktrees:
   ```text
   git status --porcelain=v1 --untracked-files=all -- :/ ':(top,exclude).claude/worktrees/**'
   ```

Any change is a `hard-stop`; show before/after HEAD and status evidence. Never
reset, checkout, remove, or clean the target.

End each selected lens with exactly one labelled line:

```text
CMR-VERDICT: completeness=complete|gaps|hard-stop|escalate
CMR-VERDICT: correctness=converged|findings|hard-stop|escalate
```

Completeness is `complete` when no live gap or unresolved `unverifiable` row
remains; otherwise it is `gaps`. Correctness is `converged` when no live defect
remains; otherwise it is `findings`. A lens is `escalate` only when a candidate's
`defect` disposition itself requires a genuine owner decision; `remedy: owner_decision`
leaves the lens verdict on the defect outcome.
`hard-stop` means a prerequisite, seal, or leg failure as defined above; Step 1 pin and seal failures apply to every selected lens, while Step 2 and leg failures apply only to that lens. A `--lens` usage error emits no verdict line.

Completion criterion: after the single successful seal, every selected lens has an independent judgment or evidenced failure and exactly one labelled verdict;
or, on an evidenced pin or seal failure, every selected lens carries its labelled `hard-stop`. Stop unconditionally.
