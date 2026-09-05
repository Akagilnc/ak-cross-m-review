# ADR 0005: CMR is two parallel lens legs; transport belongs to the harness

## Status

Accepted (2026-09-05, owner decision). Supersedes ADR 0004 §3 (ordered `all`),
§4 (panel composition, family floor, transport adapters), §2's clone
sentences, §9, and §10's scratch-clone clause; ADR 0004's Status block lists
exactly which clauses remain in force (target pinning, authority freezing,
mutation hard-stop, judgment, lens prompts, presets, prompt resolution).

## Decision

CMR runs each lens as one independent sub-agent leg; `--lens all` dispatches
both legs in a single batch and each lens ends with its own labelled verdict,
emitted by the judge (`CMR-VERDICT: completeness=…`,
`CMR-VERDICT: correctness=…`); a leg submits candidates only. One leg's
failure reports as that lens's own `hard-stop`; it never withholds the other
lens's result. The skill does not select models or transports and does not
require cross-model composition: a sub-agent is a harness primitive, and which
model runs it — or how many times the caller invokes a lens under different
harnesses — is the caller's business, exactly as `code-review` treats its two
axes. Isolation is the harness's business too: each leg works in the
harness-provided independent copy of the target (Claude Code `Agent`
`isolation: worktree`, the Codex sandbox) under a review-only brief; the skill
neither builds nor audits clones. The judge stays: the invoking session
verifies each candidate against the fixed target and authority set, disposes it
`live` / `refuted` under the four lawful rejection reasons, and adjudicates a
defect separately from its remedy.

## Considered options

- **Keep the backend adapters as caller-side transports** (moved out of the
  skill or left in the repo as optional). Rejected: no harness consumes them
  today; keeping code for an imagined consumer is the ADR 0003 failure mode.
  Git history retains them if a harness ever needs a CLI leg.
- **Keep the skill's own full-clone isolation** (48 lines of `git clone
  --no-local` + self-checks). Rejected on the worth-it gate: the incidents it
  guarded against were CLI legs mutating the target worktree, which a
  harness-provided worktree already prevents; the residual shared-refs risk
  has no incident and is reflog-recoverable.
- **Drop the judge and report leg output verbatim** (the `code-review`
  shape). Rejected: the adjudication doctrine is the owner-calibrated value of
  this skill over a plain two-axis review; it is kept, minus every multi-leg
  clause (union, dedup, agreement, family floor).

## Consequences

- `backends/`, their behavior tests, the selftest, and the pytest scaffolding
  are deleted; the review engine has no executable surface and therefore no
  tests — `scripts/install-skills.sh` remains as an installation helper only
  (ADR 0003 §3–§4 no longer have a subject). `--mode` is removed — it
  only ever validated itself.
- The `CMR-VERDICT:` contract becomes one labelled line per lens; an `all`
  invocation prints two. No executable consumer depended on the single-line
  form.
- Cross-model coverage is no longer a property the skill can promise; a
  caller who wants it composes it (two harnesses, or a harness fan-out).
- Vocabulary collapses to lens / leg / judge / verdict (`CONTEXT.md`); panel,
  member, and pass are retired.
- Version 0.5.0.0 (constitution-level change, as ADR 0004 was for 0.4).
