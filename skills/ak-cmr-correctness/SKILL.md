---
name: ak-cmr-correctness
description: Use when the user requests cross-model correctness review of a fixed base-to-HEAD diff on the caller's harness.
allowed-tools:
  - Skill
---

# ak-cmr-correctness

This is a preset, not an independent engine.

Invoke `ak-cross-m-review` exactly once with `--lens correctness`. Pass the
user's base and authority inputs through unchanged. Return the root skill's
report unchanged, then stop.
