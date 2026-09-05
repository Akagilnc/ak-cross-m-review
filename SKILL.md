---
name: ak-cross-m-review
description: Use when the user explicitly requests CMR or cross-model review of a fixed target through one or two parallel completeness and correctness lens legs, or when a CMR preset delegates to this shared engine.
allowed-tools:
  - Agent
  - Bash
  - Read
  - Grep
  - Glob
---

# /ak-cross-m-review — fixed-target review engine

This file plus each selected prompt is the complete active authority. See
`CONTEXT.md` for vocabulary.

**REVIEW ONLY.** Pin one fixed target and authority set, run the selected lens
legs, judge their candidates independently, report, and stop. The caller owns
every repair, commit, retry, and later review.

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

1. Require `git status --porcelain=v1 --untracked-files=all -- :/
   ':(top,exclude).claude/worktrees/**'` to return no output, excluding only the harness worktrees.
2. Resolve `PRE_HEAD` with `git rev-parse --verify 'HEAD^{commit}'` and
   `BASE_SHA` with `git rev-parse --verify '<base>^{commit}'`; retain the
   literal full SHAs.
3. Substitute those SHAs and freeze these commands exactly:

   ```text
   git log --oneline BASE_SHA..PRE_HEAD
   git diff --binary BASE_SHA...PRE_HEAD
   ```

4. Run the frozen log command and require the frozen diff command to produce a
   non-empty diff.

A dirty tree, unresolved ref, failed command, or empty diff is a `hard-stop`.
Record the exact failing command and its native output in one sentence.

Completion criterion: clean status, two literal commit SHAs, and one non-empty
diff represented by the two frozen commands.

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

`--lens completeness|correctness|all` is required; omission is a `hard-stop`.
Only failures common to every selected lens in Steps 1–3 — a Step 1 pin failure
or `--lens` omission — end the invocation with the single unlabelled line
`CMR-VERDICT: hard-stop`. A lens-specific Step 2 failure ends that lens with its
labelled `CMR-VERDICT: completeness=hard-stop`; any other selected lens still dispatches.

Resolve the selected prompt path from the directory containing this loaded
`SKILL.md`:

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

Launch one sub-agent leg for each selected lens, in parallel when both are
selected. The harness or caller must provide each leg an independent working copy
of the target (Claude Code: `Agent` `isolation: worktree`). A leg never works in
the target's own working tree; if no independent copy is available, that lens is
a `hard-stop`. The skill selects no model or transport, creates no copy, and audits no copy.

Give each leg a brief containing only:

- this reviewer role boundary;
- literal `BASE_SHA` and `PRE_HEAD`;
- the two frozen commands from Step 1;
- the absolute lens prompt path resolved in Step 3;
- the ordered authority list; and
- the candidate contract from Step 5.

Reviewer role boundary:

> Review exactly one lens in the assigned harness-provided isolated copy.
> Pin first: verify `git rev-parse HEAD` equals literal `PRE_HEAD` and literal
> `BASE_SHA` resolves; when HEAD differs, detach only this isolated copy at
> `PRE_HEAD`, then verify again. If either pin cannot be established, return
> this lens as a `hard-stop` with exact command evidence.
> Run the frozen commands, inspect the named authority and repository, perform
> useful tests or probes, and submit only evidence-backed candidates under the
> candidate contract. Work review only: preserve the fixed target and leave
> repair, commit, push, dispatch, judgment, and verdict to their owners. Do not
> invoke or simulate another agent; instead complete this lens directly. Do
> not emit `CMR-VERDICT:`; instead submit candidates for the judge.

Never paste the diff or file bodies into a brief; the leg runs the pinned
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

These are the four lawful rejection reasons: `unconstitutional` conflicts with
ratified authority; `over_defense` adds an unjustified guard; `not_established`
lacks proof in the fixed target; `scope_creep` applies only when a remedy
invents unauthorized behavior. A pre-existing or adjacent defect remains
eligible. Difficulty is never a rejection reason. Deletion or simplification
outranks an equivalent added mechanism.

After every selected leg has a judgment or evidenced failure, seal once:

1. require `git rev-parse 'HEAD^{commit}'` to equal `PRE_HEAD`;
2. require `git status --porcelain=v1 --untracked-files=all -- :/
   ':(top,exclude).claude/worktrees/**'` to be empty, excluding only the harness worktrees.

Any change is a `hard-stop`; show before/after HEAD and status evidence. Never
reset, checkout, remove, or clean the target.

End each selected lens with exactly one labelled line:

```text
CMR-VERDICT: completeness=complete|gaps|hard-stop|escalate
CMR-VERDICT: correctness=converged|findings|hard-stop|escalate
```

Completeness is `complete` when no live gap or unresolved `unverifiable` row remains; otherwise it is `gaps`.
Correctness is `converged` when no live defect remains; otherwise it is `findings`.
`escalate` means a genuine owner decision is required to dispose a candidate.
`hard-stop` means a prerequisite, seal, or leg failure as defined above.

Completion criterion: after the single successful seal, every selected lens
has an independent judgment or evidenced failure and exactly one labelled
verdict. Stop unconditionally.
