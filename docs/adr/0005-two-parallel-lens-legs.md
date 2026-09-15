# ADR 0005: CMR is two parallel lens legs; transport belongs to the harness

## Status

Accepted (2026-09-05, owner decision). Supersedes ADR 0004 §3 (ordered `all`),
§4 (panel composition, family floor, transport adapters), §2's clone
sentences, §9, and §10's scratch-clone clause; ADR 0004's Status block lists
exactly which clauses remain in force (target pinning, authority freezing,
mutation hard-stop, judgment, lens prompts, presets, prompt resolution).
Amended 2026-09-15 (owner decision): a single-lens invocation runs in the invoking session; see the Decision.

## Decision

CMR runs a single selected lens in the invoking session, which applies the lens prompt, restores the target it probed, and then judges; `all` runs each lens as one independent sub-agent leg, both dispatched in a single batch, and each lens ends with its own labelled verdict,
emitted by the judge (`CMR-VERDICT: completeness=…`,
`CMR-VERDICT: correctness=…`); a leg submits candidates only. One leg's
failure reports as that lens's own `hard-stop`; it never withholds the other
lens's result. The skill does not select models or transports and does not
require cross-model composition: a sub-agent is a harness primitive, and which
model runs it — or how many times the caller invokes a lens under different
harnesses — is the caller's business, exactly as `code-review` treats its two
axes. Isolation is not the skill's business either: each leg works in an
independent copy OF THE TARGET at `PRE_HEAD` under a review-only brief. The
harness provides that copy when it can (Claude Code `Agent`
`isolation: worktree` — only when the session's repository is the target);
when it cannot (an external target, or the Codex sandbox, which shares the
working tree), the caller creates one worktree per leg from `TARGET_ROOT`
(amended 2026-09-05 after both cases were observed). The skill
neither builds nor audits copies it did not create; the one-line precondition
a leg runs on its own copy (its top level is not `TARGET_ROOT`) is the leg's
pin, not a skill audit. The judge stays: the invoking session
verifies each candidate against the fixed target and authority set, disposes it
`live` / `refuted` under the four lawful rejection reasons, and adjudicates a
defect separately from its remedy.

Amended 2026-09-15 (owner decision). A sub-agent with a separate copy exists for two reasons: to keep two lenses from sharing context, and to keep probes off the reviewed target. A single-lens invocation has nothing to keep apart, so it runs in the invoking session with no sub-agent and no separate copy; the session removes its own probe residue before sealing, and residue is re-cleaned, not hard-stopped, because the tree was clean at the pin and anything new is the session's own. The only remaining seal hard-stop for an in-session lens is a moved HEAD. `all` is unchanged. A harness without sub-agents therefore runs each lens as a separate invocation.

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
