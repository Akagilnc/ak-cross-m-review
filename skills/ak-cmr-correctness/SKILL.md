---
name: ak-cmr-correctness
description: Run the correctness cross-model review gate per-slice, or after ship-pre/design completeness passes.
allowed-tools:
  - Skill
---

# ak-cmr-correctness

This is a preset, not an independent engine.

Invoke `ak-cross-m-review` exactly once with `--lens correctness`. Pass the
user's base, scenario, authority inputs, and any required prior completeness
result through unchanged. Return the root skill's report unchanged, then stop.
