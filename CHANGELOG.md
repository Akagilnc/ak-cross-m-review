# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is the gstack
4-digit `MAJOR.MINOR.PATCH.MICRO` scheme.

## 0.3.20.1 — 2026-07-13

- **S6-fixes review round-1 (1 medium + 2 low, both legs exercised the
  repro paths live under the new reviewer contract).** The F8 watchdog
  validation ran before the `--selftest` early-exit, so a polluted env
  (e.g. `CMR_CODEX_TIMEOUT=15m`) aborted the invocation-form regression
  guard itself with a fake degrade payload — the checks now mirror the
  MODE guard and skip for `--selftest` (new invariant pinned:
  polluted-env selftest exits 0). SKILL.md's mechanical bar gains the
  one-line pointer to the fixer's verbatim-propagation exception (the
  two layers had diverged). The dry-run stderr now carries `本轮缺
  codex (NON-REVIEW DRY_RUN)` so it matches Step-4's degrade
  recognition vocabulary.

## 0.3.20.0 — 2026-07-13

- **S6 audit findings: 13 fixed in one pass, 1 owner-rejected (issue
  #29's 14 findings, owner-adjudicated same day — no defer loop).**
  Headline: **the strict REVIEW-ONLY divergence is WITHDRAWN** (owner:
  reviewers were never banned from running commands; no-modify/no-fix
  stays prompt-level, no hard gates) — gemini.sh's injected preamble now
  permits read-only inspection/verification commands incl. exercises
  with injected defects in a throwaway copy; both lens prompts aligned;
  SKILL.md's REVIEW-ONLY RECORDED marker removed (2 markers remain:
  Fable, agy warm+retry); the skill re-aligns with the wiki's 2026-07-06
  exercise carve-out. Constitution/kill-axis now explicitly applies in
  ALL modes in the completeness prompt (code mode skips only ②–⑤/
  anti-minutes; addendum golden hash recomputed). Both prompts' dead
  "②–⑤ … below/untouched" anchors now point at DOC-MODE.md. Fixer:
  mode-conditional self-check (code=二连, doc=三连 per DOC-MODE.md ⑤);
  mechanical-vs-sweep contradiction closed with the verbatim-identical-
  propagation narrow exception. Backends hardened (all red-first):
  CMR_DRY_RUN can no longer pose as a successful zero-finding leg
  (loud + nonzero); watchdog env vars validated (invalid → visible
  degrade); MODE validated doc|code in both backends (JSON-injection
  shape closed); gemini auth-race grep no longer SIGPIPEs on >buffer
  output (here-string; 1.6MB repro test); non-Google AGY_MODEL overrides
  (e.g. GPT-OSS) now correctly flag NO Google voice (family check
  inverted to Gemini/Google-only no-flag). **Won't-fix per owner: no
  read-only mounts / mutation detection / fail-closed machinery**
  (「改了就改了。改对了就收,改错了就修」). Test functions 140 → 150
  (151 collected with parametrization; counts verified via
  `grep -rc '^def test_'` + `pytest --collect-only` at batch HEAD).

## 0.3.19.13 — 2026-07-13

- **Ship-pre correctness round-1 fixes (1 high + 1 medium + 1 low).**
  The cross-slice lens caught what three per-slice rounds structurally
  could not: S2's mainline cleanup dropped the `main=Claude` qualifier
  from Step 5's by-design parenthetical, leaving mainline claiming ALL
  Step-6 correctness is 1+1+1 while the host table's 固定双腿 row says
  main=Codex Step 6 = codex+agy (grok high; qualifier restored
  verbatim, matching pre-S2 main). The 固定双腿 cell now binds to the
  by-design scoring (`(N+1)/(N+1) concur + flag`). New red-first
  coherence pin: `main=Claude correctness (Step 6)` asserted in the
  Step-5 slice (grok medium — the missing semantic pin was why the
  seam survived per-slice review). ADR authority-map: four `无` pointer
  cells corrected to name the real pointer locations (Opus low).
  Orchestrator adjudication recorded: grok's Only-1-vendor join-marker
  suggestion rejected — the host table's 只在下列点替换 preamble IS the
  join; mainline stays host-clean per S2's red line. The coherence pin
  is an assertion inside the existing host-inset test; suite stays at
  140.

## 0.3.19.12 — 2026-07-13

- **Ship-pre completeness round-1 fixes (PR #33).** Both legs (Opus +
  grok-4.5; agy quota-dead) returned `gaps` — the delivered mechanisms
  all fired under injected defects, but two 缺钉 and three unposted
  process artifacts blocked: (a) `UPSTREAM-CHECKLIST.md` — the sole
  surviving copy of the deleted agy-ladder archaeology — had zero test
  coverage; now pinned by
  `test_upstream_checklist_keeps_agy_archaeology_until_sync`
  (key sentences, no golden hash — the file is designed to be consumed
  and deleted by the next sync PR); (b) the Step-2 four-element
  structure labels (入口/硬禁令/降级旗 ×3 legs) were content-pinned but
  not structure-pinned; now asserted. Process artifacts posted:
  S2 pre-refactor inset inventory → issue #27 comment; S3
  deleted-narrative guardian ledger + wiki-collation evidence → issue
  #30 comment; S1 test-split 分流清单 → PR #33 comment. 138 → 140
  tests, all green.

## 0.3.19.11 — 2026-07-13

- **S5 round-1 review fixes (1 medium + 3 low + 2 P4).** CLAUDE.md's
  intro no longer contradicts its own §Wiki sync mapping — the entry
  sentence now reads "SKILL.md … with DOC-MODE.md, together a faithful
  transcription of the wiki" (a top-of-file-only reader previously got
  the pre-split sync surface; grok medium). ADR mapping-table
  corrections: the Fable row's pointer column no longer names a
  non-existent host-table row (→ 无); row 1's "absence guard" pointer
  reworded to its negative-space meaning. Freeze-boundary sentence
  scoped to the split itself (the completeness-addendum hash is
  pre-existing, not split-produced). Thin tests deepened one notch
  (still no golden hash): ADR red-line phrase + CONTEXT load-bearing
  pointer sentence pinned red-first. "15-term" → 16-term.

## 0.3.19.10 — 2026-07-13

- **S5 (#31, PRD #25): paper sedimentation — ADR 0001 + CONTEXT.md +
  CLAUDE.md sync map.** `docs/adr/0001-progressive-disclosure.md`
  records the split's red lines as they actually landed (host
  differences stay in-file as the substitution table; ① kill-axis stays
  mainline; archaeology upstreams via UPSTREAM-CHECKLIST.md, no
  BACKENDS.md middle layer; descriptions = identity + triggers; SKILL.md
  header zero additions), the two-freeze-boundary atomic-migration rule,
  the 规则→唯一权威位置 mapping table (9 rules — the baseline for the
  future dedup round), and the wiki-side layout-note TODO. `CONTEXT.md`
  defines the 16-term domain vocabulary, each term pointing at its
  authority. Repo `CLAUDE.md` gains the sync map: 转写 = SKILL.md +
  DOC-MODE.md 的并集, linked to the ADR. Thin red-first
  existence/key-sentence assertions (no golden hash on these files).
  Orchestrator pre-commit check caught two Step-number mis-pointers in
  CONTEXT.md (clear round / qualifying-confirmation cited Step 6; the
  positive-termination authority is Step 5, loop mechanics Step 7) —
  corrected before this commit.

## 0.3.19.9 — 2026-07-13

