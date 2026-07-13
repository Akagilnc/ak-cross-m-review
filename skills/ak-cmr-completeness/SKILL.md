---
name: ak-cmr-completeness
description: Completeness gate for cross-model review. Use before the correctness gate on a finished change (ship-pre), and when reviewing a design document (ADR/spec).
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

# ak-cmr-completeness — the completeness gate (one named entry point)

This is a thin wrapper. It runs **exactly one** thing: the **completeness
lens** of cross-model review.

**Do:** invoke the `ak-cross-m-review` skill with **`--lens completeness`**
(via the `Skill` tool), passing through whatever scope args you have
(`--base` / `--range` / `--diff`; `--scenario ship-pre` for a finished
change). That dispatches the squad against `prompts/cmr-completeness.md` —
*was every spec clause delivered, and are the load-bearing mechanisms
actually wired (not hollow)?* — and loops to `CMR-VERDICT: complete`.

That is all this skill does. It exists so the completeness gate is a
**named, explicit invocation** — the agent picks *this* skill when it
means completeness, instead of trusting a parameter it might forget,
mis-set, or merge into the correctness pass.

For the full procedure (squad, dispatch, merge, drift, termination, the
fix loop) see `ak-cross-m-review` — this wrapper changes nothing but the
lens. The correctness gate is its sibling skill `ak-cmr-correctness`; on a
finished change (ship-pre) run **this one first** (it must pass), then
`ak-cmr-correctness`. Never both in one prompt («严禁合一次 cmr 闸»).
