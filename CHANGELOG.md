# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is the gstack
4-digit `MAJOR.MINOR.PATCH.MICRO` scheme.

## [0.3.2.0] - 2026-06-10

Harden the fix-loop discipline (sync wiki `91a4e1f` + raise the bar).
The fix step now **defaults to non-trivial**: the first fix-loop action
must be an explicit, up-front classification (before any read/edit) —
no classification means non-trivial, which means invoke the `/diagnose`
skill first. The **mechanical** exception is a closed high-bar allowlist
(typo / dead anchor / stale label / date / whitespace) that must ALSO
touch zero executing code, be single-site, and be provably inert;
"simple / one line / obvious / confident" are explicitly rejected as
justifications. `Skill` added to `allowed-tools` so the `/diagnose`
invocation the rule requires is actually grantable. `prompts/cmr-fixer.md`
aligned (mechanical-only scope reconciled with the MUST-fix rules:
non-trivial critical/high route to main-session `/diagnose`, not a
down-rank). New anti-pattern: over-claiming "mechanical" to skip
`/diagnose`. Docs/manifest only — no code paths changed.

## [0.3.1.0] - 2026-06-08

Sync to wiki §额外硬规则 #6 (`3b05d34`): concurrent `codex exec` must
pass **`--ephemeral`**. Without it, parallel codex instances collide on
`~/.codex/session` and cross-contaminate (a prompt from one instance
surfaces in another's context) — a latent silent-corruption footgun on
cmr's default 1+N+1 parallel path (N≥2). `backends/codex-review.sh` now
passes `--ephemeral` on all call sites; `--selftest` asserts its
presence (reverse-tested). `SKILL.md` Step 2 marks it mandatory. See
`openai/codex#11435`. Online review (gemini-code-assist + sourcery,
2-bot concur) flagged the invocation string was duplicated across 5
sites — extracted a single-source `CODEX_CMD` array; every call site and
the `--selftest` validation now derive from it, so the selftest checks
the live command instead of a hand-copied mirror.

## [0.3.0.0] - 2026-05-19

Sync to the wiki's 2026-05-18+ revision: **two-phase 顺机理 dispatch**
becomes the rule (replacing the old "all reviewers in one message"
form), and the Gemini reviewer leg switches from the EOL'd `gemini`
CLI to **`agy` 1.0.0** (Antigravity, locked to Gemini 3.5 Flash) with
the wiki's keychain warm + retry × 4 recipe around its auth-race.

### Changed

- **`SKILL.md` Step 2 rewritten** to the **two-phase dispatch contract**:
  - msg1 = ONE assistant message containing every Bash CLI reviewer
    tool call, ALL with `run_in_background: true` (N codex + 1 agy).
  - msg2 = the very next message; first content MUST be the Claude
    `Agent` call (foreground).
  - **no-peek invariant** between msg1 and msg2 (no CLI output read,
    no other tool call) — this is the one piece of discipline prose
    still has to enforce. Peek = silent serialization = drift.
  Both wiki goals (concurrency + independence) preserved by
  construction; the old "all in one message" rule fought the Agent /
  Bash tool asymmetry and kept silently serializing in practice.
- **`backends/gemini.sh` switched to `agy -p --sandbox`** (Antigravity
  CLI 1.0.0, the in-kind replacement after `gemini` CLI's 2026-06-18
  EOL). Implements the wiki's auth-race recipe: each attempt pre-warms
  the `Antigravity Safe Storage` keychain item (no-op on non-macOS via
  `|| true`), then runs `agy`; if the output matches
  `Authentication required|authentication timed out`, retry up to 4
  attempts total; after 4 failures flag `本轮缺 gemini (auth race
  after retry×3)` and degrade. `AGY_PRINT_TIMEOUT` (default 15m;
  agy's 5m default is too short for large diffs) and
  `GEMINI_RETRY_WARM_SLEEP` (default 0; tests-only) are honored.
  Never `--dangerously-skip-permissions` (anti-pattern #11).
- Anti-pattern #6 generalized to **two-phase dispatch violations**
  (peeking between msg1 and msg2 / msg2 first content not the Agent /
  the old single-message Agent+Bash mix). #11 added: dead `gemini -p`
  + forbidden `agy --dangerously-skip-permissions`.
- README / CLAUDE.md / TESTING.md synced (`agy` mentions, two-phase
  framing, dependency list).

### Added

- **`tests/test_gemini.py`** updated to stub `agy` (was `gemini`). Now
  pins three behaviors:
  1. agy non-zero exit + JSON-ish salvageable body → still degrade
     (the G_RC half of the gate);
  2. persistent auth-race signature → script retries up to 4 attempts
     then degrades with `auth race after retry×3` (verified by warn
     line count, not by sleep timing);
  3. `agy` missing on PATH → degrade up-front with the post-EOL
     explanation, never silent / never crash.

### Notes

- Gemini 3.5 Flash is weaker than the codex `gpt-5.5` review tier;
  documented in SKILL.md as an explicit exception to the strongest-
  review-model rule, accepted to keep 3-vendor cross-family coverage.
- The upstream agy keychain auth-race is tracked at
  `google-antigravity/antigravity-cli#51`. Workaround (warm + retry)
  is non-root cause but empirically effective; cleanly reflagged on
  exhaustion.

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
