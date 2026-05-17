# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is the gstack
4-digit `MAJOR.MINOR.PATCH.MICRO` scheme.

## [0.1.0.0] - 2026-05-17

First versioned release. Adds a second skill alongside `/grounded-review`.

### Added

- **`/cross-model-review` skill** — run a pre-PR cross-model review on a
  diff without re-deciding the regime each time. It dispatches the v3
  vendor squad (N codex `gpt-5.5` + 1 Claude opus Agent + 1 Gemini =
  **N+1+1**, codex instances scaled by diff size) in a single parallel
  message, merges with consensus + grounding-density severity, runs a
  computed drift/termination check, proposes a fixer diff per round with
  the defer protocol, and stops on N/N concur or an architectural drift.
  Entry: `cross-model-review/SKILL.md`; prompts in
  `cross-model-review/prompts/`.
- **`cross-model-review/backends/codex-review.sh`** — the corrected codex
  invocation (`codex exec --model gpt-5.5 -` over a stdin pipe, no `-C`,
  always `2>&1`), with a portable hard timeout and a `--selftest`
  regression guard so the known codex footguns cannot come back.
- **`lib/drift.py`** — deterministic drift detector (quantity / class /
  target drift, plus the coverage-drift override and a degraded-round
  guard) with a 13-scenario `--selftest`. Reused by the review loop so
  "should we stop?" is computed, not felt.
- README section documenting the new sibling skill.

### Changed

- `cross-model-review/SKILL.md` aligned to the 2026-05-17 wiki capability
  correction: cross-model review is always main-session-orchestrated
  (subagents cannot spawn the Claude reviewer), unified `N+1+1` notation,
  and `merge.py`'s grounding boost documented as the wiki's
  "grounding density = trust weight" principle.

### Fixed

The skill was hardened by running its own three-round adversarial review
loop (Claude subagent + Codex) on itself before shipping:

- Codex reviewer silently received an empty prompt on any machine with
  GNU `timeout` (the homebrew-macOS default), so it never actually ran.
  The prompt now reaches codex via a single stdin path on every branch.
- `drift.py` severity is normalized, so `"High"`/`"HIGH"` no longer
  undercount and false-trigger an architectural stop.
- Coverage-drift detection no longer collapses when reviewers share one
  context location; round ordering is numeric and bash-3.2 portable.
- A degraded round (reviewers never ran) can no longer read as a clean
  "converged"; a broken input pipeline is surfaced, not treated as a
  benign tick.
- Timeout handling no longer kills sibling parallel codex runs, escalates
  to SIGKILL when TERM is ignored, and a real CLI error (auth/quota)
  degrades cleanly without discarding valid reviews that merely discuss
  rate-limit/quota/429 code.
