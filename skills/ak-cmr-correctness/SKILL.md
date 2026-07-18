---
name: ak-cmr-correctness
description: Use when the user explicitly requests cross-model correctness review to find real bugs or counterexamples in a fixed diff.
allowed-tools:
  - Skill
---

# ak-cmr-correctness

This is a preset, not an independent engine.

Invoke `ak-cross-m-review` exactly once with `--lens correctness`. Pass the
user's base, mode, and authority inputs through unchanged. Return the root
skill's report unchanged, then stop.
