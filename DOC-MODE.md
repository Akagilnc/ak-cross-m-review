# Doc mode discipline ②–⑤ (design-text reviews)

> **⚠ RECORDED RULE ②–⑤ — upstreamed to the wiki 2026-07-06 (user
> decision same day; vault `b5495e8` / `da04ff5` / `e06bcfe`).** Do
> NOT drop this section on a wiki re-sync (a re-sync from a stale wiki
> checkout would erase it). The
> round-gate value **10** restores cmr's original founding setting (it
> had been silently forgotten by later versions).

**Why doc mode needs its own defense (evidence: #440).** A review of a
DESIGN TEXT is structurally **additive** — every finding suggests adding
text, every fix grows the reviewable surface. #440 ran 34 rounds: of 121
fixes, 7% fixed the original design, **58% fixed the review's own
earlier fixes**, 23% were mechanisms the review itself invented; the
text bloated 2.4×; at round 3, 3/4 legs had already judged `complete`
and the loop still ran ~30 more full rounds. **SKILL.md Step 6's drift
triple never fired once in 34 rounds** — quantity drift watches "findings
count not decreasing", and a runaway doc review *resolves* findings every
round (count keeps falling) while the text grows and fixes fix fixes.
The triple is structurally blind to additive-text runaway, so doc mode
adds the defenses in this file. 标 vs 本: ① in `SKILL.md`, ③ here, and
the ledger are the **root** fixes (they stop the runaway from being
generated); the bloat line and the round gate are **backstops** for when
the roots fail.

### ② Fix-classification ledger + stop signals

- **(a) Ledger — the measuring instrument, lands first.** Every round
  intro MUST carry the previous round's fix classification:
  **original-defect / fix-fix / invention** (原始缺陷 / fix修fix / 加戏).
  Without the ledger none of the signals below is measurable.
- **(b) Bloat line = audit trigger, NOT a death line.** Reviewed text
  grows past **1.5×** its round-1 size → audit the ledger. Growth driven
  by original-defect fixes → legitimate: note it in the round report and
  continue (a genuinely complex design may lawfully grow). Growth driven
  by fix-fix / invention → STOP, escalate to the user with the ledger.
- **(c) Early stop via a FULL confirmation round (no #14 exception).**
  A round where the **majority of legs judge `complete`** AND the ledger —
  **aggregating ALL legs' findings, including any leg dissenting from the
  majority-complete vote** — shows **zero blocking (P0/P1/P2/P3) findings
  regardless of classification** (any classification — original-defect,
  fix-fix, or invention all count toward blocking; the
  original-defect/fix-fix/invention split is for ②(b)'s
  bloat-line/ledger-audit trigger only, never for filtering the
  clear/convergence gate) (only P4 exempt; P4 clarity
  reported-but-Deferred, doesn't block the confirmation round) → the next
  round is a **confirmation round that is still a FULL re-review**
  (SKILL.md anti-pattern #14 stays fully intact — the spot-check variant
  was considered and rejected: one full round costs nothing against the
  ~30 wasted ones it prevents, and it keeps the fresh-full-read guarantee).
  Confirmation round again majority-complete **AND the ledger (again
  spanning ALL legs, dissenters included) again showing zero blocking
  (P0/P1/P2/P3) findings regardless of classification** (any
  classification — original-defect, fix-fix, or invention all count toward
  blocking; the split is ②(b)'s bloat-line/ledger-audit trigger only, never
  the clear/convergence gate) (only P4 exempt; P4 clarity
  reported-but-Deferred, doesn't block the confirmation round) →
  **converged, stop** (a confirmation round that itself makes any edit is
  not terminal — see SKILL.md Step 7's carve-out; its edit is new diff
  needing its own full re-review). Because the zero-blocking check spans every leg AND
  counts blocking findings of every classification, a single dissenting
  leg's blocking finding (original-defect, fix-fix, or invention — all
  count) keeps the ledger non-zero → NOT converged **regardless of the
  majority-complete vote**:
  fix it and the loop continues (the early-stop arm must re-qualify from
  scratch — bare majority-complete never converges on its own, or the
  dissenting leg's real finding gets swallowed).
- **(d) Round gate at 10 — an escalation checkpoint, NOT a hard cap.**
  Doc mode reaching **round 10** without convergence → stop dispatching
  and **escalate to the user with the ledger + current state**; the user
  rules "genuinely complex — continue" (the loop resumes, next window)
  or "runaway — close". Never a silent stop, never auto-terminate. A
  #440-style ledger (58% fix-fix) indicts itself; a genuinely complex
  design is not framed by the number. Code/correctness mode keeps the
  no-cap rule (`3 rounds is not a hard cap`, SKILL.md Step 6) unchanged —
  there the drift triple CAN see runaway; here it demonstrably cannot.

### ③ Anti-minutes-ification (fix output discipline)

A design-text fix **changes the conclusion** — it does not append
per-round argumentation to the doc/issue body. Argumentation and history
go to comments or the review ledger. Body length defaults to
**decrease-only**; an increase requires a stated justification in the
round report. (#440's bloat engine was exactly per-fix mechanism prose
appended to the body — every append enlarged the attackable surface.)

### ④ Dead-leg standing degrade

A leg returning empty / 429 / an error pattern is DEGRADED for the round
(SKILL.md Step 3 flag + out of the concur denominator — already the
rule). Doc mode adds: **2 consecutive dead rounds → stop re-dispatching
that leg**; mark **`standing-DEGRADED`** in every subsequent round report
(never counted as a zero-finding approve); re-probe it once at the ②(d)
escalation checkpoint — recovered → rejoin. (Evidence: #440's gemini leg
429'd empty for six late rounds and was re-dispatched and awaited every
single time.)

### ⑤ Fix self-check becomes 三连

Doc mode extends SKILL.md Step 7's mandatory self-check 二连 with a third
check before commit: **does the fix's mechanism itself actually hold,
and does it introduce no new contradiction with sibling issues / other
fixes?** (#440 round 33: 3 of 4 findings were bugs in previous rounds'
fixes — the cheapest whole-round saver in the set.)
