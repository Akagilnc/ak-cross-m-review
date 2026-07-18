---
name: ak-cmr-completeness
description: Use when the user explicitly requests cross-model completeness review of whether a fixed diff delivers every stated requirement, spec clause, or design decision.
allowed-tools:
  - Skill
---

# ak-cmr-completeness

This is a preset, not an independent engine.

Invoke `ak-cross-m-review` exactly once with `--lens completeness`. Pass the
user's base, mode, and authority inputs through unchanged. Return the root
skill's report unchanged, then stop. The caller owns any later correctness call.
