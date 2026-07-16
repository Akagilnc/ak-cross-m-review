---
name: ak-cmr-correctness
description: Run an independent correctness cross-model review of a fixed base-to-HEAD diff.
allowed-tools:
  - Skill
---

# ak-cmr-correctness

This is a preset, not an independent engine.

Invoke `ak-cross-m-review` exactly once with `--lens correctness`. Pass the
user's base, mode, and authority inputs through unchanged. Return the root
skill's report unchanged, then stop.
