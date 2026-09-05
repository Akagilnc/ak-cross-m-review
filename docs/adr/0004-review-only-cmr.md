# ADR 0004: CMR is a review-only fixed-target gate

## Status

Accepted (2026-07-15); amended 2026-07-16, owner decision. Amended again
2026-09-05 by ADR 0005, which supersedes: §3 (ordered `all`); §4 (panel
composition, family floor, transport adapters); §2's clone sentences — the
text from "Each panel member receives an independent writable clone" through
"rejects a destination inside the original target", and the text from "Only
clean, unmoved, remote-free scratch" through "without reset or cleanup"
(isolation is the harness's; the skill neither builds nor audits copies) —
while the sentence between those two ranges, "Original-target mutation
hard-stops with evidence", stays in force; §9 (no executable surface remains,
so no behavior tests); §10's scratch-clone clause; §1's "explicit ordered
`all` gate" / "fresh panel passes" sentences; and §11's six-item packet
enumeration (the v0.5 brief, listed in `SKILL.md` Step 4, also carries
`TARGET_ROOT` and the lens prompt's text). Still in force: §1's review-only
boundary; §2's target-pinning, authority-freezing, and "original-target
mutation hard-stops with evidence" clauses; §5's adjudication doctrine (its
"Panel outputs … verifies their union" wording is superseded — one leg per
lens, no union); §6; §7; §8; §10's first sentence (prompts resolve from the
directory containing the loaded `SKILL.md`, now the Step 4 brief item "read
from `prompts/` beside this loaded `SKILL.md`"); §11's "never embeds …
the diff or repository files" clause (the target's, not the lens prompt).
The Consequences section below is the 2026-07 record: only its first, third,
and sixth bullets still describe v0.5; the others (model-family diversity,
adapters, independent clones, ordered `all`) are historical.

## Context

CMR had accumulated dispatch variants, reviewer-count formulas, voting,
termination policy, document-specific repair policy, and an embedded repair
procedure. Review generated work, repaired that work, and then reviewed its own
repairs. The skill became a second development engine instead of a review gate.

The useful core is smaller: freeze what is being reviewed and which authority
governs it; ask each fresh panel one focused question; let a judge verify
candidate findings; report once.

## Decision

1. CMR is review-only. One invocation fixes one target and authority set, then
   performs either one selected lens or the explicit ordered `all` gate. `all`
   uses fresh panel passes for completeness and correctness; it never combines
   their prompts or reviewer contexts. The caller owns every repair, commit,
   retry, and later gate. Review-only is an outcome boundary, not filesystem
   read-only inside isolated reviewer clones.
2. The target is one user-supplied base-to-HEAD range from a clean committed
   repository. Record HEAD and status before dispatch and recheck both before
   the terminal verdict. Pin one resolved log command and one resolved diff
   command; each reviewer runs them itself. Each panel member receives an
   independent writable clone detached at the recorded HEAD. The clone does not
   share the target's Git config, refs, or object store. Its source remote is
   removed before dispatch, and clone preparation rejects a destination inside
   the original target.
   Original-target mutation hard-stops with evidence. Only clean, unmoved,
   remote-free scratch may be discarded; preserve every dirty, moved, or
   remote-changed leg and unexpected target change without reset or cleanup.
   The authority set is frozen before dispatch. Completeness without enumerable
   authority hard-stops.
3. The two named lenses are independent calls; neither requires a report from
   the other. CMR does not decide when a caller should invoke a lens or use HEAD
   movement across invocations as a workflow gate. Explicit `all` is only an
   invocation-local ordered convenience: it runs completeness first and starts
   a fresh correctness pass after `complete`, reusing the pinned endpoints and
   authority set but no reviewer context or scratch clone. Lens omission remains
   an error; it does not default to `all`.
4. The default panel is Codex + Grok. The optional `claude` token uses the
   explicit `backends/claude-review.sh` CLI adapter, configurable through
   `CMR_CLAUDE_MODEL` and defaulting to `claude-opus-4-8`; it leaves CLI
   reasoning effort unset. Its headless call uses `--permission-mode
   acceptEdits --allowedTools Bash` so it can write scratch and run Git, tests,
   and probes in its independent clone. It does not use `bypassPermissions`.
   It makes no automatic fallback; CLI failure, empty output, or malformed
   reviewer output degrades the leg. Other optional legs are agy and OpenCode. agy
   makes one primary call and, only when its log
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
   `scope_creep`, with evidence. `scope_creep` means the proposed fix invents
   behavior not authorized by authority/spec; pre-existing, adjacent-file, or
   incidentally discovered defects do not qualify.
6. Correctness uses Trace–Break–Prove. Completeness uses
   Clause–Wire–Exercise. Reviewer prompts do not emit terminal verdicts or
   require a remedy.
7. The completeness and correctness wrapper skills remain named presets. They
   select one lens and return the root engine result; neither owns procedure or
   invokes the other.
8. `DOC-MODE.md` and `prompts/cmr-fixer.md` are removed. Their historical
   rationale remains in git and the changelog, not in the active skill.
9. CLI invocation contracts have executable behavior tests. A failed Codex leg
   preserves a bounded, strict-valid UTF-8 tail of native diagnostics before
   the generic degrade flag; invalid byte fragments such as a partial character
   at the cut boundary are discarded. A non-zero exit is not guessed to mean
   auth, quota, or crash. Markdown wording does not gain golden or phrase-pinning
   tests (ADR 0003).
10. Prompts and adapters resolve from the physical directory containing the
    loaded `SKILL.md`; every transport runs with cwd at its own writable scratch
    clone. Reviewers may install, test, and probe there, but may not repair,
    commit, push, or mutate remotes. Candidate locations are actual `path:line`
    anchors. Completeness gaps require both authority and consumer anchors.
11. Each panel pass's task packet contains only the fixed reviewer role
    boundary, endpoint SHAs, the two resolved Git commands, that pass's
    selected lens, the ordered authority source list, and the candidate
    contract. It never embeds, segments,
    compresses, archives, or preloads the diff or repository files. Equal
    reviewer input means equal target/range, authority, lens, and candidate
    contract.
This decision expressly supersedes the active CMR behavior recorded in ADR
0001/0002 where it requires host-specific squads, disclosed document repair
rules, or `SKILL.md + DOC-MODE.md` as the authority union. Their historical
record remains intact. It also authorizes removal of superseded RECORDED rules
from the active skill; provenance remains in git history.

## Consequences

- `SKILL.md` plus each selected lens prompt is the complete active authority.
- Model-family diversity remains. Panel membership and review-pass retries are
  caller decisions; agy's declared quota-only second pool is the sole
  adapter-local fallback.
- A live defect can survive rejection of a bad proposed remedy.
- Evidence work may write freely in independent clones without granting
  reviewers the target or turning CMR into a repair engine. Claude's adapter
  grants the headless process the matching edit and Bash permissions without
  bypassing Claude Code's permission system.
- Reviewer context comes from the independent clone, not from serializing the
  repository into the model prompt.
- Review reports become inputs to an outer workflow instead of instructions to
  mutate the reviewed target.
- The generic engine can run an explicit ordered `--lens all` invocation without
  turning either named single-lens entry point into a prerequisite for the other.
