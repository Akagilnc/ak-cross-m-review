# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is the gstack
4-digit `MAJOR.MINOR.PATCH.MICRO` scheme.

## [0.3.6.0] - 2026-06-13

Sync the accumulated wiki deltas, headlined by the **Fable pause**.

### Changed — Claude reviewer model (wiki `f0b4747`)
The Claude leg is no longer hardcoded to `fable`. Step 2's Claude-reviewer
bullet is now the **single authoritative place** for the model = "current
strongest available Claude": `fable` (Claude Fable 5) when up;
**2026-06-13 Fable is paused → `opus` (Opus 4.8) now, revert when it
returns**. The model MUST be set explicitly on the `Agent` call — it does
NOT inherit the session model (a dev-tier session would otherwise drag
the reviewer below the strongest-review-model rule). Step 1 / the
dispatch line / the frontmatter description / README / CLAUDE.md all stop
hardcoding "Claude Fable 5" and point at Step 2; the Step 3 Fable rows
(safeguards-autofallback, client < v2.1.170) are flagged **dormant while
Fable is paused** (Opus 4.8 is the baseline now, not a degradation).

### Added — previously-missing wiki rules (transcription gaps)
- **Design docs (ADR / spec / contract) get cmr too** (wiki §设计文档):
  a Step 0 pre-flight gate — design docs MUST run a full cmr in `doc`
  mode (design-completeness lens), and the agent proactively reminds the
  user when it produces one. TDD-green ≠ spec-correct.
