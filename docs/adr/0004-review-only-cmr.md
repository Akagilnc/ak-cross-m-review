# ADR 0004: CMR is a one-pass review gate

## Status

Accepted (2026-07-15); amended 2026-07-16, owner decision.

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
   commit, retry, and later gate. Review-only is an outcome boundary, not
   filesystem read-only inside isolated reviewer clones.
2. The target is one user-supplied base-to-HEAD range from a clean committed
   repository. Record HEAD and status before dispatch and recheck both before
   the terminal verdict. Pin one resolved log command and one resolved diff
   command; each reviewer runs them itself. Each panel member receives an
   independent writable clone detached at the recorded HEAD; never expose the
   original target. The clone does not share the target's Git config, refs, or
   object store, and its source remote is removed before dispatch.
   Original-target mutation hard-stops with evidence. Only clean, unmoved,
   remote-free scratch may be discarded; preserve every dirty, moved, or
   remote-changed leg and unexpected target change without reset or cleanup.
   The authority set is frozen before dispatch. Completeness without enumerable
   authority hard-stops.
3. Per-slice uses correctness. Ship-pre and design-document work call
   completeness first and correctness later as separate outer invocations.
4. The default panel is Codex + Grok. The optional `claude` preset explicitly
   requests Opus 4.8 through an independent host Agent and never inherits the
   host default or Fable routing. If unavailable, the leg degrades and the
   caller may explicitly select another panel transport/model. Other optional
   legs are agy and OpenCode. agy makes one primary call and, only when its log
   confirms quota/429, may make one configured second-pool call; an empty
   fallback disables it. Auth and other failures do not retry. The successful
   model's actual family counts. OpenCode GLM is Z.AI; an OpenAI model through
   OpenCode is the same family as Codex. CMR does not replace degraded panel
   members. Every member sees the same small task packet and reads the range,
   authority, surrounding repository, and tests from its own clone; at least
   two actually successful, distinct actual model families are required.
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
9. CLI invocation contracts have executable behavior tests. A failed Codex leg
   preserves a bounded tail of native diagnostics before the generic degrade
   flag; a non-zero exit is not guessed to mean auth, quota, or crash. Markdown
   wording does not gain golden or phrase-pinning tests (ADR 0003).
10. Prompts and adapters resolve from the physical directory containing the
    loaded `SKILL.md`; every transport runs with cwd at its own writable scratch
    clone. Reviewers may install, test, and probe there, but may not repair,
    commit, push, or mutate remotes. Candidate locations are actual `path:line`
    anchors. Completeness gaps require both authority and consumer anchors.
11. The task packet contains only the endpoint SHAs, the two resolved Git
    commands, the selected lens, the ordered authority source list, and the
    candidate contract. It never embeds, segments, compresses, archives, or
    preloads the diff or repository files. Equal reviewer input means equal
    target/range, authority, lens, and candidate contract.

This decision expressly supersedes the active CMR behavior recorded in ADR
0001/0002 where it requires host-specific squads, disclosed document repair
rules, or `SKILL.md + DOC-MODE.md` as the authority union. Their historical
record remains intact. It also authorizes removal of superseded RECORDED rules
from the active skill; provenance remains in git history.

## Consequences

- `SKILL.md` plus the selected lens prompt is the complete active authority.
- Model-family diversity remains. Panel membership and review-pass retries are
  caller decisions; agy's declared quota-only second pool is the sole
  adapter-local fallback.
- A live defect can survive rejection of a bad proposed remedy.
- Evidence work may write freely in independent clones without granting
  reviewers the target or turning CMR into a repair engine.
- Reviewer context comes from the independent clone, not from serializing the
  repository into the model prompt.
- Review reports become inputs to an outer workflow instead of instructions to
  mutate the reviewed target.
