---
name: ak-cmr-completeness
description: Use when the user requests cross-model completeness review of a fixed base-to-HEAD diff on the caller's harness.
allowed-tools:
  - Skill
---

# ak-cmr-completeness

This is a preset, not an independent engine.

Invoke `ak-cross-m-review` exactly once with `--lens completeness`. Pass the
user's base and authority inputs through unchanged. Return the root skill's
report unchanged, then stop. The caller owns any later correctness call.
