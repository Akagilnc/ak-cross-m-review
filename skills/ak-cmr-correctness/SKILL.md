---
name: ak-cmr-correctness
description: Run the CORRECTNESS gate of cross-model review (tdd-autonomous-dev per-slice / ship-pre Step 6) — find real defects in the change: wrong logic, broken invariants, spec-vs-implementation contradictions, missing guards, security, P0–P4. This is the defect lens (is what's there correct?), distinct from the completeness lens (was everything required delivered?). Use it per-slice after a baseline commit, or as the SECOND ship-pre gate after completeness passes. A thin named entry point so the lens is explicit and never conflated with completeness.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
  - TodoWrite
  - Skill
---

# ak-cmr-correctness — the correctness gate (one named entry point)

This is a thin wrapper. It runs **exactly one** thing: the **correctness
lens** of cross-model review.

**Do:** invoke the `ak-cross-m-review` skill with **`--lens correctness`**
(via the `Skill` tool), passing through whatever scope args you have
(`--base` / `--range` / `--diff` / `--scenario per-slice|ship-pre`). That
dispatches the squad against `prompts/cmr-reviewer.md` — *is what's there
correct?* — grading P0–P4 and looping to `CMR-VERDICT: converged`.

That is all this skill does. It exists so the correctness gate is a
**named, explicit invocation** — the agent picks *this* skill when it
means correctness, instead of trusting a parameter it might forget or
mis-set. (`--lens correctness` is also the engine default, so this is the
plain "review my change for bugs" entry point.)

For the full procedure (squad, dispatch, merge, drift, termination, the
fix loop) see `ak-cross-m-review` — this wrapper changes nothing but the
lens. The completeness gate is its sibling skill `ak-cmr-completeness`; on a
finished change (ship-pre) run `ak-cmr-completeness` **first**, then this one.
Never both in one prompt («严禁合一次 cmr 闸»).
