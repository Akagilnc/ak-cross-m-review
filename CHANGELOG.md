# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is the gstack
4-digit `MAJOR.MINOR.PATCH.MICRO` scheme.

## [0.2.0.0] - 2026-05-18

`/ak-cross-m-review` becomes the sole skill (the original
`/grounded-review` is removed) and is rebuilt as a **faithful, compact
transcription of the wiki's `cross-model-review.md`** instead of a
deterministic review engine.

### Why

Three rounds of cross-model review of this branch kept surfacing new
bugs, every one in the self-invented orchestration/merge/drift
machinery — never in the procedure the wiki actually prescribes. The
wiki explicitly frames merge / grade / drift / termination as agent
*judgment* (numeric thresholds are proto-calibrated, non-portable). The
skill had over-formalized that judgment into brittle code; that code
was the entire bug reservoir. Fix = match the wiki, not re-engineer it.

### Changed

- **`SKILL.md` rewritten** as a tight executable transcription of the
  wiki step (setup / parallel-launch / invocation forms / degradation /
  merge+grade / termination / drift triple / loop), 461 → 238 lines.
  Merge / grade / drift / termination are now performed as the agent
  judgment the wiki describes — no deterministic engine.
- **`/ak-cross-m-review` is the registered skill at the repo root**
  (flattened out of the `ak-cross-m-review/ak-cross-m-review/`
  double-nesting; `backends/codex-review.sh` self-locates one level up).
- `backends/codex-review.sh` hardened: degrades when the codex process
  exits non-zero even if its error body was salvageable (an auth/quota
  failure no longer counts as a valid zero-finding reviewer).

### Removed

- **The deterministic review engine** — `lib/merge.py`, `lib/drift.py`,
  `lib/apply_diff.py` and their tests. This machinery contradicted the
  wiki ("this is judgment; thresholds are non-portable") and was the
  source of the recurring orchestration bugs.
- **The `/grounded-review` skill** — old root `SKILL.md`,
  `backends/claude-headless.sh`,
  `prompts/{fixer,reviewer-doc,reviewer-code}.md`, `lib/strip_audit.py`.
- **`backends/codex.sh`** — legacy uncorrected codex backend (the
  `-C` + positional-prompt footguns), superseded, no caller.
- **`eval/`** — the grounded-review fixture suite (follow-up debt).

### Kept / tested

- `SKILL.md`, `backends/codex-review.sh`, `backends/gemini.sh`,
  `lib/extract_json.py`, `prompts/cmr-{reviewer,fixer}.md`.
- pytest scoped to `lib/extract_json.py` + a `codex-review.sh` degrade
  subprocess regression test; `bash backends/codex-review.sh --selftest`
  is the invocation-form regression guard. CI runs both on push / PR
  with least-privilege `permissions`.

### Notes

- Capability gap: grounded single-file fact-checking (catching
  shared-hallucination content errors) has no implementation here.
  Cross-model review cannot cover that lens — see README
  "Limitations / boundary".
- Architecture follow-up: the skill is still LLM-orchestrated prose by
  design (the wiki step is judgment, not a program). Faithfulness to
  the wiki is enforced by review, not tests — keep it re-synced when
  `cross-model-review.md` changes.

## [0.1.0.0] - 2026-05-17

First versioned release. Adds a second skill alongside `/grounded-review`.

### Added

- **`/ak-cross-m-review` skill** — run a pre-PR cross-model review on a
  diff without re-deciding the regime each time. It dispatches the v3
  vendor squad (N codex `gpt-5.5` + 1 Claude opus Agent + 1 Gemini =
  **N+1+1**, codex instances scaled by diff size) in a single parallel
  message, merges with consensus + grounding-density severity, runs a
  computed drift/termination check, proposes a fixer diff per round with
  the defer protocol, and stops on N/N concur or an architectural drift.
  Entry: `ak-cross-m-review/SKILL.md`; prompts in
  `ak-cross-m-review/prompts/`.
- **`ak-cross-m-review/backends/codex-review.sh`** — the corrected codex
  invocation (`codex exec --model gpt-5.5 -` over a stdin pipe, no `-C`,
  always `2>&1`), with a portable hard timeout and a `--selftest`
  regression guard so the known codex footguns cannot come back.
- **`lib/drift.py`** — deterministic drift detector (quantity / class /
  target drift, plus the coverage-drift override and a degraded-round
  guard) with a 13-scenario `--selftest`. Reused by the review loop so
  "should we stop?" is computed, not felt.
- README section documenting the new sibling skill.

### Changed

- `ak-cross-m-review/SKILL.md` aligned to the 2026-05-17 wiki capability
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
