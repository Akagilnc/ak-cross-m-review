---
name: ak-cmr-completeness
description: Run the completeness cross-model review gate before ship-pre correctness, or for a design document.
allowed-tools:
  - Skill
---

# ak-cmr-completeness

This is a preset, not an independent engine.

Invoke `ak-cross-m-review` exactly once with `--lens completeness`. Pass the
user's base, scenario, and authority inputs through unchanged. Return the root
skill's report unchanged, then stop. The caller owns any later correctness call.
