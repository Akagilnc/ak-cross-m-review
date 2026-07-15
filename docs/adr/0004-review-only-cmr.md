# ADR 0004: CMR is a one-pass review gate

## Status

Accepted (2026-07-15), owner decision.

## Context

CMR had accumulated dispatch variants, reviewer-count formulas, voting,
termination policy, document-specific repair policy, and an embedded repair
procedure. Review generated work, repaired that work, and then reviewed its own
repairs. The skill became a second development engine instead of a review gate.

The useful core is smaller: freeze what is being reviewed and which authority
governs it; ask independent model families one focused question; let a judge
verify candidate findings; report once.

## Decision

1. CMR is review-only. One invocation performs one fixed-target, one-lens,
   one-panel pass and stops after judgment. The caller owns every repair,
   commit, retry, and later gate.
2. The target is one user-supplied base-to-HEAD diff materialized once. The
   authority set is frozen before dispatch. Completeness without enumerable
   authority hard-stops.
3. Per-slice uses correctness. Ship-pre and design-document work call
   completeness first and correctness later as separate outer invocations.
4. The default panel is Codex + Grok. Claude is optional, not required. Legacy
   agy remains selectable and its backend remains available to external
   consumers. Every member sees the same full packet; at least two actually
   successful, distinct transport families are required.
5. Panel outputs are candidate findings, never votes. The judge verifies their
   union, separates defect adjudication from remedy adjudication, and may reject
   only as `unconstitutional`, `over_defense`, `not_established`, or
   `scope_creep`, with evidence.
6. Correctness uses Trace–Break–Prove. Completeness uses
   Clause–Wire–Exercise. Reviewer prompts do not emit terminal verdicts or
   require a remedy.
7. The completeness and correctness wrapper skills remain named presets. They
   select one lens and return the root engine result; neither owns procedure or
   invokes the other.
8. `DOC-MODE.md` and `prompts/cmr-fixer.md` are removed. Their historical
   rationale remains in git and the changelog, not in the active skill.
9. CLI invocation contracts have executable behavior tests. Markdown wording
   does not gain golden or phrase-pinning tests (ADR 0003).

This decision expressly supersedes the active CMR behavior recorded in ADR
0001/0002 where it requires host-specific squads, disclosed document repair
rules, or `SKILL.md + DOC-MODE.md` as the authority union. Their historical
record remains intact. It also authorizes removal of superseded RECORDED rules
from the active skill; provenance remains in git history.

## Consequences

- `SKILL.md` plus the selected lens prompt is the complete active authority.
- Model-family diversity remains, but panel size, quota choice, and retry are
  explicit caller decisions rather than hidden substitutions.
- A live defect can survive rejection of a bad proposed remedy.
- Review reports become inputs to an outer workflow instead of instructions to
  mutate the reviewed target.
