# ak-cross-m-review

Local, pre-PR review gate: two independent lenses run as parallel sub-agents
against a pinned diff and report one verdict each. `SKILL.md` plus the selected
lens prompt is the complete active authority; this file is vocabulary only.

## Language

**Fixed target**:
The pinned base-to-HEAD snapshot under review, resolved to two literal SHAs
before anything is dispatched.
_Avoid_: range, worktree diff, working changes

**Authority set**:
The ordered sources that govern the review — user decisions first, then
ratified ADRs / specs, then repository contracts.
_Avoid_: spec (alone), reference docs

**Lens**:
One review question with its own prompt file — `completeness` (was the
authority delivered?) or `correctness` (is what exists right?).
_Avoid_: axis, gate, mode, pass

**Leg**:
One independent sub-agent running exactly one lens inside a harness-provided
isolated copy of the target. A lens has exactly one leg per invocation.
_Avoid_: panel, member, reviewer squad, vendor leg

**Candidate**:
An evidence-backed claim a leg submits for judgment; never a verdict.
_Avoid_: finding (before judgment), vote

**Judge**:
The invoking session, which verifies each candidate against the fixed target
and authority set and disposes it as live or refuted.
_Avoid_: orchestrator, runner, merger

**Verdict**:
The single terminal line a lens ends with, labelled by lens
(`CMR-VERDICT: completeness=…` / `CMR-VERDICT: correctness=…`).
_Avoid_: gate result, concur, convergence

**Preset**:
A named wrapper skill that invokes the engine with one lens and returns its
report unchanged.
_Avoid_: gate skill, entry point

**Review only**:
The outcome boundary — the invocation reports and stops; the caller owns every
repair, commit, retry, and later review.
_Avoid_: read-only (that is a filesystem property, not this boundary)