- **Huge-diff (>10K lines) segmentation** hard rule (wiki §额外硬规则
  #3) added to the Step 2 invocation forms — avoid pipe-buffer saturation
  (separate from the N-table, which scales reviewer count).
- **Upgraded-state degraded termination sub-cases** (wiki §终止信号)
  added to Step 5: Claude/Gemini-missing → (N+1)/(N+1); all-codex-missing
  → 1+0+1 2/2; codex partial N→N′ → (N′+2)/(N′+2).
- **Main-session = Codex degradation table** (wiki §降级链) restored in
  Step 3 (was a one-line parenthetical) + the live-smoke auth rule.

### Note — reverse drift reconciled
The skill's hidden-path workspace warning is now in the wiki too (wiki
`51ad2b0`). The only remaining skill-ahead item is the client-<v2.1.170
degradation row (not in the wiki). An uncommitted `AGY_MODEL` `--model`
override was found in the repo working tree and **rejected, not adopted**:
routing the agy/Gemini leg to a Claude model collapses cross-family
diversity (2 Claude + 0 Gemini, anti-pattern #2/#4), its example used a
forbidden dev-tier reviewer (`claude sonnet-4.6`), and Fable-down is
correctly handled by the Claude leg → Opus 4.8, not by hijacking the
Gemini slot. Docs/manifest only — no code paths changed.

## [0.3.5.0] - 2026-06-12

Sync to wiki `5e565f1` — new rule **§每轮 review = 全量复审** (every
round is a full re-review, not a "did last round's P0/P1 close?"
spot-check). From round 2 on, a reviewer (and the session dispatching
it) drifts toward only verifying prior findings and stops reading the
current full diff; this repo has hit it repeatedly. SKILL.md Step 7 now
carries the rule: every round full-re-reviews the current diff (including
this round's fix) and prior-finding acceptance is only a tail-appended
item — with the three structural reasons it can't be narrowed (the fix
is new diff that must be reviewed; one round is non-exhaustive; narrowing
fakes a low finding count that breaks the Step 5/6 convergence read), the
body+tail prompt-construction shape, and the ❌ degraded spot-check form.
New anti-pattern #14. The Step 7 loop line is annotated `next round
(FULL re-review)`. Docs/manifest only — no code paths changed.

(The wiki's other recent change, `def164a` — the agy `--sandbox --print
''` invocation form + `--log-file` quota note — was already in the skill
from v0.3.4.0; the two converged on the same form. Reverse-drift still
owed the OTHER way: the skill's hidden-path workspace warning is not yet
in the wiki.)

## [0.3.4.0] - 2026-06-11

Fix the agy (Gemini leg) invocation + surface the real degrade reason —
found by running `/diagnose` on "agy went empty for 8 straight cmr
rounds." Root cause was **quota** (agy hit `RESOURCE_EXHAUSTED` / 429,
"Individual quota reached", resets in ~64h), but the diagnosis surfaced
two real defects in `backends/gemini.sh` besides the quota itself:

### Fixed

- **agy invocation form** (`agy -p --sandbox` → `agy --sandbox --print
  ''`). agy 1.0.7 changed `--print`/`-p` into a string flag that takes
  its value from the next token, so `-p --sandbox` silently swallowed
  `--sandbox` as the prompt value — **`--sandbox` never engaged** (the
  real prompt still reached agy only via agy's stdin-concatenation,
  `prompt = <--print value> + "\n" + stdin`). The new form puts
  `--sandbox` before an explicit empty `--print ''`, so sandbox is a
  real flag (verified by agy's "enabling terminal sandbox for this
  session" log line) and the diff still rides on stdin (no ARG_MAX
  limit). Regression test pins the exact argv (`--sandbox` standalone +
  `--print` value empty), so a revert to the `-p`-eats-`--sandbox` form
  fails CI.

### Added

- **Quota / 429 visibility.** agy routes fatal backend errors
  (RESOURCE_EXHAUSTED / 429 / quota) to its `--log-file`, NOT
  stdout/stderr — so a quota-exhausted run looks like a plain empty
  success (rc=0, empty stdout) and the round degraded with a bare
  "empty output" and no reason (this is why 8 rounds looked mysterious).
  `gemini.sh` now passes `--log-file` and, on any degrade, greps that
  log (only — see the R1 note below) for the fatal-error signatures, so
  the flag names the cause: `本轮缺 gemini (empty output, agy rc=0;
  quota/429 — agy
  individual quota exhausted; Resets in 63h…)`. Verified live against
  real agy. Regression test stubs an agy that writes the 429 to its
  log-file and exits 0 empty.
- **Hidden-path workspace warning.** agy refuses to add a workspace
  folder whose path has a hidden (dot) component ("is hidden: ignore
  uri" in its log), so running cmr from e.g. a `.claude/worktrees/...`
  worktree gives the Gemini reviewer NO repo context (diff-only, no
  source grep). `gemini.sh` now warns (does not degrade — agy still
  reviews the diff) so the quality gap is visible; rerun from a
  non-hidden path for full context. Both branches of the new conditional
  are covered (hidden → warns, visible → silent).

### Hardened in pre-PR cross-model review (R1)

The change ran its own skill (`/ak-cross-m-review`, 1+2+1; gemini leg
degraded on the same quota 429 — and the new flag named it live).
Fixes from that round:

- **`agy_fatal_reason` false quota attribution (high).** The reason scan
  read agy's log AND `$RAW`; on the extract-fail path `$RAW` is the full
  model output (which quotes the reviewed diff), and a bare `quota`
  pattern made any diff mentioning quota/429 code falsely report "quota
  exhausted" — which would wrongly drive the degrade-chain (skip retry /
  wait ~64h). Now scans ONLY agy's `--log-file`, patterns pinned to
  agy's fatal-line shapes, and greps the file directly (no
  `printf | grep -q` that could SIGPIPE under `pipefail` on a large
  blob). Negative regression test added (Claude C1 + codex#2 R1,
  live-reproduced by both).
- **argv regression test strengthened** — it now rejects the short `-p`
  and asserts no `--print`/`-p` has `--sandbox` as its value, so the
  exact `-p`-eats-`--sandbox` regression cannot slip through (codex#1
  R2).
- **Stale `agy 1.0.0` pins removed** from SKILL.md / README.md /
  CLAUDE.md / the test docstring (only historical CHANGELOG entries keep
  the version) — they contradicted the 1.0.7 behavior the fix documents
  (Claude C2 + codex#1/#2).
- **Visible-path test guarded** against a base-temp-dir-under-a-hidden-
  component env edge (Claude C3).

### Hardened in online PR review (R1)

Online bots on the PR (codex clean-approved; gemini-code-assist +
sourcery raised three points, all in `agy_fatal_reason` / the retry
loop):

- **Optional greps made non-fatal + crash-proof.** `resets=` and
  `execerr=` now use `grep -m1 … || true` instead of `… | head -1`,
  so a no-match (grep exit 1) cannot abort under `set -euo pipefail`
  and there is no pipefail/SIGPIPE interaction. (Empirically the old
  form already degraded cleanly — locked by the R2 characterization
  tests — but `|| true` makes it explicit and cross-bash-robust rather
  than relying on subtle errexit semantics. gemini-code-assist high +
  medium.)
- **Per-attempt log truncation.** `AGY_LOG` is truncated (`: > …`)
  before each retry attempt, so a fatal error recorded on an earlier
  attempt cannot leak into the degrade reason for a later attempt that
  failed for a different cause (sourcery). Regression test added.
- **Executor-error reason no longer truncated at the first colon** —
  the grep matches `agent executor error: .*` (to end of line) instead
  of `[^:]*`, so a multi-colon message is kept whole (sourcery).
  Regression test added.

### Notes

- Could not verify live that the corrected invocation produces real
  findings: the same quota 429 that triggered the investigation blocks
  any agy output for ~64h. Invocation correctness (sandbox engaged,
  prompt delivered) and both observability features ARE verified live;
  the model-output step is quota-blocked, not logic-blocked.
- **Wiki re-sync owed (reverse drift):** the source-of-truth wiki
  (`cross-model-review.md`) still documents `agy -p --sandbox` / "agy
  1.0.0". This skill had to track the installed agy 1.0.7 to keep
  working; the wiki needs the same invocation correction or the next
  re-sync will drift it back.

## [0.3.3.0] - 2026-06-10

Claude reviewer leg: **Opus → Claude Fable 5** (wiki `904c988`+`a64d064`).
Anthropic shipped `claude-fable-5` (Mythos-class) 2026-06-09 as a tier
above Opus 4.8 on capability + reasoning, so per the "strongest review
model" rule the Claude leg switches to it. The Agent dispatch goes from
`model: opus` (which only tracked the Opus family → Opus 4.8, never
Fable) to `model: fable`. Step 3 gains a degradation row: Fable's
safeguards auto-route <5% of sessions (security / bio / chem /
distillation) to Opus 4.8 — that is NOT a leg failure (squad stays
1+1+1), but the round flags `Claude leg = Opus 4.8 (Fable safeguards
trigger)` so finding-consistency comparisons stay honest. Docs/manifest
only — no code paths changed.

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