- **S4 round-1 review fixes (2 medium + 2 low).** The absence guard now
  bans the tokens actually dieted out — `gpt-5.6`, `codex`, `agy`, plus
  the ASCII `P0-P4` variant (round 1's list only named Claude/Gemini,
  under-delivering the advertised "model names" class); the correctness
  trigger test locks the gate-order phrase "after completeness passes"
  (symmetry with completeness's "before the correctness gate"); the
  completeness description regains the ship-pre spine keyword (22/28
  words) with its own trigger assert. Full enforced tuple (superset of
  the highlights below): `N+1+1`, `N+1`, `two-phase`, `no-peek`,
  `Claude`, `Gemini`, `gpt-5.6`, `codex`, `agy`, `DONE/PARTIAL`,
  `NOT-DONE`, `CONFORMS/VIOLATES`, `UNVERIFIED-GAP`, `P0–P4`, `P0-P4`.

## 0.3.19.8 — 2026-07-13

- **S4 (#28, PRD #25): frontmatter description diet — identity +
  triggers only.** The three descriptions (main skill + two gate
  wrappers) shed every mechanism/rubric detail that now has an
  authoritative home in the body or prompts: 124→30, 98→22, 79→23
  words (total 301→75, −75% of always-resident context). Trigger
  semantics preserved (per-slice after a baseline commit / ship-pre
  before a PR / design docs / gate ordering). Main gate:
  red-first **absence assertions** in test_skill_frontmatter.py —
  the length caps (36/28/30 words) are only the auxiliary net, since a
  short-but-mechanism-laden description would pass a cap. Wrapper
  bodies untouched. 132 → 135 tests, all green.

## 0.3.19.7 — 2026-07-13

- **S3 round-1 review fixes (1 high + 1 medium + 2 low + 1 P4).** The
  compression had dropped the **step-down / no-Google-voice operator
  rule** from the runtime surface (it survived only in
  UPSTREAM-CHECKLIST.md staging and gemini.sh's stderr note) — restored
  as a contract clause in the Gemini bullet: an agy ladder step-down is
  a successful leg but the round's third read is agy-served Claude
  (same Anthropic family), never counted as Google-family diversity,
  flagged in the round report (grok F1, high). The
  "keeps_all_invocation_hard_bans" test was missing two bans — `agy -p
  --sandbox` and the >10K one-segment rule — both now pinned (grok F2,
  medium). Shared all-legs discipline line restored (always `2>&1`;
  hang = idle >15min, not wall-clock; scoped pid-tree kill only) (grok
  F3). 0.3.19.6's wording corrected: three legs share 入口/硬禁令/降级旗,
  RECORDED markers only where a standing divergence exists (grok F4).
  Gemini 降级旗 lead no longer claims every flag path exhausts the
  ladder (auth-race / not-installed short-circuit) (Opus P4). Squad:
  Opus converged; grok-4.5 high caught F1/F2 — the substitute leg again
  out-hunting the primary.

## 0.3.19.6 — 2026-07-13

- **S3 (#30, PRD #25): Step-2 invocation forms compressed to contract
  level + wiki upstreaming checklist.** All three invocation bullets now
  share 唯一入口 backend / 硬禁令 / 降级旗语义: codex (via
  codex-review.sh; never `"$(...)"`, `-C`, global pkill…), gemini (via
  gemini.sh; never `-p --sandbox`, `--dangerously-skip-permissions`…),
  Claude (via Agent tool, model=opus; never headless `claude -p`).
  One-line ⚠ RECORDED markers appear only on legs with a standing divergence.
  Three sync-recognizable RECORDED markers, correctly classified: Fable
  禁用 = 存续; **agy warm+retry = 新建** (vs wiki "1.0.8 无需
  warm+retry"); **strict REVIEW-ONLY = 新建** (vs wiki's 2026-07-06
  exercise carve-out) — behavior guards ≠ sync markers, so the two new
  ones now exist as markers, closing the sync-erasure vacuum. Unguarded
  behavior narratives (agy `--sandbox` not write-hard) moved to a
  `### 待补守护（暂不得删）` section, not deleted (backends/ frozen this
  round). Archaeology narratives deleted only after wiki collation;
  the one un-collated piece (agy model-degradation ladder → Sonnet rung)
  is preserved verbatim in `UPSTREAM-CHECKLIST.md` for the next sync PR.
  The reasoning-effort contract callout (TESTING.md's single source of
  truth) survives intact. SKILL.md 842 → 758 lines (net −84). 128 → 131
  tests (three new red-first contract assertions), all green; selftest
  green; doc-mode residual hash unchanged.

## 0.3.19.5 — 2026-07-13

- **S2 round-2 nits + convergence.** Pin the last unpinned table flag
  string `不用 Claude (credit)` (tests/test_codex_host_substitution.py);
  note the 5th test (127 → 128) in the 0.3.19.4 entry. S2 converged at
  round 3 (rounds 2+3 both clear; Opus + grok-4.5 high). This heading
  backfills the missing 0.3.19.5 entry (grok round-3 low — the
  one-heading-per-micro convention, same class as PR #32 round-8 F5).

## 0.3.19.4 — 2026-07-13

- **S2 per-slice review round-1 fixes (2 medium + 2 low + 1 clarity).**
  The consolidation had dropped two load-bearing nuances that existed
  nowhere else in the tree (both restored into the Claude-leg table
  row): the **file/env auth-check ban** (keychain/GUI false negatives —
  live-smoke is the only accepted probe) and the **concrete review
  invocation** (`cat "$PROMPT_FILE" | claude -p --model claude-opus-4-8
  --output-format json --disable-slash-commands`), preserving the
  smoke-has-`--tools ""` / review-does-not asymmetry. The codex-leg row
  regains its (wiki hypothesis，未在本 skill 实测) hedge — the native-
  subagent path was never field-verified. Test suite hardened: Row 6's
  unique tokens, the three degrade flag strings, the codex-solo flag,
  and the two restored phrases are all pinned (9 new assertions); a
  5th test was added to the suite, taking the total from 127 → 128.
  Squad note: Opus cleared the dropped invocation as non-load-bearing;
  the grok-4.5 leg flagged both drops as medium — orchestrator
  adjudicated with grok after source verification (HEAD~1 had them,
  tree had zero occurrences, no other home in repo).

## 0.3.19.3 — 2026-07-13

- **S2 (#27, PRD #25): main=Codex host substitution table.** All
  main=Codex point-differences, previously scattered as parenthetical
  insets across Step 2/3/5, consolidate into one `## main=Codex
  宿主替换表` section (placed before Step 2 — a Codex-host agent reads
  it once on entry, then walks the same main=Claude mainline): codex leg
  → native subagent (ship-pre top level only; per-slice stays `codex
  exec`), Claude leg → live-smoke probe then `claude -p` (pin
  `--model claude-opus-4-8`, no `--effort max`, reviewer without
  `--tools ""`), the three Codex-host degrade rows, the fixed-2-vendor
  scenarios, and the codex-solo positive-termination exception —
  verbatim carrying its "不适用于 Step 5 completeness" exclusion.
  Mainline Step 2/3/5 now read clean as main=Claude; old inset signature
  phrases asserted absent. The Fable RECORDED RULE block stays mainline
  (host-independent, not a substitution point). New red-first suite
  `tests/test_codex_host_substitution.py` (4 tests: table existence,
  codex-solo scope + exclusion, degrade rows, inset absence). SKILL.md
  876 → 842 lines (net −34: 能删大于能加); doc-mode residual hash
  unchanged (`f0c27d0e…`). 123 → 127 tests, all green; selftest green.

## 0.3.19.2 — 2026-07-13

- **Owner directive: 「能删大于能加」 reviewer principle added to both
  lens prompts (`prompts/cmr-reviewer.md` L14, `prompts/cmr-completeness.md`
  L18).** Deletion outranks addition: for the same functionality, code
  count going down vastly outranks going up; reviewers flag additions a
  deletion could have achieved. Counterweight to the review loop's
  structural additive bias (completeness lens is add-only by
  construction; the nail-token incident cost 8 rounds of patching an
  unimplementable mechanism). Duplicated in both prompts intentionally
  (standing repo policy, no DRY extraction); placed outside
  cmr-completeness.md's golden-hashed addendum (hash unchanged). New
  red-first pin `test_both_lenses_prioritize_deletion_over_addition`
  (tests/test_prompts.py). 122 → 123 tests.

## 0.3.19.1 — 2026-07-13

- **S1 per-slice review finding (grok-4.5 leg, low) — README inventory
  registers `DOC-MODE.md` (README.md L128).** The "What ships in this
  repo" tree still presented the engine as a single file after S1
  externalized doc-mode ②–⑤; an operator reading only README would miss
  the sibling that Step 0 requires reading before doc-mode dispatch.
  Review squad note: agy quota-dead again → per owner order the third
  voice ran as xai grok-4.5 (`grok` CLI, reasoning-effort xhigh, non-fast)
  — its first outing; both legs (Opus + grok) returned converged on S1.

## 0.3.19.0 — 2026-07-13

- **S1 (#26, PRD #25): doc-mode ②–⑤ split out of SKILL.md into
  `DOC-MODE.md` (progressive disclosure, atomic golden-hash migration).**
  SKILL.md 970 → 876 lines; DOC-MODE.md = 105 lines (②–⑤ verbatim + the
  shared "Why doc mode needs its own defense (#440)" rationale + its own
  ⚠ RECORDED ②–⑤ banner + new golden hash
  `5bfd8483…`). SKILL.md keeps ① (constitution packet + kill-axis, ALL
  modes) with its own independent ⚠ RECORDED ① marker (do-not-drop
  semantics preserved), a one-line residual pointer to DOC-MODE.md, and a
  recomputed residual-section hash `f0c27d0e…`. Step 0's doc-mode bullet
  now carries the hard read-before-dispatch pointer (review 对象是
  ADR/spec/plan → 先 Read DOC-MODE.md 再派单); the completeness-lens
  bullet's discipline enumeration and Step 5's ②(c) reference (L599)
  rewritten to cross-file form — no stale in-file pointers to migrated
  content remain. All internal references inside the migrated text
  (anti-pattern #14, Step 3, Step 6, Step 7 ×2) rewritten to `SKILL.md
  …` cross-file form. Tests: `test_doc_mode.py` assertions split
  per-object (① + Step-0 pointer stay on SKILL.md; ②–⑤ + hash follow to
  DOC-MODE.md; golden freeze now three boundaries), `test_convergence.py`
  ②(c) assertions redirected to DOC-MODE.md, two new red-first guards
  (`test_doc_mode_sections_have_one_owner_each` bidirectional
  anti-dual-source; `test_shared_doc_mode_rationale_survives_once_in_external_file`
  keyed on "58% fix-fix"). completeness-addendum hash untouched
  (`48bd9e6d…`). 120 → 122 tests, all green; selftest green (zero script
  changes). Implemented by codex worker (gpt-5.6-sol); baseline
  reconciliation addenda from issue #26's 2026-07-13 comment applied.

## 0.3.18.27 — 2026-07-13

- **Ship-pre correctness-gate round 9 (qualifying clear round) — two P4
  clarity fixes (`prompts/cmr-fixer.md`).** Round 9 was the gate's first
  clear round (codex + Claude both `converged`; gemini degraded, 本轮缺):
  no blocking finding, two `clarity` observations from the Claude leg,
  both verified and fixed per SHOULD-fix-by-default. (a) The
  `fixes_skipped` schema example used the free-form reason "reviewers
  disagreed on the value" instead of Terminal-outcomes' canonical
  `blocking-but-unfixable → main-session /diagnosing-bugs (no safe
  suggested_fix)` string — example aligned, disagreement detail moved to
  `details`. (b) Branch 2's `claim_quote not found` route was silent on
  adjudication, so a literal-minded fixer could stamp `verdict: REAL` on
  a finding routed precisely because it could not be verified — added the
  one-line no-verdict mirror of branch 3's rule (routed-for-verification,
  not a confirmed verdict).

## 0.3.18.26 — 2026-07-13

- **Ship-pre correctness-gate round 8 — 4 findings fixed, 1 rejected FALSE.**
  The rejected finding (codex, high) claimed the 交卷契约's
  `incidental_fixes`/`reported_defects`/`summary` envelope violates "ADR
  0062's three-signal envelope" and demanded DELETE; verified FALSE — ADR
  0062 appears in this repo only as an illustrative example inside the
  kill-axis ① description (SKILL.md ~L854) and a cross-reference in
  `prompts/cmr-reviewer.md`, not as a ratified constraint of this repo (no
  `docs/adr/` exists), so there is nothing for the fixer-output contract to
  violate.
- **Round 8, F2 — a "clear" confirmation round that itself edits is not
  terminal (`SKILL.md` Step 7 + Step 5 + doc-mode ②(c)).** Step 7's loop let
  STOP fire straight after a confirmation round even if that round had just
  fixed a non-blocking P3/P4 (per SHOULD-fix-by-default) — leaving that fix,
  which is new diff, forever un-re-reviewed, contradicting the file's own
  "the fix is itself new diff and must be reviewed" principle. Step 7 now
  carries the authoritative carve-out; the Step-5 positive-termination
  paragraph and doc-mode ②(c) early-stop arm each gained a one-line pointer
  to it (coverage-drift doctrine: one authority, pointers elsewhere). The
  doc-mode golden hash in `tests/test_doc_mode.py` was recomputed per that
  test's own intentional-edit procedure.
- **Round 8, F3 — First-duty and Terminal-outcomes acknowledge the
  no-verdict third state (`prompts/cmr-fixer.md`).** Round 7 created the
  "genuinely-unverifiable non-blocking → deferred with NO adjudications
  entry" path, but First-duty still promised "an empirical verdict on every
  finding" and Terminal-outcomes still claimed exhaustive (FALSE/REAL)
  coverage. Both summary lines now name the third state; the branch logic
  itself is unchanged.
- **Round 8, F4 — the doc-guard test's comment no longer overclaims
  (`tests/test_codex_review.py`).** Comment-only edit: part (A) is genuinely
  tied to the real backend invariant, part (B) is honestly scoped as a
  narrow textual net against the one recurring value-token phrasing — not an
  exhaustive guard against every semantically-equivalent rewording (docs are
  free text; residual risk accepted, per don't-over-defend). Assertions
  untouched.
- **Round 8, F5 — backfilled the missing `0.3.18.25` CHANGELOG entry.**
  `VERSION` and HEAD were at 0.3.18.25 but the changelog's latest entry was
  still 0.3.18.24; the round-7 commit had skipped its entry.

## 0.3.18.25 — 2026-07-13

- **Ship-pre correctness-gate finding (round 7, F1) — scope-clarification
  that incidental defects are a separate track from the Terminal-outcomes
  branches (`prompts/cmr-fixer.md`).** The Terminal-outcomes opening line now
  states it governs only **supplied/adjudicated** findings (the ones you were
  handed); an **incidental** defect spotted in passing is First-duty's
  separate, parallel track and does **not** flow through these branches. An
  incidental defect follows its own **severity-independent** rule — a clean
  mechanical one goes to `incidental_fixes`, a **non-trivial** one is reported
  in `reported_defects` for the main session regardless of its own severity —
  so a non-blocking incidental defect is still routed, never subject to this
  section's blocking/non-blocking split. No behavior change; closes a
  readability contradiction.
- **Round 7, F2 — unverifiable non-blocking findings route straight to
  `deferred[]` with no forced REAL/FALSE adjudication (`prompts/cmr-fixer.md`).**
  Round 4's own fix had said an unverifiable non-blocking finding "stays
  **REAL**" and is deferred, which asserted absence-of-evidence as
  proof-of-real — the same epistemic error as the FALSE-default it replaced.
  It now goes straight to `deferred[]` with **no** `adjudications` entry
  (neither REAL nor FALSE is confirmed), framed as a safety/visibility
  default: inability to verify is neither evidence-of-false (never laundered
  into a FALSE adjudication) nor evidence-of-true (not stamped REAL). Applied
  at both the Terminal-outcomes non-blocking branch and the Diff-requirements
  `claim_quote` sibling bullet; test expectations updated in
  `tests/test_defer_severity.py`. No new schema verdict value.
- **Round 7, F3 (4th recurrence — root fix) — the codex-effort doc-guard test
  now ties to the real backend selftest code invariant, not a wording pattern
  (`tests/test_codex_review.py`, `TESTING.md`, `SKILL.md`).** `TESTING.md`
  described `--selftest` as checking a fixed `model_reasoning_effort=medium`;
  the selftest actually validates `model_reasoning_effort=${CMR_CODEX_EFFORT}`
  (form, not value), and the round-6 backtick-`` `medium` `` regex guard was
  structurally blind to the compound `model_reasoning_effort=medium` token.
  Reworded `TESTING.md` to form-not-value with a pointer to the canonical
  `SKILL.md` §调用规范 site (the single source of truth), and trimmed the two
  Step-1 bullets to point at that source instead of restating the contract.
  Replaced the value-token regex guard with
  `test_selftest_validates_effort_form_not_value`, tied to the REAL invariant:
  part (A) extracts the actual selftest block from the backend and asserts it
  interpolates `${CMR_CODEX_EFFORT}` and hard-codes no
  `model_reasoning_effort=medium`; part (B) is a narrower textual net that no
  doc describes the selftest as checking that fixed value.

## 0.3.18.24 — 2026-07-13

- **Ship-pre correctness-gate finding (round 6) — a THIRD leftover site of
  the same "codex effort stated as absolute" class, and a definitive fix.**
  `SKILL.md` Step 1 (which a reader meets BEFORE Step 2's already-fixed
  callout) had two more sites: `codex effort = `medium`
  (`CMR_CODEX_EFFORT=medium`)` and `codex effort = `medium`, the same as
  per-slice`. Both stated the value flat with no override acknowledgment,
  and — crucially — neither contained the word "uniform", so round 5's
  regression guard (which only scanned `uniform`-bearing windows) was
  structurally blind to them. Reworded both to state `medium` as the
  **default** used when `CMR_CODEX_EFFORT` is unset, **overridable** (passed
  through verbatim, no whitelist), matching the L266/L289 sites' spirit.
  Only `SKILL.md` touched (no backend/dispatch/prompt changes).
- **Replaced the narrow guard with THE comprehensive one
  (`tests/test_codex_review.py`).** Rounds 4/5/6 each patched a
  progressively different but still-incomplete pattern (exact phrase →
  `uniform*` family → this). New guard
  `test_every_codex_effort_value_claim_carries_override_caveat` stops
  keying on any phrase/adjective and keys on the **value token itself**:
  every standalone backticked `` `medium` `` in an effort/reasoning context,
  across `SKILL.md` / `README.md` / `TESTING.md`, must carry an override
  token (`overrid`) within a 320-char window. The lone-backtick form cleanly
  selects genuine prose claims and excludes the `model_reasoning_effort=medium`
  code/config form and the `critical|high|medium|low` severity vocabulary
  with no carve-out list. Mutation-tested: reintroducing each of the three
  historical buggy phrasings (round-4 "mandatory and uniform", round-5
  "`medium` uniformly", round-6 "codex effort = `medium`") one at a time,
  in real SKILL.md context, makes the new guard fire — the one test that
  would have caught all three incidents from the start. Repo-wide
  scope-check (same pattern, all 11 operative `.md` files, CHANGELOG
  exempt): zero uncaveated instances remain.

## 0.3.18.23 — 2026-07-13

- **Ship-pre correctness-gate finding (PR #32, round 5) — one leftover
  site of round-4's F3 class.** The Step-2 "Reasoning-effort reality, per
  leg" summary table in `SKILL.md` still read `codex = medium uniformly …
  CMR_CODEX_EFFORT, pinned via -c so host config cannot drift` — mentioning
  `CMR_CODEX_EFFORT` only as the drift-guard, never as a genuine override.
  As the FIRST place a reader meets codex's effort behavior (before the
  L287 §调用规范 callout that round 4 fixed), it read as the same absolute
  "always medium, no exceptions" claim. Reworded to `medium **uniform
  default** for both ship-pre … and per-slice … overridable via
  `CMR_CODEX_EFFORT`, which is pinned via `-c` so unset host config cannot
  silently drift the value — see §调用规范 below`, matching the already-fixed
  callout's spirit (default + genuine override) without reintroducing a new
  inconsistency. Only `SKILL.md` touched (no backend/dispatch changes).
- **Widened the regression guard (`tests/test_codex_review.py`).** The old
  negative pin only asserted one retired exact phrase was absent — which is
  exactly why this leftover site slipped through round 4 undetected. Added:
  (1) a broader class guard that requires every `uniform…`+`medium` effort
  claim anywhere in `SKILL.md` to carry an override token
  (`CMR_CODEX_EFFORT` / `overridable`) within the same window; (2) a pin on
  the retired absolute `` `medium` uniformly `` shape; (3) a positive pin
  that the summary bullet itself states the override, so both known sites
  (summary + callout) are individually guarded.

## 0.3.18.22 — 2026-07-13

- **Three ship-pre correctness-gate findings (PR #32, round 4).**
  - *Finding 1 [P1] — `prompts/cmr-fixer.md` scope-banner header.* The
    opening banner's primary verb "is NOT yours — **route it** to the main
    session" was severity-unqualified, contradicting `## Terminal outcomes`
    (where a non-blocking finding is "never routed"). Reworded so the header
    states the finding is not yours to patch here and its actual disposition
    (fixed elsewhere / routed / deferred) depends on **severity** per
    Terminal outcomes — routing is the blocking-only exit, non-blocking is
    never routed. Mechanical bar and "do not guess" left intact. (The five
    other sites codex flagged were re-verified as genuine pointers, not
    restatements — not touched; no re-consolidation.)
  - *Finding 2 [P2, introduced by 0.3.18.21] — "cannot verify → FALSE" is
    an epistemic error.* Two sites (`## Terminal outcomes` non-blocking
    branch, and the Diff-requirements `claim_quote` bullet) told the fixer
    to adjudicate an unverifiable non-blocking finding **FALSE**. Inability
    to verify is the *absence* of evidence, not refuting evidence (FALSE
    requires concrete refuting evidence per First duty), so a real but
    hard-to-locate finding could vanish via a laundered FALSE. Both sites now
    keep it **REAL** and **deferred**, with the verification gap stated in the
    deferral's rationale.
  - *Finding 3 [P2] — stale "mandatory and uniform" effort docs.* The hard
    `exit 64` effort whitelist was removed in 0.3.18.15; the backend now
    passes any `CMR_CODEX_EFFORT` override verbatim with `medium` only as the
    unset-default. `SKILL.md` ("mandatory and uniform") and `README.md`
    ("uniformly medium") still implied a non-overridable pin. Both reworded to
    describe `medium` as the DEFAULT operational convention with a genuine
    verbatim override (no whitelist), keeping the pinning-prevents-config.toml-
    drift rationale. (`TESTING.md` line 38 describes the default selftest form
    check accurately — not touched.)
  - Tests: `tests/test_defer_severity.py` gains header + FALSE-on-unverifiable
    pins (positive + negative) and updates the two prior pins that asserted the
    now-corrected text; `tests/test_codex_review.py` gains doc pins grounding
    SKILL.md/README.md effort claims against the real backend contract.

## 0.3.18.21 — 2026-07-13

- **Root-cause consolidation of the "terminal outcomes" concept in
  `prompts/cmr-fixer.md` (ship-pre correctness gate, PR #32 Step 6, round 3
  — coverage-drift fix, not another point patch).** Versions 0.3.18.16
  through .20 each patched ONE site that stated an incomplete version of
  "what are the valid terminal outcomes for a supplied finding" (the
  First-duty overview, the Scope-rules routing tail, the Defer-protocol
  closing paragraph, the JSON `claim_quote` instruction). Round 3 found
  the SAME rule-class recurring on two more sites, so per the wiki Step-6
  "coverage drift ≠ architectural drift" doctrine (same rule-class on new
  sites each round → centralize the rule) this consolidates the concept
  into ONE authoritative **`## Terminal outcomes`** section instead of
  patching the Nth sentence.
  - **New `## Terminal outcomes` section** exhaustively enumerates every
    valid exit for a supplied finding, resolving all
    (FALSE/REAL) × (blocking/non-blocking) × (locatable/not) combinations
    to exactly one path: **FALSE (any severity)** → `adjudications` entry,
    resolved before any severity branch; **REAL, blocking** (P0/P1/P2; doc
    mode also P3) → fixed OR routed via `fixes_skipped`, never deferred,
    with the three named routed reasons; **REAL, non-blocking**
    (`low`/`clarity`; doc mode `clarity` only) → fixed OR
    deferred-with-all-three-parts, never routed. The violation clause is a
    REAL finding reaching NONE of these (a silent drop).
  - **Round-3 Finding 1 (non-blocking/clarity, Claude + codex) — the
    First-duty overview and intro summary line were not severity-qualified**,
    reading as if ALL non-trivial REAL findings route regardless of
    severity. Both now point at Terminal outcomes rather than asserting the
    fix-vs-route split inline; only blocking findings route, non-blocking
    findings fix-or-defer.
  - **Round-3 Finding 2 (medium/blocking, codex; also flagged by Claude) —
    the `claim_quote`-not-found instruction created an unblessed 4th
    outcome** (bare `fixes_skipped` reason, outside the terminal-outcome
    framework, tripping the terminal rule's own violation clause). Folded
    in as a NAMED blocking-route reason
    (`claim_quote not found → main-session /diagnosing-bugs (needs
    verification)`); on a non-blocking finding an unlocatable claim now
    routes to a FALSE adjudication, not a silent park.
  - **Every other site is now a pointer, not an independent restatement**:
    the Scope rules keep the classification (WHICH findings are fixable:
    medium is blocking, doc-mode low, MUST-NOT-fix conditions, the
    anti-down-rank ban) and point at Terminal outcomes for the route; the
    Defer protocol keeps the three-part deferral mechanics and points at
    the section; First-duty, the header, the intro, and the JSON
    `claim_quote` bullet all cross-reference it.
- `tests/test_defer_severity.py` consolidated to match: a `_section()`
  helper asserts the enumeration lives IN the single `## Terminal outcomes`
  section and is absent (as an independent restatement) from Scope rules
  and Defer protocol; the six input traces each pin to their one exit;
  negative pins confirm the old scattered restatements (bare
  `claim_quote not found` reason, tier-blind "neither fixed nor deferred",
  un-REAL-qualified drop set, low-only SHOULD-fix body, intro summary line)
  are gone.

## 0.3.18.20 — 2026-07-12

- **Two correctness fixes in `prompts/cmr-fixer.md` (ship-pre correctness
  gate, PR #32 Step 6, round 2).**
  - **Finding 1 (P1/high, codex) — the Defer-protocol terminal rule now
    recognizes a FALSE adjudication as a valid resolution.** The First-duty
    § establishes THREE per-finding actions (REAL → resolve, FALSE → reject
    with evidence in `adjudications`, incidental → separate patch), but the
    0.3.18.19 terminal rule enumerated only the two REAL-outcome branches
    (blocking → fixed-or-routed; non-blocking → fixed-or-deferred). A
    finding correctly adjudicated FALSE is neither fixed, routed, nor
    deferred, so under the literal "reaches none of these = violation"
    clause it would trip the violation flag — the same class of gap
    0.3.18.19 closed, for a third outcome category. Reworded so a FALSE
    adjudication (evidence in `adjudications`) is itself a complete valid
    resolution at ANY severity, resolved BEFORE the tier branch; only a
    finding adjudicated REAL proceeds to the blocking/non-blocking branch,
    and the silent-drop violation set is scoped to REAL findings.
  - **Finding 2 (P2/medium, codex) — the `deferred[]` schema severity is
    now a pipe-delimited enum.** The strict JSON `deferred[]` example
    hardcoded `"severity": "low"` (a single literal), but the defer-protocol
    prose allows a doc-mode `clarity` deferral and the sibling severity
    fields (incidental_fixes, reported_defects) use a pipe-delimited enum
    showing the valid set. Changed to `"severity": "low|clarity"` — the
    actual legal set for this field, consistent with the other enum fields.
- Regression pins in `tests/test_defer_severity.py` (positive + negative,
  repo phrase-pin style) for both: the terminal rule recognizes a FALSE
  adjudication as a valid resolution at any severity, resolved before the
  tier branch; `deferred[].severity` is the `low|clarity` enum, not a
  single `low` literal.
- Same-file sweep for the two bug classes (missing-category enumeration /
  under-built schema enum) across First-duty, Scope rules, Defer protocol,
  Concept sweep, and the full JSON schema found no further instances: the
  other severity enums (incidental_fixes, reported_defects) are already the
  full 5-value set, `verdict` is `REAL|FALSE`, `fixer_mode` is `doc|code`,
  and the First-duty three-action enumeration is complete.

## 0.3.18.19 — 2026-07-12

- **Two correctness fixes in `prompts/cmr-fixer.md` (ship-pre correctness
  gate, PR #32 Step 6).**
  - **Finding 1 (P1/high, codex) — the Defer-protocol terminal rule now
    recognizes valid routing as a resolution.** The section's closing
    sentence read "A finding that is neither fixed nor
    deferred-with-all-three-parts is a protocol violation." Its
    substantive rules are all scoped to `low`/`clarity`, so it
    contextually meant that tier — but 0.3.18.18 added a THIRD valid
    outcome for **blocking** findings: route via `fixes_skipped` to the
    main session's `/diagnosing-bugs` when they cannot be mechanically
    resolved. A fixer reading the sentence literally, in isolation, could
    flag a blocking finding it just validly routed (technically "not
    fixed" and "not deferred") as its own protocol violation. Reworded to
    enumerate the terminal outcomes per tier: a blocking finding must be
    fixed OR validly routed (routing is a resolution, not a violation); a
    non-blocking (`low`/`clarity`) finding must be fixed OR
    deferred-with-all-three-parts; only a finding reaching NONE of its
    tier's outcomes (a silent drop) is the violation.
  - **Finding 2 (P2 codex / P3 Claude, both independent) — the
    SHOULD-fix-by-default bullet now names `clarity` for code mode.** It
    enumerated only `low` in its body, but the immediately-following
    MUST-NOT-fix section back-references this exact rule to make a fixable
    `clarity` finding fix-eligible ("under the SHOULD-fix-by-default rule
    above"), and `SKILL.md`'s "cheap/low-risk P3/P4 should still be FIXED
    now" (P4 = clarity) says the same. Reworded to name the full code-mode
    non-blocking tier (`low`/`clarity`; doc mode: only `clarity`, since
    `low`/P3 is blocking there) and to make the drift stop-condition cover
    the whole tier ("If fixing these non-blocking findings keeps surfacing
    new findings") instead of only "the lows".
- Regression pins in `tests/test_defer_severity.py` (positive + negative,
  repo phrase-pin style) for both: the terminal rule recognizes valid
  routing as non-violating for blocking findings; the SHOULD-fix bullet
  names `clarity` for code mode.

## 0.3.18.18 — 2026-07-12

- **Close a three-way routing trap in `prompts/cmr-fixer.md`'s Scope rules
  (ship-pre completeness-gate P2, round 5).** A specific-but-realistic
  input had no valid exit: a **blocking** (`medium`/P2) finding classified
  **mechanical** by the header allowlist (typo/dead-anchor/stale-label/
  date/whitespace + zero-executing-code + single-site + provably-inert)
  whose `suggested_fix` is `n/a`/empty. MUST-fix said fix it (mechanical +
  medium); MUST-NOT-fix said never patch it (empty `suggested_fix`) —
  contradiction; the non-trivial→`/diagnosing-bugs` route's literal
  precondition ("non-trivial") did not apply, because the header makes
  mechanical and non-trivial **disjoint**; and the defer protocol covers
  only `low`/`clarity`, never P2. Net: not fixable, not deferrable, and the
  route didn't cover it → the fixer's own "neither fixed nor deferred =
  protocol violation" trap. **Fix:** reword the route trigger from "a
  blocking finding that is **non-trivial**" to "a blocking finding you
  **cannot mechanically resolve**", explicitly covering **both**
  non-trivial-by-nature **and** mechanical-by-classification-but-blocked-by-
  a-MUST-NOT-fix-condition (empty `suggested_fix` / reviewer disagreement /
  needs new content). Uses the **existing** `fixes_skipped` field and
  **existing** main-session hand-back — no new field, tier, or defer
  category. A distinct reason string `blocking-but-unfixable →
  main-session /diagnosing-bugs (no safe suggested_fix)` marks the
  MUST-NOT-fix-blocked case vs the behavioral-complexity `non-trivial →
  main-session /diagnosing-bugs`. Post-fix the trap example has exactly one
  route; routing is not patching, so no contradiction with MUST-NOT-fix
  remains. Scope check: the reword scopes to all three MUST-NOT-fix
  conditions, so reviewer-disagreement and needs-new-content blocking
  findings are covered too, not just empty-`suggested_fix`. Wording pins
  (positive + negative, with an embedded concrete-example trace) added in
  `tests/test_defer_severity.py`.

## 0.3.18.17 — 2026-07-12

- **Close a loose-coupling gap in `test_completeness_grades_gaps_and_gate_is_no_blocking`
  (ship-pre completeness-gate P1, PR #32).** The two mode-threshold
  assertions checked the mode label and its severity set as two
  *independent* substrings (`"code / ship-pre" in txt and "blocking = P0 /
  P1 / P2" in txt`). Presence anywhere in the normalized file satisfied
  each half separately, so the assertion did not verify the severity set
  is actually *coupled to* that mode's clause — its stated intent
  ("mode-dependent blocking thresholds spelled out"). Codex proved the gap
  with a poison copy: the real code/ship-pre clause was broken to
  "blocking = P0 / P1" (missing P2) while an unrelated "blocking = P0 / P1
  / P2" substring survived elsewhere, and the test still passed. Both
  asserts (code/ship-pre and doc mode) are now single **coupled-clause**
  substring checks (`"**code / ship-pre completeness gate** → **blocking =
  P0 / P1 / P2**"` and the doc-mode equivalent), matching the exact source
  wording in `prompts/cmr-completeness.md`. Verified by reproducing the
  poison: the old asserts pass on it (bug), the new coupled asserts
  correctly fail (gap closed). Test-assertion-quality fix only — the source
  protocol text was already correct and is untouched. Scope check: the
  other `A in txt and B in txt` sites in the PR's tests are prose-fragment
  smoke checks, not severity-value-to-mode coupling, so none share the
  identical bug class.

## 0.3.18.16 — 2026-07-12

- **Fix an internal contradiction in `prompts/cmr-fixer.md`'s Scope rules
  (ship-pre completeness-gate P2, PR #32).** The MUST-NOT-fix list carried
  a standalone unconditional ban — "`clarity` findings (author judgment)"
  — that directly contradicted the SHOULD-fix-by-default bullet
  immediately above it (and `SKILL.md`'s "cheap/low-risk P3/P4 should
  still be FIXED now ... NOT banked as backlog debt", where P4 = clarity).
  A fixer handed a cheap, obviously-correct clarity finding (a comment
  typo, a clear rename with an explicit `suggested_fix`) was told to fix it
  by one rule and forbidden to fix it by the next. The blanket
  severity-based clarity ban is removed; the list is now **severity-blind**
  and the three remaining conditions (no concrete `suggested_fix`,
  reviewer disagreement, requires inventing new behavior/content) already
  gate out the genuinely un-fixable clarity subset on their own merits. A
  clarity finding with a concrete fix, no disagreement, and no new-content
  invention is now fix-eligible like any other cheap/low-risk non-blocking
  finding. Scope check confirmed `SKILL.md` has no second instance — its
  clarity mentions are all about blocking/convergence status (correct,
  untouched). Wording pins added in `tests/test_defer_severity.py`
  (positive: severity-blind + clarity fix-eligible; negative: the old
  standalone `clarity` findings (author judgment) bullet is gone).

## 0.3.18.15 — 2026-07-12

- **Merge `codex/cmr-gpt56-sol-medium` into this branch** — the codex leg's
  default model moves `gpt-5.5` → **`gpt-5.6-sol`**, reasoning effort
  uniform **`medium`** for both per-slice and ship-pre (`backends/codex-review.sh`
  default; `CMR_CODEX_MODEL` / `CMR_CODEX_EFFORT` still override). The prior
  hard `CMR_CODEX_EFFORT != medium → exit 64` whitelist is removed —
  `codex-review.sh`'s sole job is avoiding codex invocation footguns
  (`--ephemeral` / `-o` / stdin pipe / no `-C` / scoped idle-kill /
  degrade), never restricting which model or effort the caller picks
  (owner ruling 2026-07-12): unset → default `gpt-5.6-sol` + `medium`; any
  explicit override (`luna`, `low`, `high`, …) passes through verbatim.
  `SKILL.md`, `README.md`, `TESTING.md` updated off the stale `gpt-5.5`
  references left over from before this merge.

## 0.3.18.14 — 2026-07-12

- **REVERSAL — the 钉子令牌 (nail-token) jurisdiction-handoff apparatus is
  removed** (`prompts/cmr-completeness.md`, `SKILL.md` Step 5, tests; owner
  authorization 2026-07-12). The nail-token mechanism introduced in 0.3.17.0
  and patched across eight subsequent commits (0.3.18.3, .4, .5, .8, .9, .10,
  .11, .12) is reverted, keeping **only** its original sound piece — the
  same-round 缺钉 (missing-nail) precondition. Two reasons, both verified
  against the repo:
  1. **It required cross-round persistence the skill has no way to
     implement.** `ak-cross-m-review` is a SKILL invoked by an external
     session; it holds no cross-round memory of its own, and a repo-wide grep
     confirms NO script or file anywhere (`backends/`, `scripts/`) implements
     the "orchestrator persists a `DONE-and-nailed surfaces` list across
     rounds and injects it into every round's dispatch packet" mechanism.
     Eight rounds of review-fixes were polishing the WORDING of a protocol
     describing a nonexistent implementation.
  2. **Even if implemented, the tamper logic was wrong.** "Any diff that
     modifies a nailed surface beyond its baseline ref = nail-tamper =
     blocking" had NO carve-out for a legitimate multi-commit fix addressing a
     currently-reported finding on that surface — it would unconditionally
     flag good engineering (e.g. a fixer's clean 3-commit refactor fixing a
     real bug) as a blocking violation.
- **What survives (the one sound piece):** judging any spec-surface DONE has
  a precondition — that surface's contract test is already in the repo; a
  missing nail is itself a blocking finding (category 缺钉/missing-nail) with
  a named suggested nail point. This is a **same-round, diff-and-repo-only**
  check — no persistence needed, so the stateless skill can actually run it.
  Renamed the completeness-lens section header `## 钉子令牌` → `## 缺钉闸
  (missing-nail gate)`.
- **Deleted:** the "nailed-surface" jurisdiction handoff, round-wide
  merged-ledger nail-authorization, qualifying/confirmation two-step nailing,
  baseline-ref / baseline-refresh, nail-tamper scoping, 钉上刻字 (engraving),
  and orchestrator-persistence paragraphs from `prompts/cmr-completeness.md`;
  the entire "Cross-round jurisdiction hand-off" note from `SKILL.md` Step 5.
  Reduced `tests/test_nail_token.py` (renamed → `tests/test_missing_nail_gate.py`)
  to the surviving 缺钉-precondition pins plus a reversal guard that fails if
  any deleted jurisdiction-handoff phrase re-appears in either file; removed
  the matching `test_step5_handoff_note_*` from `tests/test_doc_mode.py`.
- **Untouched (separate, unrelated mechanisms):** the severity-aware
  convergence machinery (P0–P4 blocking thresholds, two-round
  qualifying+confirmation convergence, 交卷契约 submission contract) and the
  doc-mode ②(c) majority-complete + zero-blocking-ledger check — including
  their golden-hashed ranges, which are not touched and need no recompute.

## 0.3.18.13 — 2026-07-12

- **[P2] Step-7 flow line presented deferral as the default action for
  P3/P4** (`SKILL.md` Step 7 — the loop; codex round-13). The flow arm read
  `P3/P4 only → reported-but-Deferred (交卷契约); they do NOT block...`. That
  conflated two orthogonal facts: (a) a P3/P4-only round does not block
  convergence and does not force another full-review round (TRUE — kept), and
  (b) the leading `→ reported-but-Deferred` reads as "the ACTION/outcome for
  P3/P4 is: defer them". (b) contradicts `prompts/cmr-fixer.md`'s
  SHOULD-fix-by-default rule (non-blocking tier should be FIXED now, then
  self-check二连; Defer is ONLY for the genuinely out-of-scope / needs-design
  / high-risk subset). An orchestrator reading only the Step-7 diagram would
  defer every non-blocking finding by default, banking work that should be
  fixed immediately. **Fix:** reworded the flow line so CLEAR-status
  (doesn't block, doesn't force a round — unconditional) is stated as
  ORTHOGONAL to whether the finding is FIXED; cheap/low-risk P3/P4 should
  still be fixed now (cross-referencing the fixer's rule), and Deferred is
  the narrow exception (the 交卷契约 still requires every P3/P4 stay reported
  either way). Scope-check confirmed the concur-vote frame (`SKILL.md`
  "those go to Deferred and do **not** cost its concur vote", pinned by
  `tests/test_convergence.py`) and the completeness-reviewer frame
  (`prompts/cmr-completeness.md` "does not block means goes to Deferred")
  are the correct vote/gate-accounting statements — "Deferred" there names
  the non-blocking bucket, not a fix-vs-defer default — and were left
  unchanged. Regression pin + negative pin in
  `tests/test_convergence.py::test_skill_step7_loop_two_round_severity`.

## 0.3.18.12 — 2026-07-12

- **[P2] Same-file stale phrase contradicts the 0.3.18.11 baseline-refresh
  rule** (`prompts/cmr-completeness.md` §钉子令牌 + `SKILL.md` Step-5
  "Cross-round jurisdiction hand-off" note; codex round-12). 0.3.18.11 added
  the refresh rule — a PERMANENTLY nailed surface's `DONE-and-nailed` entry
  records the **confirmation-round** state as its baseline ref, not the
  original qualifying-round baseline. But the SAME files still described the
  baseline ref generically in older prose that predated the refresh rule and
  contradicted it: the entry-list definition said the ref was **"captured at
  nail-authorization time"**, and the tamper-scoping paragraph keyed tamper to
  change **"beyond the nail-authorization baseline"** / **"relative to the
  state at which its nail was authorized"** (all = the qualifying-round
  state). A reviewer reading those lines in isolation — e.g. checking a LATER
  round's tamper — would revert to comparing against the stale qualifying-round
  baseline and reproduce the exact false-positive nail-tamper flag 0.3.18.11
  was meant to eliminate. Fix: ONE authoritative definition of the baseline
  ref (= the commit/tree ref **currently recorded on the entry**, which per the
  refresh rule is the confirmation-round state, refreshed exactly once at
  permanent hand-off); every other mention now just says "the baseline ref"
  without re-describing its capture time. Applied to BOTH files (two-file sync
  discipline, rounds 10-11). New `test_no_stale_nail_authorization_time_baseline_phrasing_whole_file`
  is a WHOLE-FILE guard so a future re-introduction of the stale phrasing
  ANYWHERE in either file is caught. No hashed range touched, no recompute.

## 0.3.18.11 — 2026-07-12

- **[P2] Stale baseline ref after a legitimate qualifying→confirmation
  change** (`prompts/cmr-completeness.md` §钉子令牌 + `SKILL.md` Step-5
  "Cross-round jurisdiction hand-off" note; codex round-11). The
  `DONE-and-nailed surfaces` entry's **baseline ref** is captured at
  QUALIFYING-round nail-eligibility time (0.3.18.5 beyond-baseline tamper
  scoping). But if the surface is legitimately modified BETWEEN the qualifying
  round and the confirmation round — e.g. a non-blocking P3 fix the
  confirmation round re-audits and approves on the UPDATED surface — the
  confirmation round hands the surface off permanently while the stored
  baseline still points at the ORIGINAL qualifying-round commit. Subsequent
  rounds comparing the cumulative diff against that stale baseline would then
  misclassify the confirmation-round-approved update as post-nail tampering (a
  false-positive nail-tamper flag on already-reviewed work). Fix: when the
  confirmation round permanently hands off a surface (independently reconfirms
  DONE-and-nailed, round-wide ledger clean again — 0.3.18.9/0.3.18.10), the
  **baseline ref is REFRESHED to the confirmation round's state** before the
  surface goes on the permanent list, capturing any legitimate
  qualifying→confirmation change; nail-tamper going forward is scoped beyond
  THIS refreshed baseline, refreshed exactly once at hand-off. Stated in BOTH
  files (two-file sync discipline from round 10). Everything else about
  nail-tamper (beyond-baseline scoping 0.3.18.5, qualifying/confirmation
  two-step 0.3.18.9/10) intact — narrow addition of WHICH commit the baseline
  points to. Both edits outside the doc-mode golden-hash ranges, no recompute.

## 0.3.18.10 — 2026-07-12

- **[P1] SKILL.md Step-5 hand-off note missed the confirmation-round gate**
  (`SKILL.md` Step-5 "Cross-round jurisdiction hand-off" note, ~L575-596;
  codex round-10). The 0.3.18.9 fix — a qualifying-round nail is NOT yet
  permanent; the next confirmation round must re-audit and independently
  reconfirm it before it leaves jurisdiction — landed **only** in
  `prompts/cmr-completeness.md` §钉子令牌. SKILL.md's mode-general Step-5
  note still carried only the 0.3.18.8 round-wide-merged-ledger precondition
  and equated a clean qualifying-round ledger with permanent nail
  authorization, so an orchestrator following SKILL.md literally would add a
  surface to the permanent `DONE-and-nailed surfaces` list immediately on a
  clean qualifying-round ledger — skipping the confirmation round's
  substantive re-audit, the exact hole 0.3.18.9 was meant to close. Fix:
  restate BOTH preconditions in the Step-5 note so the two files agree — (1)
  round-wide-merged-ledger clean earns **qualifying-round nail-eligibility
  only** (0.3.18.8), and (2) the surface stays in-jurisdiction until the
  **confirmation round independently reconfirms DONE-and-nailed** (0.3.18.9),
  with a qualifying-round nail not yet confirmed explicitly NOT on the
  permanent list. Cross-references `prompts/cmr-completeness.md` §钉子令牌 as
  the detailed source. cmr-completeness.md unchanged (already correct); Step-5
  note is outside the doc-mode golden-hash range, no recompute.

## 0.3.18.9 — 2026-07-12

- **[P1] Nailed surfaces skipped the confirmation round entirely**
  (`prompts/cmr-completeness.md` §钉子令牌, ~L158-172; codex round-9). As
  worded, a surface nailed in the qualifying round **permanently left
  completeness's jurisdiction immediately** — so the confirmation round
  (which is supposed to substantively re-verify convergence) could have
  nothing left to review if everything got nailed in round 1, and would
  trivially pass as the second "clear" round, defeating the two-round
  guarantee. Fix: nailing takes effect for jurisdiction purposes **only
  after it survives the confirmation round**. A surface nailed in a
  qualifying round is **not yet permanently out of jurisdiction** — the
  very next confirmation round still audits it (this is what makes the
  confirmation round substantive: it re-verifies the qualifying round's
  DONE-and-nail judgments). Only after the confirmation round
  independently confirms DONE-and-nailed does the surface permanently
  leave jurisdiction for ALL subsequent rounds. A qualifying-round nail
  not yet confirmed is **NOT on the `DONE-and-nailed surfaces`
  (out-of-jurisdiction) list**, so it stays auditable. Composes with the
  round-wide-merged-ledger precondition (0.3.18.8): nail-eligible this
  (qualifying) round → still audited next (confirmation) round → permanent
  only after that.
- **[P1] Doc-mode clear check filtered blocking findings by
  classification** (`SKILL.md` doc-mode ②(c), ~L886-904, and the Step-5
  mode-general note ~L601-606; codex round-9). The zero-blocking-ledger
  check (used for both the majority-complete-qualifying and the
  confirmation-round-clear gates) counted only blocking findings
  classified **original-defect** in the ②(a) ledger. A dissenting leg's
  blocking finding classified **fix-fix** or **invention** was silently
  excluded from the clear check — so a round with a real, unaddressed
  blocking finding could pass as "clear" if it landed in the wrong ledger
  category. Fix: the clear/convergence gate now counts **ALL blocking
  findings from any leg, regardless of classification** (original-defect,
  fix-fix, and invention all count toward blocking). The
  original-defect/fix-fix/invention split stays exactly as-is for its own
  purposes — the ②(b) bloat-line audit trigger and drift analysis — but
  never filters the clear/convergence gate.
- Golden hash: `SKILL.md`'s ②(c) edit is inside the doc-mode golden-hashed
  range (`## Doc mode discipline` → `## Anti-patterns`), so the hash was
  recomputed in this same commit
  (`616860ab…` → `d4557e19…`). The `prompts/cmr-completeness.md` edit is in
  §钉子令牌 (before `## Doc mode addendum`), outside the completeness
  addendum hash — that hash is unchanged. Phrase-pin regressions added in
  `tests/test_nail_token.py` (confirmation round re-audits a
  qualifying-round nail; permanent only after confirmation; negative that
  the immediate-on-qualifying wording is gone), `tests/test_doc_mode.py`
  and `tests/test_convergence.py` (all blocking findings count regardless
  of classification; negative that the classification-filtered clear check
  is gone).

## 0.3.18.8 — 2026-07-12

- **[P1] Nail authorization ignored a dissenting leg's blocking gap**
  (`prompts/cmr-completeness.md` §钉子令牌, ~L141-146; codex round-8). As
  worded, a single reviewer leg judging a surface DONE (with its nail)
  could add that surface to the persistent `DONE-and-nailed surfaces` list
  and take it out of completeness jurisdiction — **even when another leg in
  the same round reported a BLOCKING gap on that same surface**. Once
  nailed, later rounds skip the surface entirely, so neither the other
  leg's gap nor the DONE judgment ever gets the two-round confirmation the
  convergence mechanism requires — a single dissenting leg's finding was
  silently swallowed. Fix: a surface may be nailed **only when the
  round-wide MERGED LEDGER** — aggregating every leg's findings for that
  surface, the same aggregation the doc-mode zero-blocking-ledger check
  uses — **shows zero blocking finding on that specific surface that
  round**. One leg's DONE is necessary but not sufficient; if another leg
  flags a blocking gap on the same surface the same round, the surface is
  NOT nailed that round (fix, re-audit, nail once the merged ledger is
  clean for it). Same principle already applied to majority-complete in
  doc-mode ②(c). A single-reviewer dispatch (per-slice) degrades
  gracefully — the round-wide ledger trivially holds just that one leg's
  findings, no special case. `SKILL.md` Step 5's mode-general orchestrator
  note got the matching precondition so the orchestrator does not add to
  the list on one leg's DONE. Both edits are outside the doc-mode
  golden-hashed ranges (`prompts` `## Doc mode addendum` → `## The gate`;
  `SKILL.md` `## Doc mode discipline` → `## Anti-patterns`); no hash
  recompute. Phrase-pin regressions added in `tests/test_nail_token.py`
  (positive: round-wide merged-ledger precondition + graceful
  single-reviewer degrade + Step-5 mirror; negative: old "single leg DONE +
  nail = leaves jurisdiction" wording gone).

## 0.3.18.7 — 2026-07-12

- **[P2] Mode-blind wording in the Step-5 concur definition** (`SKILL.md`
  Step 5, ~L552-562; codex round-7). The paragraph's first half correctly
  defines doc-mode blocking as P0/P1/P2/P3 (only P4 exempt), but the next
  sentence said "P3/P4 findings … do **not** cost its concur vote" with no
  mode qualifier — contradicting the first half for doc mode, where P3 IS
  blocking and SHOULD cost the concur vote. An implementer following the
  unqualified sentence literally would defer a doc-mode P3 that should be
  fixed/routed and could prematurely enter the confirmation round. Reworded
  to mode-qualify the disposition: non-blocking = **P3/P4 in
  correctness/code mode, P4 only in doc mode**; and added an explicit "in
  doc mode P3 **is** blocking and **does** cost the concur vote" clause.
  Scope-check of every other "P3/P4" / "low/clarity" non-blocking mention
  in `SKILL.md` + `prompts/*.md` found no other mode-blind instance — the
  defer-severity protocol (`SKILL.md` L802-809) and the completeness
  prompt's blocking table were already correctly mode-qualified. Edit is
  outside the doc-mode golden-hashed range (`## Doc mode discipline` →
  `## Anti-patterns`); no hash recompute. Wording-pin regression added in
  `tests/test_convergence.py` (positive: mode-split disposition + doc-mode
  P3-blocking clause; negative: old unqualified sentence gone).

## 0.3.18.6 — 2026-07-12

- **[P2×2] Fixer output schema systematically under-built vs the prose it
  serves** (`prompts/cmr-fixer.md`; codex round-6, two findings that are
  one class — the same class as the round-3 FALSE-adjudication-field fix).
  A holistic audit enumerated every output the fixer PROSE requires and
  checked each has a representable strict-JSON field with a complete
  severity enum:
  - supplied-finding fix → `diff` (was already representable).
  - per-finding REAL/FALSE adjudication + evidence → `adjudications[]`
    (finding_id/verdict/evidence; verdict enum REAL|FALSE) — complete,
    the FALSE-reject-with-evidence duty is representable.
  - incidental mechanical fixes → `incidental_fixes[]`: its `severity`
    enum was the 4-value `critical|high|medium|low`, so a typo/comment/
    pure-formatting incidental (which is `clarity`/P4) was
    **unrepresentable**. Added `clarity` → full 5-value set.
  - non-trivial incidental defects routed to the main session →
    `reported_defects[]`: same 4-value gap, now the same 5-value set for
    consistency (a clarity-level non-trivial defect is representable).
  - the "report loudly / 大报" narrative required a **summary**, but the
    strict schema had no such field (only a vague optional `notes`), and
    output forbids text outside the schema → the loud-report duty was
    **unrepresentable**. Added a top-level `summary` field and pointed
    both report-loudly instructions (incidental_fixes and reported_defects)
    at it; the `summary` explicitly notes a FALSE verdict's refuting
    evidence still lands in `adjudications`, never here (round-3 rule
    preserved).
  - skipped/deferred → `fixes_skipped[]` and `deferred[]`: unchanged; the
    defer protocol (P3/P4 code, P4 doc; deferred severity is low/clarity
    by design — the one field with a documented reason to exclude the
    blocking severities) is correctly represented.
  No fix-loop behavior changed — 交卷契约 first duty, EXAM/concept sweep,
  钉子/convergence references, mechanical-vs-nontrivial routing, and
  P2-blocking defer-severity all preserved; the change ADDS schema fields,
  completes two enums, and points prose at concrete fields. cmr-fixer.md is
  outside every golden-hash range (no hash test references it). Tests:
  `tests/test_submission_contract.py` gains 4 pins (both severity enums
  include `clarity`; the top-level `summary` field exists and the
  report-loudly instructions reference it; negatives that the clarity-less
  enum and the fieldless "in your summary" are gone, and that FALSE
  evidence still routes to `adjudications`).

## 0.3.18.5 — 2026-07-12

- **[P1] Nail-tamper × cumulative-diff full-re-review × two-round
  convergence — a 3-way interaction bug** (`prompts/cmr-completeness.md`,
  `SKILL.md` Step 5; codex round-5 P1). The 钉子令牌 rule said "any diff
  touching a nailed surface → nail-tamper → blocking", but SKILL.md makes
  every round full-re-review the **cumulative** diff (vs main). A surface
  judged DONE-and-nailed in an early round STILL appears in the cumulative
  diff of later/confirmation rounds — its authorized change is part of the
  PR. "Any diff touching a nailed surface = tamper" therefore mis-flagged
  that already-authorized-and-nailed change as tampering → the confirmation
  round always yielded a blocking finding → the new two-round convergence
  could **never** complete. Fix: nail-tamper is scoped to change **beyond
  the nail-authorization baseline** — a NEW change layered on top of the
  nailed baseline, checked against a **baseline ref** the DONE-and-nailed
  entry now carries (the commit/tree ref, or the nail test's state, at
  nail-authorization time). The original nailed change remaining unchanged
  in the cumulative diff is out-of-jurisdiction (skip), explicitly NOT
  re-flagged; only a post-nail modification is nail-tamper → blocking.
  Updated BOTH the completeness-lens 钉子令牌 entry+rule and SKILL.md Step 5's
  orchestrator-persistence note (each `DONE-and-nailed surfaces` entry now
  carries the nail's baseline ref alongside its authorization token). No
  golden hash changed — the 钉子令牌 section is before the doc-mode addendum
  hash, and the Step 5 edit is outside the doc-mode ②–⑤ hash range. Tests:
  the "any touch" pin replaced with baseline-scoped positive pins + a
  negative pin that the mis-flagging wording is gone + baseline-ref entry
  pins on both files.

## 0.3.18.4 — 2026-07-12

- **[P1] DONE-and-nailed jurisdiction hand-off was placed doc-mode-only**
  (`SKILL.md`, codex round-4 P1 — a placement error from 0.3.18.3). The
  钉子令牌 hand-off ("later rounds do NOT re-litigate an
  already-DONE-and-nailed surface") applies to **all** completeness modes,
  but 0.3.18.3 put the **orchestrator** persistence+injection instruction
  ("persists a `DONE-and-nailed surfaces` list across rounds and injects it
  into every round's dispatch packet") *only* inside §Doc mode discipline
  ②(a). So a plain code/ship-pre completeness multi-round loop never built
  that state → a fresh reviewer re-audited already-handed-off surfaces, and
  nail-tamper detection was unenforceable in code mode. Fix: **hoisted** the
  orchestrator persistence+injection to a **mode-general** location (Step 5
  termination), stated for **EVERY completeness round — the ship-pre code
  gate AND doc mode**; removed the doc-mode-scoped copy from ②(a).
  `prompts/cmr-completeness.md`'s stale ②(a) back-reference re-pointed to
  §Step 5 and generalized to every completeness mode. Doc-mode golden hash
  recomputed (the ②(a) removal is inside the hashed range). Tests: the
  ②(a) pin became a mode-general Step 5 pin with a regression assertion
  that the instruction is NOT confined to the doc-mode section.

## 0.3.18.3 — 2026-07-12

- **Four self-contradictions in the recently-landed protocol additions
  resolved.** Caught by codex's round-3 outside-voice review of the
  submission-contract branch (one P1, three P2). Each was a case where a
  new rule was stated in one place but silently contradicted by an
  older/neighboring rule.
  - **#1 [P1] Doc-mode termination vs the all-concur rule** (`SKILL.md`
    Step 5 + doc-mode ②(c)). Step 5's "two consecutive clear rounds = every
    non-degraded leg concurs" contradicted doc mode's still-standing
    **majority**-complete convergence. Fix: Step 5 now names doc mode as an
    **explicit exception** to all-legs-concur — doc mode converges on
    *majority-complete AND a zero-blocking-(P0–P3)-original-defect ledger
    that aggregates ALL legs' findings, dissenters included*. Because the
    ledger clause spans every leg, a minority leg's blocking finding keeps
    the ledger non-zero → NOT converged regardless of the majority vote:
    the dissent cannot be swallowed. ②(c) reworded to make the
    all-legs span of the ledger check explicit (both the qualifying and
    confirmation rounds). Correctness/code modes stay all-legs-concur.
  - **#2 [P2] FALSE adjudication had no schema field** (`prompts/cmr-fixer.md`).
    The first-duty told the fixer to reject a FALSE finding "with evidence
    written into your summary", but the strict JSON schema had no such
    field. Fix: a structured `adjudications` array
    (`finding_id` / `verdict` REAL|FALSE / `evidence`); the FALSE-rejection
    instruction now points at that field, not a vague summary.
  - **#3 [P2] `incidental_fixes` vs the "nothing more" scope ban**
    (`prompts/cmr-fixer.md`). The new incidental-fix clause conflicted with
    the intro "fix exactly what the findings identify, nothing more" and
    Safety rule #2's scope-expansion ban. Fix: both old rules now carve out
    `incidental_fixes` as the **single** sanctioned scope exception and
    cross-reference each other — the supplied-finding diff still fixes
    exactly the findings (no gold-plating); a real mechanical defect seen
    in passing goes to its own separate patch, and that is the only
    exception, not a licence for general gold-plating.
  - **#4 [P2] DONE-and-nailed cross-round state was not persisted**
    (`prompts/cmr-completeness.md` 钉子令牌 + `SKILL.md` ②(a)). "Later
    rounds do NOT re-litigate an already-DONE-and-nailed surface" was
    unenforceable — a fresh reviewer had no field naming the nailed
    surfaces. Fix: the orchestrator persists a **`DONE-and-nailed
    surfaces`** list (each with its nail's authorization token) across
    rounds and injects it into every round's dispatch packet; the
    completeness reviewer treats listed surfaces as out-of-jurisdiction and
    audits only the remaining clauses plus any diff that touches a nailed
    surface (a nail-tamper → blocking, per 钉上刻字).
  - `SKILL.md` doc-mode section edits (②(a), ②(c)) land inside the
    golden-hashed range, so `tests/test_doc_mode.py`'s SKILL.md hash was
    recomputed in this commit (the RECORDED-RULE conscious-edit act); the
    `cmr-completeness.md` addendum hash is unchanged (the 钉子令牌 edit is
    outside the hashed addendum range).
  - Tests: new wording pins (positive + negative) for the Step-5 doc-mode
    exception + all-legs ledger, the `adjudications` schema field, the
    incidental-vs-scope carve-out, and the packet `DONE-and-nailed
    surfaces` injection; existing FALSE-adjudication pins updated to the new
    wording.

## 0.3.18.2 — 2026-07-12

- **Fixer output contract extended so incidental fixes are representable
  as separate patches.** The 交卷契约 first-duty section told the fixer
  subagent that other real defects seen in passing should be "small-fix
  them, committed independently" — but the same prompt defines the
  subagent's only output as ONE strict-JSON response carrying a SINGLE
  unified diff, with no commit mechanism. The subagent literally could not
  "independently commit" an incidental fix: it would have to pollute the
  supplied-finding patch or silently drop the required action. Level
  mismatch — "独立提交 (independent commit)" is a fix-LOOP / main-session
  action wrongly assigned to a subagent whose interface can't do it.
  Caught by codex's round-2 outside-voice review of the
  submission-contract branch (P2).
  - `prompts/cmr-fixer.md`: the fixer output schema gains a dedicated
    `incidental_fixes` array — each entry is a target, its **OWN separate**
    unified diff (never merged into the supplied-finding `diff`), a 1–2
    sentence rationale, and a severity — plus a `reported_defects` array
    for non-trivial incidental defects the subagent only reports (routed to
    the main session's `/diagnosing-bugs`, never risk-patched).
  - The first-duty incidental-defect clause is reworded: the subagent
    **surfaces** each incidental defect as its own `incidental_fixes` entry
    (separate patch) and **reports it loudly** — the **main session** is
    what lands each entry as an independent commit. "大报 / never look away"
    is preserved; "committed independently" (a subagent-level instruction it
    could not satisfy) is gone.
  - The 交卷约定 semantic (小修 / 独立提交 / 大报) is now representable
    end-to-end: the subagent produces separable patches, the main session
    commits each independently. No wiki change needed — §额外硬规则 #8's
    "独立提交" is an orchestration-level end-state, not a subagent action.

## 0.3.18.1 — 2026-07-12

- **Fixer / defer protocol aligned to severity-aware convergence — P2 is
  blocking, not deferrable.** 0.3.18.0 made **medium/P2 a blocking
  severity** (a round is CLEAR only with no P0/P1/P2; doc mode no
  P0/P1/P2/P3), but the fixer/defer protocol still treated medium/P2 as
  "SHOULD fix … may defer." A fixer could therefore legitimately defer a
  P2 that still blocks convergence → the next full review re-finds it →
  the loop never terminates. Caught by the codex outside-voice review of
  the submission-contract branch; wiki tdd-autonomous-dev §切片内纪律 sync
  (P2 into the 必修/阻塞级 row with P0/P1, deferrable row = P3/P4 only) was
  done by the main session and this aligns the skill to it.
  - `SKILL.md` defer protocol: deferral is now **ONLY for the non-blocking
    tier — P3/P4 in correctness/code mode, P4 only in doc mode** (P3/low
    blocks in doc mode). A blocking finding (P0/P1/P2; doc mode also P3)
    is **must-fix-or-route, NEVER deferred**; trying to defer one = not
    converged → escalate to the user, do not silently stage it as
    converged. (P2→P3 down-ranking to escape = same anti-pattern as
    critical/high→medium.) The staging example tag went `[P2]` → `[P3]`.
  - `prompts/cmr-fixer.md`: **medium/P2 moved from the deferrable set into
    MUST-fix (blocking)** — same obligation as critical/high (mechanical
    fix now, or route non-trivial to the main session's
    `/diagnosing-bugs`). Deferrable set is now **low/clarity (P3/P4) in
    correctness/code mode, clarity only (P4) in doc mode** (low/P3 blocks
    in doc mode). Structured-deferral obligation re-keyed to low/clarity;
    the "never down-rank critical/high→medium" ban mirrored to "never
    down-rank medium→low." EXAM-818 sweep, critical/high routing, the
    交卷契约 first-duty section, and the JSON schema untouched.
  - `tests/test_defer_severity.py`: positive+negative phrase pins that the
    deferrable tier is P3/P4 (P2 gone) and medium = blocking/must-fix, so
    a re-sync cannot silently revert. The doc-mode golden-hash range is
    untouched (the defer protocol sits outside it).

## 0.3.18.0 — 2026-07-12

- **Severity-aware convergence + two-round confirmation for ALL modes
  (user ratification 2026-07-12; wiki §终止信号 sync done by the main
  session).** A review round is now **CLEAR** when it has **no blocking
  finding**, where blocking is mode-dependent: **correctness / per-slice
  and the ship-pre completeness gate on code → P0/P1/P2** (P3/P4 defer);
  **doc mode → P0/P1/P2/P3** (only P4 defers). **P4 never blocks in any
  mode.** Every finding is still graded and REPORTED (交卷契约,
  0.3.17.0) — P3/P4 go to Deferred, never silently dropped.
  - **Two-round confirmation extended from doc-only to every mode.**
    Positive termination = **two consecutive clear rounds** (a qualifying
    round + a full-re-review confirmation round, both clear). A single
    clear round no longer converges on its own; a blocking finding in the
    confirmation round re-qualifies the early-stop arm from scratch. The
    relaxed predicate "clear = no blocking" is what makes two-round
    non-endless (the old "zero-finding = approve" × two-round never
    would).
  - `prompts/cmr-reviewer.md`: `converged` verdict redefined — you raised
    **no critical/high/medium** defect this round (you MAY have raised
    low/clarity, still reported, they don't cost the approve vote);
    `findings` = at least one critical/high/medium. (Was "found no
    defects".)
  - `prompts/cmr-completeness.md`: each gap now **graded P0–P4**; the gate
    is **no BLOCKING gap** (mode-dependent threshold) instead of the old
    zero-any-verdict binary; `complete` = no blocking gap (deferred P3/P4
    — P4 in doc mode — allowed), `gaps` = at least one blocking gap.
  - `SKILL.md`: Step 5 §终止信号 (concur = no blocking finding; positive
    termination = two consecutive clear rounds, all modes), Step 7 loop
    (blocking → FIX; clear → confirmation round; two consecutive clear →
    STOP), and doc-mode ②(c) (early-stop predicate now "zero **blocking
    (P0/P1/P2/P3)** original-defect findings — only P4 exempt"). The ②(c)
    edit is inside the golden-hashed doc-mode section → golden hash
    recomputed in `tests/test_doc_mode.py` in the same commit.
  - `tests/test_convergence.py`: new phrase pins (positive + negative
    counterpart) for the severity-aware verdict/gate/loop wording;
    `tests/test_doc_mode.py`: early-stop assertions updated to the new
    blocking predicate + recomputed SKILL.md doc-mode golden hash (the
    completeness addendum hash is unchanged — the severity layer lands
    outside that hashed range).

## 0.3.17.0 — 2026-07-12

- **Review submission contract (交卷契约) landed in the prompts (ADR 0130;
  user ratification 2026-07-12).** The wiki sync was already done by the
  main session (§额外硬规则 #8); this is the skill→wiki alignment that puts
  the executing shaping language into the prompt files.
  - `prompts/cmr-reviewer.md` + `prompts/cmr-completeness.md`: each gains a
    **Submission contract** section — report EVERY finding/gap you see this
    round; severity/verdict is a label you attach, not a threshold a
    finding must clear to be worth reporting; delivery is complete only
    once every one is written down. Applies to every review mode; "report
    all" means the *findings* you see, never a licence to pad the design
    with suggested text; doc-mode ②–⑤ anti-runaway discipline is untouched;
    progressive exposure (a hole visible only after an earlier fix) is not
    a contract breach.
  - `prompts/cmr-fixer.md`: gains a **First duty** section — adjudicate
    each supplied finding empirically against the source (REAL → resolve +
    same-class Concept-sweep, unchanged; FALSE → reject WITH EVIDENCE in
    the summary for next round's fresh reviewer; other real defects seen in
    passing → small-fix, committed independently, + report loudly).
  - `tests/test_submission_contract.py`: phrase pins (positive + negative
    counterpart each) for all three files, so a re-sync that softens the
    contract back to "report a couple" fails the suite. Root cause: #860
    (21+ serial rounds from the missing shaping language).
- **钉子令牌 (nail token) + 刻字惯例 landed in the completeness lens (ADR
  0130; wiki §额外硬规则 #9 sync done by the main session; user ratification
  2026-07-12).** The second half of 0.3.17.0.
  - `prompts/cmr-completeness.md`: gains a **钉子令牌** section — judging any
    spec-surface DONE has a precondition (that surface's contract test is
    already in the repo); a missing nail is itself a **blocking** finding
    (category 缺钉 / missing-nail) with a named suggested nail point. Once
    DONE-and-nailed, the surface **permanently leaves completeness's
    jurisdiction** (later rounds do not re-litigate it; its guard is the
    red test at the write-point + the correctness channel — the split is
    temporal, the token is the test). **刻字 (engraving):** a contract-nail
    test's name / first-line comment carries an authorization token (e.g.
    `契约钉 #491·永不喂全知`); suggested nails follow the convention, and an
    engraved nail in the diff with no authorization provenance (issue AC /
    ADR / prior-round ruling) is blocking — same family as the existing
    `preexistingAssertionTouched` assertion-hunting and the #732
    silent-nail-flip prohibition.
  - `tests/test_nail_token.py`: phrase pins (positive + negative
    counterpart each) for both semantics, so a re-sync that downgrades a
    missing nail below blocking or re-pulls a DONE-and-nailed surface back
    into the completeness lens fails the suite.
## 0.3.16.1 — 2026-07-12

- Constitution-check example in `prompts/cmr-reviewer.md` names ADR 0062's
  own carve-outs (typed claimed-fix coverage / suppression-governance) so
  the kill-axis targets free-text fate-forking, not the preserved typed
  checks (PR #862 coderabbit r1).

## 0.3.16.0 — 2026-07-12

- **① Constitution packet + kill-axis de-scoped from doc-mode-only to EVERY
  review mode (owner decision 2026-07-12).** The doc-ONLY narrowing was an
  unratified editorial choice; the #604 closure machines entered a
  code-diff review through the unguarded suggestion channel and killed
  live family runs on 2026-07-12. `prompts/cmr-reviewer.md` (correctness
  lens) now carries the constitution-check block; golden hash + scope
  test updated in the same commit per the RECORDED RULE recipe.

## [0.3.15.1] - 2026-07-06

### Changed — codex idle-timeout default 480s → 900s (user decision; wiki updated to 15min the same day — in sync)

An xhigh codex reviewer was false-killed at the 8min idle threshold again
(the same failure mode that killed the 3min threshold): deep-reasoning /
large-diff runs go silent for many minutes before the first byte.
Escalation history: 3min → 8min → **15min**.

- `backends/codex-review.sh`: `CMR_CODEX_TIMEOUT` default 480 → **900**
  (still IDLE/silence-based, never a total wall-clock cap; scoped kill
  unchanged). Now matches agy's `--print-timeout 15m`.
- `SKILL.md` Step 2: hang judgment 8min → 15min. Wiki §额外硬规则 #4 was
  updated to 15min the same day (vault `b5495e8`) — skill and wiki in
  sync; do not regress either side on a re-sync.
- `tests/test_codex_review.py::test_default_idle_timeout_is_900s` pins
  the default (red at 480, green at 900).
- NOTE (outside this repo, for the user): the "hang 判定 = > 8min" line
  in `~/.claude/CLAUDE.md` (Claude 特有 section; no line number — the
  file shifts) needs updating to 15min. (Correction 2026-07-06:
  `~/.codex/AGENTS.md` does NOT carry this line — it sits outside the
  byte-identical SHARED block, so only the one file needs the edit.)

- wiki-wins contract qualified (correctness-gate r2 P1): the SKILL.md
  intro + README "the wiki wins" sentences now carry the ⚠ RECORDED RULE
  exception — deliberate, user-decided divergences reconcile by their
  decision record, never silently overwritten wiki-ward (the
  unconditional contract contradicted the do-not-drop blocks). Stale
  "pending wiki upstream" / "wiki still says 8min" claims corrected:
  the doc-mode discipline + 15min WERE upstreamed the same day (vault
  `b5495e8` / `da04ff5` / `e06bcfe`). Pinned by
  `test_wiki_wins_contract_carries_recorded_rule_exception` +
  `test_no_stale_pending_upstream_claims`.

Suite green at every commit on this branch; selftest green. Exact test
counts live in `pytest` output, not here — the count line itself drew a
completeness finding when it went stale, and a with-count restatement
of this very rule drew the next one.

## [0.3.15.0] - 2026-07-06

### Added — doc-mode discipline: the additive-runaway defense (RECORDED RULE; upstreamed to the wiki same day)

A review of a **design text** is structurally additive — every finding
adds text, every fix grows the reviewable surface. Evidence #440: 34
rounds, 121 fixes (7% original-defect / **58% fix-fix** / 23% invented
mechanisms), 2.4× body bloat, majority-complete at round 3 ignored for
~30 more rounds — and **the Step 6 drift triple never fired once**
(quantity drift watches "count not decreasing"; a doc runaway resolves
findings every round while the text grows, so the triple is blind to it).
Origin: Fable's 5 doc-mode proposals, re-assessed quality-first.

- `SKILL.md` new **§Doc mode discipline** (design-text reviews ONLY;
  code-diff mode untouched):
  - **① Constitution packet + kill-axis** — dispatcher collects the
    project's decided ADRs + user-stated principles onto packet page one;
    legs get a second mission to find should-not-exist mechanisms and
    recommend **DELETE, which outranks patching** (subtraction must be
    explicitly licensed — an add-only lens can only lengthen the text).
  - **② Ledger + stop signals** — (a) per-round fix classification
    `original-defect / fix-fix / invention` (the measuring instrument,
    lands first); (b) **1.5× bloat line as a ledger-audit trigger, not a
    death line** (legit growth continues, fix-fix growth escalates);
    (c) early stop: majority-complete + zero original-defect findings → one
    **FULL confirmation round** (no anti-pattern-#14 exception — the
    spot-check variant was rejected), again majority-complete AND again
    zero original-defect findings → converged (a fresh original-defect finding
    in the confirmation round blocks convergence — the same blocker-free
    predicate applies at trigger AND terminal; correctness-gate P1 fix); (d) **round gate at 10 = escalation checkpoint, NOT a
    hard cap** — escalate to the user with the ledger, user rules
    continue/close; code mode keeps no-cap. **10 restores cmr's original
    founding value** (user decision 2026-07-06; it had been silently
    forgotten — `tests/test_doc_mode.py` now pins it).
  - **③ Anti-minutes-ification** — a doc fix changes the conclusion,
    never appends per-round argumentation to the body; body length
    decrease-only by default.
  - **④ Dead-leg standing degrade** — 2 consecutive dead rounds → stop
    re-dispatching; `standing-DEGRADED` in every round report; re-probe
    at the escalation checkpoint (#440: gemini 429'd empty six rounds
    and was re-dispatched every time).
  - **⑤ Self-check 三连** — doc mode adds "fix mechanism itself holds +
    no new contradiction with sibling issues" to the mandatory 二连.
- `prompts/cmr-completeness.md` gains a scoped **Doc mode addendum**
  (constitution check + kill-axis + anti-minutes; explicitly licensed to
  subtract; code mode skips it).
- `tests/test_doc_mode.py` pins every element above so a wiki
  re-sync cannot silently drop the section — per-element real-value pins
  for diagnosability, plus a **golden-hash freeze** of the entire
  normalized doc-mode section + prompt addendum (the fix-coverage-drift
  centralization from review rounds 1-2: phrase-by-phrase pinning is
  structurally non-exhaustive, so the tail is closed by an exact-content
  hash; editing the section means updating the hash in the same commit —
  a visible, conscious act).

## [0.3.14.2] - 2026-06-24

### Changed — the Claude leg is Opus 4.8; cmr no longer uses Fable (recorded rule)
Operational decision (user, 2026-06-24): given Fable's quota scarcity, cmr
will **not dispatch Claude Fable 5 on any leg** — the Claude reviewer leg
is **`claude-opus-4-8` (Opus 4.8), period**, even when Fable is available.
This is a **deliberate skill-vs-wiki divergence**: the wiki (§操作规程
model table) says "use the strongest available Claude = Fable when up",
which is the *ideal*; the skill's operational choice is Opus 4.8.

- SKILL.md: the Step-2 Claude-leg model bullet drops the "fable when up /
  revert to fable / needs client v2.1.170+" machinery and pins Opus 4.8,
  with a prominent **⚠ RECORDED RULE** callout stating the divergence and
  **"do NOT re-add Fable on a wiki re-sync"** (same standing-divergence
  handling as the kept agy warm+retry). The two Fable-specific degrade
  rows (Fable-safeguards auto-routing to Opus; the `fable` alias needing
  client v2.1.170+) are removed — there is no Fable leg to fall back FROM.
  README.md matches; anti-pattern #9's "opus / fable" → "opus".
- No behavior change to the dispatch/merge/loop engine; the Claude leg
  simply runs Opus 4.8 unconditionally now.

40 tests pass; selftest green.

## [0.3.14.1] - 2026-06-24

### Changed — rename gate skills to the `ak-cmr-` namespace
The two gate skills shipped in 0.3.14.0 as `cmr-completeness` /
`cmr-correctness` — off-namespace next to the engine `ak-cross-m-review`.
Renamed to **`ak-cmr-completeness`** / **`ak-cmr-correctness`** (skill dirs,
frontmatter `name:`, wrapper bodies, `install-skills.sh`, SKILL.md / README
references, and `tests/test_gate_skills.py`). The **prompt file**
`prompts/cmr-completeness.md` is unchanged — it is a prompt artifact, not a
skill. `install-skills.sh` now links `ak-cmr-completeness` /
`ak-cmr-correctness`; re-run it to refresh the symlinks.

## [0.3.14.0] - 2026-06-24

### Added — the completeness lens is now an EXECUTABLE prompt (`prompts/cmr-completeness.md`)
The Step-5 completeness gate never actually ran. The only dispatchable
reviewer prompt was `cmr-reviewer.md` — hardcoded to the **correctness**
lens ("find real correctness defects"). The completeness lens existed
**only as prose** in SKILL.md ("append a design-completeness lens to
cmr-reviewer.md"), with no artifact and no selector — so `--scenario
ship-pre`, which is supposed to run completeness THEN correctness, could
operationally dispatch nothing but correctness. The "两道分跑 / 严禁合一"
discipline was unenforceable because half of it (the completeness pass)
had no prompt to dispatch. This is the structural root cause of a ship-pre
cmr only ever exercising correctness — not worker laziness.

- **New `prompts/cmr-completeness.md`** — the executable completeness lens:
  audit each spec clause for delivery (DONE/PARTIAL/NOT-DONE for features +
  CONFORMS/VIOLATES/UNVERIFIED-GAP for constraints/delegations/exemptions),
  **chase the reference chain** (ground against the authority the spec
  names), **exercise behavioral keys** (run a gate/fix-loop/guard with an
  injected defect — green tests are not completeness evidence), with its
  own verdict line `CMR-VERDICT: complete | gaps`. It carries the full
  rubric that previously lived as scattered prose (dec9de6 / e3999be).
- **Two named gate skills** (`skills/cmr-completeness/`,
  `skills/cmr-correctness/` — renamed to `ak-cmr-*` in 0.3.14.1) — the
  user-facing entry points. Each is a
  thin one-line wrapper that invokes the `ak-cross-m-review` engine with
  `--lens completeness` / `--lens correctness`. The agent picks the skill
  that **names** what it means (completeness vs correctness) instead of
  trusting a `--lens` flag it might forget, mis-set, or merge into the
  other pass — that explicitness is the point. The engine keeps `--lens`
  as the **internal** switch the wrappers pass; **one invocation runs ONE
  lens** (no auto-both). A finished change runs `cmr-completeness` first
  (must pass), then `cmr-correctness`. `scripts/install-skills.sh` symlinks
  all three into `~/.claude/skills/`. SKILL.md Step 1 "Prompt templates"
  names which prompt per gate; the Step-0 completeness blocks collapse to a
  pointer at the prompt (de-dup).
- **Tests**: `tests/test_prompts.py` (both lens prompts exist as distinct
  dispatchable artifacts; completeness prompt carries both verdict scales +
  chase-reference / exercise / green-≠-evidence rules + its verdict line) +
  `tests/test_gate_skills.py` (both gate skills exist, name themselves,
  delegate to the engine with the right lens, stay thin, and the install
  script links all three). No backend / engine change — the engine
  machinery is shared, never duplicated.

40 tests pass; selftest green.

## [0.3.13.0] - 2026-06-24

### Fixed — codex hang detection is IDLE-based, not total wall-clock (`codex-review.sh`)
The backend ran `timeout <N>s codex exec` — a **total wall-clock cap** that
killed codex after N seconds even while it was still streaming tokens. The
wiki canonical (§额外硬规则 #4) is an **idle / silence** rule: a hang =
> 8min with **no new stdout/stderr** → kill; a codex still producing output
runs as long as it needs (deep reasoning / large diffs go silent for
minutes before the first token, then stream). The total-time cap was a
long-standing drift — and the earlier 600 → 1200 bump (v0.3.10.1) tuned the
wrong axis (a value on a mechanism that was itself wrong).

Replaced the `timeout(1)` total cap with a pure-bash **idle watchdog**:
codex runs in the background, its combined output file is watched for
growth, and it is scoped-killed only after `CMR_CODEX_TIMEOUT` seconds of
**no new output** (the var is now an **idle/silence** timeout, default
**480 = 8min**; `CMR_CODEX_IDLE_POLL` sets the poll interval). A streaming
codex is never killed for total runtime. Regression tests:
`test_streaming_codex_survives_when_total_time_exceeds_idle_window` (the
old total cap killed it),
`test_silent_codex_killed_after_idle_window`. SKILL.md doc corrected (it
still described a `600s` total cap).

30 tests pass; selftest green.

## [0.3.12.0] - 2026-06-23

### Changed — wiki sync: Step-5 exercise/grounding + fix-loop defer + anti-pattern #11
Two cmr-relevant wiki commits (2026-06-23, post-0.3.11.0):

- **e3999be** — the cmr page gains **anti-pattern #11** and Step 5 gains
  two rules against a *hollowed-out* gate:
  - **Exercise behavioral keys, don't static-read them** — a gate /
    fix-loop / guard / state-machine must be RUN with an injected defect;
    "looks right / matches spec / tests pass" can't tell a real gate from
    a hollow one (both return `converged`). The author's green tests are
    not evidence. 2-3 reviewers sharing one "read the diff" prompt all
    miss behavioral defects (input-bias). → SKILL.md **anti-pattern #15**
    + the Step-5 completeness lens.
  - **Chase the reference chain** — ground against the authority the spec
    itself names ("faithful to X" → pull X in as the checklist), not just
    the local plan-file. → SKILL.md Step-5 lens. Evidence: #330.
- **e6615db** — fix-loop defer policy: cheap / low-risk `medium`/`low`
  findings are **fixed by default** (+ the self-check二连), NOT banked as
  backlog debt; **defer only** out-of-scope / needs-design / high-risk-own-
  PR, never "we hit round N"; the drift triple still governs the stop. →
  prompts/cmr-fixer.md.

Prose / prompt sync only — no code change (28 tests pass; selftest green).

## [0.3.11.0] - 2026-06-22

### Changed — wiki sync: spine 5a/5b → Step 5/6 + per-slice always nested
Sync to two `cross-model-review.md` commits (2026-06-19) that landed
after the 0.3.8.0 sync:

- **a70f97b** — the ship-pre spine sub-steps split: `5a/5b` are now
  independent **Step 5 (completeness) / Step 6 (correctness)** (ship →
  spine Step 7, pr-review → Step 8). SKILL.md relabels every `5a/5b`, and
  the `spine step 5 ship-pre` references (description / scenario list /
  README), to `step 5–6` / `completeness/correctness (spine Step 5/6)` —
  spelled out, NOT bare "Step 5/6", to avoid colliding with the skill's
  own Step-N headers. Also adds the **«严禁合一次 cmr 闸»** discipline: the
  two ship-pre gates (completeness Step 5 → correctness Step 6) are
  separate sequential passes with different lenses; merging them into one
  prompt makes both shallow (wiki gate-lens-heterogeneity).
- **be396aa** — every slice is now implemented by a clean-context
  subagent (the old main-session-self-runs-small-slices exception is
  removed), so **per-slice review always runs nested → every leg is a
  Bash CLI**; the native codex-subagent path is **ship-pre only**.
  SKILL.md Step 1 (谁跑 cmr) + the codex-leg note updated.
- **dec9de6** (2026-06-22) — the Step-5 completeness audit gains a
  PRD-compliance dimension. The transferable principle is folded into the
  skill's completeness lens: **green tests / a pipeline that runs
  end-to-end are NOT completeness evidence**; audit constraints /
  delegations / exemptions, not just features; for any "X exempt because Y
  backstops it", verify Y is wired (else `UNVERIFIED-GAP`, not done). The
  full CONFORMS/VIOLATES/UNVERIFIED-GAP rubric stays spine-side
  ([[tdd-autonomous-dev]] §Step 5 / new [[verification-scope-vacuum]]),
  which the cmr skill references but does not transcribe.

Prose / terminology sync only — no code or test change (28 tests still
pass; selftest green).

## [0.3.10.1] - 2026-06-22

### Changed — codex review timeout default 600 → 1200s (`codex-review.sh`)
`CMR_CODEX_TIMEOUT` defaults to **1200s** (20 min), up from 600s. Deep
`xhigh` reviews of large cumulative diffs were brushing the 10-min wall
and getting killed (a false "本轮缺 codex"); 20 min gives headroom. Still
caller-overridable via the env var.

## [0.3.10.0] - 2026-06-21

Emit codex's final message only, not its ~1.5MB stdout — a ~99% size cut
for the orchestrator's merge step, with no parser.

### Changed — codex review via `-o`/`--output-last-message` (`codex-review.sh`)
`codex exec`'s stdout is the full prompt echo + reasoning trace —
**~1.5MB** (≈375K tokens) on a real diff, almost all of it noise the
orchestrator already has; feeding that to the merge step wastes context
(or gets truncated from the tail, which is the review). codex's native
**`-o <file>`** writes ONLY its final message (findings + verification +
`CMR-VERDICT`) — a few KB, complete. The backend now adds `-o "$LASTMSG"`
to `CODEX_CMD` and emits that file's contents on success (measured: a
small diff went 23KB stdout → 0.7KB last-message; a real run is ~1.5MB →
a few KB). stdout is still captured (2>&1) but only for outage
diagnostics.

This is **not** a return of the parser we removed in 0.3.9.0: we use the
CLI's own last-message output, never tail-parse or marker-scan (codex
echoes the prompt that *defines* any marker, so a self-written scanner
false-positives on the echo). Extraction is not a format gate — degrade
still fires only on a true outage: timeout/kill, codex exiting non-zero,
or **an empty `-o` file** (rc=0 but no final message). New regression
tests: `test_emits_last_message_not_stdout_echo`,
`test_degrades_when_final_message_empty`; `--selftest` pins the new
10-token array (`-o <file>` before stdin `-`). The Gemini leg (`agy
--print`, 0–7KB, no echo) needs no trimming and is unchanged.

### Changed — wiki sync (source of truth)
`cross-model-review.md` §额外硬规则 #7 gains a clause: trim the
echo/trace via the CLI's native output (codex `-o`), never a self-written
parser, and extraction-miss is not a degrade.

## [0.3.9.0] - 2026-06-21

Reviewers now return a **prose** review and the orchestrator reads it —
removing a skill-only divergence from the wiki that repeatedly dropped the
strongest reviewer (codex) over output format.

### Fixed — prose review no longer degraded as a phantom outage (backends)
The backends piped each reviewer's stdout through a `lib/extract_json.py`
sentinel-JSON parser and degraded to "本轮缺 X" whenever it found no
`===CMR-FINDINGS-BEGIN===`-wrapped JSON. But codex's (and agy's) strongest
review is **prose** — so a real, deep review with no JSON wrapper was
treated as a missing vendor, **indistinguishable from an actual outage**.
The wiki never asked for the sentinel (`§.result 是 review 文本`:
reviewers return review text, the agent reads it); the parser was the
skill's own over-formalization. Now `backends/codex-review.sh` /
`gemini.sh` **pass a successful review through verbatim** and degrade
**only on a true outage** — empty output, the CLI exiting non-zero
(auth/quota/crash), timeout, or agy auth-race after its retries are
exhausted. Regression tests pin
prose-passthrough on both legs (`test_prose_review_passes_through_not_degraded`).

### Removed — `lib/extract_json.py` + `tests/test_extract_json.py`
The sentinel-JSON parser and its tests are deleted (no callers remain) —
the same "no deterministic engine, this is agent judgment" stance that
removed `merge.py` / `drift.py` in 0.2.0.0, one layer down. `python3` is
now a **test-only** dependency; the backends call no Python at runtime.

### Changed — reviewer prompt is prose-first (`prompts/cmr-reviewer.md`)
The Output section drops the mandatory sentinel-JSON schema. Reviewers
write grounded **prose** (severity / location / quoted offending line /
verification / fix) and end with a single `CMR-VERDICT: converged|findings`
line — the only fixed-format ask, so the orchestrator can tell approve
from findings and a real review from a missing vendor at a glance.

### Changed — wiki sync (source of truth)
`cross-model-review.md` §额外硬规则 gains rule #7: reviewer output is
prose the agent reads; never gate on JSON format; degrade only on a true
outage. Codifies the lesson so a future skill re-sync can't drift back
into a sentinel-JSON straitjacket. SKILL.md / README.md / CLAUDE.md /
TESTING.md updated to match (findings channel, merge step, ships list,
dependencies, test layers).

## [0.3.8.0] - 2026-06-18

Full sync to the wiki's 2026-06-14→06-18 revision (16 commits) — a major
restructure of who runs cmr and at what depth. Several of these supersede
the earlier-this-PR reasoning-effort sync (always-`xhigh`, `--effort
max`), so they never ship.

### Changed — squad depends on the trigger point (wiki §谁跑 cmr)
**Claude is concentrated to ship-pre** (`claude -p` credit is too tight
for the high-frequency per-slice gate): **per-slice = `N codex + agy`
(2-vendor, NO Claude)**, run by the slice's own implementing subagent
(both Bash, no nested-Agent); **ship-pre = `N codex + Claude + agy`
(1+1+1)**, main session orchestrates with Claude via the `Agent`
subagent. SKILL.md Step 1/2/5, the two-phase rule (Step 2 + anti-pattern
#6) and the termination table now distinguish the two.

### Changed — codex reasoning effort is scenario-dependent (`codex-review.sh`, code)
Not always `xhigh`. **ship-pre 5a/5b = `xhigh`; per-slice = `high`**
(downshifted to save credit, but never below `high`). `codex-review.sh`
takes `CMR_CODEX_EFFORT` (validated `high|xhigh`, default `xhigh`); the
`--selftest` matches the live effort. Header/callout updated.

### Changed — N table thresholds ×2.5–3 + effective lines (wiki §N 取值表)
`<500 / 500–1500 / 1500+` (was 200/500). N is now by **effective (core-
logic) lines** — exclude test/spec/fixture/lock/generated/`*.md`/docs
noise before computing N; dense core → bump a tier with a one-line
justification. (Both hypothesis, not yet validated; roll back if findings
slip.)

### Changed — `claude -p --effort max` RETRACTED (wiki, code-doc)
The main=Codex Claude review call drops `--effort max` (billing on
isolated/capped `claude -p` credit burns 5× tokens too fast — the 6/15
policy is paused but may restart). It now pins `--model claude-opus-4-8`
(current strongest; revert to `claude-fable-5` when Fable returns) and
keeps **no `--tools ""`** (reviewer needs Read/Grep/Glob for grounded
review; tool-kill is auth-smoke only).

### Changed — misc
- Fix-loop **mandatory self-check 二连** after every fix (same-type +
  fix-introduced-bug, with a visible "自查二连 done"); used to be a
  flowchart arrow that got skipped (wiki §修复).
- `/diagnose` → **`/diagnosing-bugs`** (skill renamed) everywhere in
  SKILL.md + `prompts/cmr-fixer.md`.
- **Hang judgment 3min → 8min** (deep reasoning thinks silently past
  3min; still under agy's 15m print-timeout).
- main=Codex codex leg note: runs as a Codex **native subagent** (not
  `codex exec`) except nested → `codex exec` (wiki §主=Codex …,
  hypothesis; this skill executes main=Claude, so its codex leg stays
  `codex exec`).

### Note — divergence kept (auth-race warm+retry)
The wiki (re)affirms agy's auth-race was fixed in 1.0.1 and 1.0.8 needs
no warm+retry; the skill **deliberately keeps** the warm+retry recipe in
`gemini.sh` because the OAuth page still pops intermittently on 1.0.8 in
practice. Flagged in SKILL.md; the wiki note is the stale side.

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

### Added — agy model-degradation ladder (`backends/gemini.sh`, code)
The agy/Gemini leg now has its own model fallback. agy's Gemini quota is
a small **consumer Code Assist** bucket (separate from any paid Gemini
plan) that exhausts; when the preferred **Gemini 3.5 Flash** rung
quota-429s, `gemini.sh` steps the leg DOWN to **`Claude Sonnet 4.6
(Thinking)` via agy** — a SEPARATE quota bucket (verified live: Gemini
429 while agy-Claude still answered) — so a third independent read
survives instead of the leg dropping. Sonnet (not Opus 4.6) is chosen
deliberately: it is a *different* model from the squad's Claude-Agent leg
(Opus 4.8), so it is a distinct voice rather than a near-duplicate. Only
when EVERY rung is quota-exhausted does the leg degrade (`本轮缺 gemini`).
When a fallback rung runs, the round has **no Google voice** and
`gemini.sh` flags it on stderr (the 3rd voice is then agy-served Claude).
`AGY_MODEL` env pins one explicit model (manual / tests). 3 regression
tests (step-down → Sonnet; all-rungs → degrade; happy-path no step-down;
the doubled-Resets dedup is its own test in the Fixed entry below). This
supersedes an earlier mislabeled
"Fable-death stopgap" working-tree experiment — same mechanism, but
correctly framed (it is a Gemini-quota fallback, not a Fable thing) and
using the right model. **The wiki §降级链 should bless this rung** (the
anti-#9 "don't escalate Claude when Gemini's down" rule was quota-driven,
and agy-Claude uses a different bucket, so that rationale doesn't apply).

### Fixed — agy workspace was the skill's own (hidden) dir, not the reviewed repo (`gemini.sh`, code)
The real root cause behind the perpetual "WITHOUT repo context" warning.
`gemini.sh` cd'd agy into `PROTO_ROOT` (the skill's own dir) before
running it — and the registered skill lives under `~/.claude/skills/...`
(hidden), so agy refused the (hidden) workspace and ran **diff-only on
every registered-skill invocation**, regardless of where the user's
project was. The v0.3.4.0 change only *warned* (and mislabeled the
skill's dir as the "workspace root"). Now agy runs from **`REVIEW_ROOT`**
(the reviewed repo = the invocation cwd's `git rev-parse --show-toplevel`,
captured before any cd); `PROTO_ROOT` is kept only for `lib/`. The
hidden-path warning now keys on `REVIEW_ROOT`, so it fires only when the
*reviewed repo itself* is under a dot-path — not on every run. This
restores agy grep-grounding (matters for the 5a completeness audit).
Verified live (non-hidden cwd → no warning + agy gets the repo; hidden
cwd → warning). The two hidden-path tests now drive REVIEW_ROOT via cwd.

### Fixed — doubled "Resets in …" in the quota flag (`gemini.sh`, code)
Live-surfaced: real agy writes the fatal error TWICE on one log line, and
`agy_fatal_reason`'s `grep -m1 -o` (caps matching *lines*, not
matches-per-line) emitted both → the degrade flag carried a doubled,
newline-split `Resets in …`. Now takes only the first via
`${resets%%<newline>*}` (no extra pipe). Regression test added.

### Note — reverse drift (skill-ahead-of-wiki items owed back)
The skill's hidden-path workspace warning is now in the wiki too (wiki
`51ad2b0`). Two skill-ahead items remain, both owed back to the wiki:
(1) the client-<v2.1.170 Claude degradation row; (2) **the agy model
ladder (Gemini 3.5 Flash → Sonnet 4.6 on quota)** — the wiki §降级链 does
not yet bless the Sonnet rung (its anti-#9 "don't escalate Claude when
Gemini's down" rule is quota-driven and doesn't apply, since agy-Claude
uses a separate bucket). Until the wiki is updated these are intentional
skill-ahead exceptions, flagged here.

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
