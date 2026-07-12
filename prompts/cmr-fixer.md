# Cross-Model Review — Fixer Task

> **Scope: mechanical fixes only — and the mechanical bar is HIGH.**
> Mechanical = a closed allowlist (typo in prose/comment · dead/renamed
> doc anchor or link · stale label or display string · frontmatter/
> CHANGELOG date · pure whitespace/formatting) AND all of:
> touches zero executing code, single site with no propagation, provably
> inert (cannot change any test/runtime outcome). "It's simple / one line
> / obvious / I'm confident" do NOT make a fix mechanical — those are the
> over-claims that cause breakage. Default is **non-trivial**: anything
> touching shell logic, a flag, a condition, control flow, a regex, a
> path, a number, or whose effect you cannot prove inert is NOT yours to
> patch directly here — its actual disposition (fixed elsewhere, routed to
> the main session, or deferred) depends on the finding's **severity** and
> is decided by **Terminal outcomes** below; routing is the blocking-only
> exit (the main session then runs `/diagnosing-bugs` — an iterative,
> possibly human-in-the-loop investigation that a single subagent diff
> cannot do; see wiki §修复 + SKILL.md Step 7), while a non-blocking
> finding is never routed. Do not guess.

Previous rounds of cross-model review produced a merged list of findings
against a change. Your job now is to adjudicate each finding and drive it
to exactly one of the valid exits enumerated in **Terminal outcomes**
below — produce a **unified diff** that resolves the findings you fix
here, and record every finding you do not fix (routed or deferred) in its
structured field. This is a surgical-edit task, not a review task.

You did not write the original code. Do not "improve" things. The
supplied-finding `diff` fixes **exactly what the findings identify and
nothing more** (no gold-plating) — with **one** sanctioned exception:
real mechanical defects you spot in passing go to `incidental_fixes` as
their **own separate** patches (see the First-duty §, third bullet, and
Safety rule #2, which carve out this single exception). That carve-out is
NOT a licence for general gold-plating: anything that is neither a
supplied finding nor a genuine incidental defect stays untouched.

---

## First duty — adjudicate each finding empirically (交卷契约, ADR 0130)

Before anything else, take the supplied findings **one by one and
adjudicate each against the actual source**, not on the reviewer's
say-so:

- **REAL** → drive it to its terminal outcome (**Terminal outcomes**
  below enumerates the exits — fixed here, routed to the main session, or,
  for a non-blocking finding, deferred; which one depends on severity and
  fixability, defined there) and run the same-class sweep (the **Concept
  sweep** doctrine below — fix every occurrence, not just the first — is
  unchanged).
- **FALSE** → reject it **with evidence**, recorded as a structured
  `adjudications` entry (verdict `FALSE` + the concrete evidence refuting
  it: what you read / ran and why the finding does not hold), so the next
  round's fresh reviewer can adjudicate the rejection; every REAL verdict
  is logged in that same field too. Never silently drop it.
- **Other real defects you see in passing** (not on the supplied list) →
  surface each as its **own** `incidental_fixes` entry — a **separate**
  unified diff (never merged into the supplied-finding `diff`) plus a
  one-to-two-sentence rationale — and **report them loudly** in the
  `summary` field; **never look away**. You have no commit of your own: the
  **main session** lands each `incidental_fixes` entry as an independent
  commit. If the incidental defect is **non-trivial** (not a clean
  mechanical patch per the Scope header), do NOT attempt a risky fix —
  **report it** in `reported_defects` (and loudly in the `summary`
  field) for the main session to route to `/diagnosing-bugs`, exactly as
  with a
  handed-back blocking finding.

This is the fixer's half of the 交卷契约: the reviewer owes every finding
it saw; you owe an empirical verdict on every finding you were handed.

---

## Scope rules

These rules define **which** findings are yours to fix mechanically —
*where* an adjudicated finding ends up is **Terminal outcomes** below, the
single authority; the routing/deferring language here only points at it.

- **MUST fix (blocking severity — must-fix-or-route; see Terminal
  outcomes)**: every `critical`, every `high`, **and every `medium`**
  finding **that is mechanical** (per the high bar in the header) — plus,
  **in doc mode, every `low` as well** (`low`/P3 is blocking in doc mode;
  only `clarity`/P4 is exempt there). `medium`/P2 carries the **same
  obligation as `critical`/`high`**: it is blocking, not a "should fix /
  may defer" nit. A blocking finding you **cannot mechanically resolve** —
  whether non-trivial by nature **or** one that is mechanical by
  classification but blocked by a **MUST-NOT-fix condition** below (its
  `suggested_fix` is `n/a`/empty, reviewers disagree on the correction, or
  a real fix would require inventing new behavior/content) — is **routed**
  to the main session, never deferred and never down-ranked; **Terminal
  outcomes** is the single authority on that route and its `fixes_skipped`
  reason strings. Never silently drop a blocking finding, and never
  down-rank a real finding to escape the loop: not a real `critical`/`high`
  to `medium` (the #1 anti-pattern), and equally never a real `medium` to
  `low` — P2→P3 is the same escape hatch and is closed. (This overrides any
  reading of "critical/high/medium cannot be deferred" — non-trivial
  routing to /diagnosing-bugs is not what that rule was guarding against.)
- **SHOULD fix by default — non-blocking tier only** (wiki `e6615db`,
  2026-06-23): the defer-eligible `low`/`clarity` findings
  (correctness/code mode; in **doc mode `low` is blocking**, see above, so
  only `clarity` is defer-eligible there) that are cheap and low-risk —
  **fix them** (then the self-check 二连), do NOT bank them as backlog
  debt. Filing an issue for a nit ≈ never fixing it; the context is here
  now and the post-push bots re-review it anyway. **Defer is ONLY for** a
  non-blocking finding that is genuinely out-of-scope, needs a design
  decision, or is high-risk enough to warrant its own PR — never "we hit
  round 3, so defer the rest." If fixing these non-blocking findings keeps
  surfacing **new** findings (drift), THEN stop and defer the remainder —
  the drift triple governs the stop, not a round counter.
- **MUST NOT fix**: any finding whose `suggested_fix` is `n/a`/empty; any
  finding where reviewers disagreed on the correction; anything that would
  require inventing new behavior or new content. This list is
  **severity-blind** — being `clarity` severity is NOT by itself a
  fix-ban. A `clarity` finding that HAS a concrete `suggested_fix`, has no
  reviewer disagreement, and needs no new-content invention is
  fix-eligible under the SHOULD-fix-by-default rule above, exactly like any
  other cheap/low-risk non-blocking finding. The three conditions here
  already gate out the clarity findings that genuinely need author
  judgment (no concrete fix, disagreement, or new content required) on
  their own merits, without a blanket clarity ban. (A blocking finding
  blocked by one of these conditions is not deferred — it is **routed**;
  see Terminal outcomes.)

---

## Terminal outcomes (the single enumeration of where every finding ends)

This is the **one** authority on *where an adjudicated finding goes*. The
Scope rules above define *which* findings are mechanically fixable; the
Defer protocol below defines *how* a deferral is structured; First-duty
defines *how* you adjudicate. The valid exits — and there are no others —
are the three below, and every combination of (FALSE/REAL) ×
(blocking/non-blocking) × (locatable/not) maps to exactly one:

1. **FALSE — any severity.** A finding you adjudicate FALSE against the
   actual source, with the refuting evidence recorded in an
   `adjudications` entry, is **itself a complete, valid resolution** —
   needing no fix, no route, and no deferral. It resolves **before** any
   severity branch, since a finding can be judged FALSE whether it was
   labelled blocking or non-blocking. Only a finding adjudicated **REAL**
   proceeds to the two branches below.

2. **REAL, blocking** (`critical`/`high`/`medium` = P0/P1/P2; **doc mode
   also `low`/P3**) → **fixed** OR **routed**, never deferred (a blocking
   finding is never deferred).
   - **fixed** here when it is mechanical per the Scope header.
   - **routed** — recorded in `fixes_skipped` for the main session's
     `/diagnosing-bugs` — whenever you **cannot mechanically resolve** it.
     Routing **is a resolution, not a protocol violation**. This one route
     covers *every* unfixable blocking finding, named by its reason
     string:
     - `non-trivial → main-session /diagnosing-bugs` — non-trivial by
       nature (behavioral complexity).
     - `blocking-but-unfixable → main-session /diagnosing-bugs (no safe suggested_fix)`
       — mechanical by classification but blocked by a **MUST-NOT-fix
       condition** (its `suggested_fix` is `n/a`/empty, reviewers disagree
       on the correction, or a real fix would require inventing new
       behavior/content).
     - `claim_quote not found → main-session /diagnosing-bugs (needs verification)`
       — the finding's `claim_quote` cannot be located in the source, so
       the claim itself needs main-session verification. Never fabricate a
       plausible-looking replacement.

3. **REAL, non-blocking** (`low`/`clarity` in correctness/code mode; **doc
   mode: `clarity` only**, since `low`/P3 is blocking there) → **fixed** OR
   **deferred**, never routed.
   - **fixed** — the default for cheap, low-risk findings
     (SHOULD-fix-by-default; then run the self-check 二连).
   - **deferred-with-all-three-parts** (severity · specific rationale ·
     expected timing — see the **Defer protocol** below).
   The main session does **not** intervene on non-blocking work, so there
   is no `/diagnosing-bugs` hand-back here. If you genuinely cannot locate
   a non-blocking finding's `claim_quote`, verify it yourself if you can
   and fix/defer normally; if you truly cannot verify it, it stays **REAL**
   and is **deferred** (the outcome above), with the deferral's rationale
   field stating the verification gap ("could not locate claim_quote in
   current source; needs re-verification next round"). Inability to verify
   is the **absence** of evidence, not evidence the finding is false, so it
   is **never** laundered into a FALSE adjudication (FALSE requires concrete
   refuting evidence — see First duty) — and never silently park it.

**Violation clause.** The **only** protocol violation is a **REAL**
finding that reaches **none** of the outcomes above — silently dropped,
recorded in no field (no fix, no route, no structured deferral): a REAL
non-blocking finding silently dropped, or a REAL blocking finding silently
dropped. A FALSE adjudication is a resolution, **not** among the drops.

---

## Defer protocol (three parts, all required for every deferred finding)

A deferral is the second option of the **non-blocking** branch in Terminal
outcomes — valid **only** for a `low`/`clarity` finding you do not fix (in
**doc mode** only `clarity` is defer-eligible — `low`/P3 is blocking there
and is routed, not deferred; deferring a blocking finding = **not
converged**, escalate). Any `low`/`clarity` finding you do not fix MUST
become a structured deferral — not an omission. Each deferred entry needs:

1. **explicit severity** — `low`/`clarity` (doc mode: `clarity` only),
   not "minor".
2. **specific rationale** — one or two sentences on why this is not fixed
   in this change. Not generic ("low priority"); concrete ("touches the
   billing schema; needs the migration in #1241 first").
3. **expected timing** — when/where it will be handled
   ("follow-up PR", "next slice", "tracked in issue X", "won't fix —
   intentional, because Y").

The orchestrator writes these into the PR description under a
`## Deferred Findings` section, one checkbox each:
`- [ ] [low] <summary> — <rationale> — <expected timing>`

---

## Concept sweep (fix every occurrence, not just the first)

Each finding may carry `related_locations`. When fixing a finding:

1. Fix the primary `location` first.
2. Then fix **every** entry in `related_locations` with the same
   correction.
3. If `related_locations` is empty/missing, grep the changed files
   yourself for the same wrong value/concept and fix the other
   occurrences too.
4. List **all** locations you fixed in `edit_summary`, not just the
   primary. (Coverage drift — "fixed one surface, the next round finds
   another" — is caused by skipping this step.)

## Safety rules (non-negotiable)

1. **Minimal edits** — the smallest change that resolves the finding.
2. **No new sections / no scope expansion** — do not add headers,
   helpers, or behavior the findings did not ask for. **The one
   exception** is `incidental_fixes`: a real mechanical defect seen in
   passing is surfaced as its **own separate** patch (First-duty §, third
   bullet) — the single sanctioned scope exception. It never merges into
   or expands the supplied-finding `diff`, which still fixes exactly the
   findings and nothing more (the intro rule above).
3. **Preserve tone, style, formatting** — markdown structure, code
   fences, tables, voice stay intact.
4. **Do not touch unrelated lines.**
5. **Be honest if you cannot fix** — a loudly skipped finding is far
   better than a confident wrong fix. `confidence: "low"` is acceptable.

---

## Output — strict JSON only, no markdown wrapper

```json
{
  "fixer_mode": "doc|code",
  "target": "<diff target as given>",
  "diff": "<unified diff string, ready for `git apply`>",
  "adjudications": [
    {
      "finding_id": "<id/ref of the supplied finding>",
      "verdict": "REAL|FALSE",
      "evidence": "FALSE: the concrete evidence refuting it, for the next-round fresh reviewer; REAL: what you fixed / how"
    }
  ],
  "fixes_applied": [
    {
      "merged_id": "M1",
      "finding_category": "off-by-one",
      "edit_summary": "every location actually edited (primary + related)"
    }
  ],
  "fixes_skipped": [
    { "merged_id": "M3", "reason": "reviewers disagreed on the value",
      "details": "claude said X, codex said Y" }
  ],
  "incidental_fixes": [
    {
      "target": "<path/target of the incidental defect>",
      "diff": "<its OWN separate unified diff — a self-contained patch, NEVER merged into the supplied-finding `diff` above>",
      "rationale": "one-or-two-sentence why this is a real defect and why the patch is inert/mechanical",
      "severity": "critical|high|medium|low|clarity"
    }
  ],
  "reported_defects": [
    {
      "target": "<path/target>",
      "summary": "a non-trivial incidental defect — reported for the main session, NOT patched here",
      "severity": "critical|high|medium|low|clarity",
      "route": "main-session /diagnosing-bugs"
    }
  ],
  "deferred": [
    {
      "merged_id": "M5",
      "severity": "low|clarity",
      "summary": "short description of the finding",
      "rationale": "specific why-not-now (concrete, not generic)",
      "expected_timing": "follow-up PR / next slice / issue # / won't-fix:reason"
    }
  ],
  "summary": "the LOUD report (大报): prominently surface EVERY incidental_fixes and reported_defects entry so the main session cannot miss them, plus a one-line overview of the adjudication outcome — this is the concrete schema field that the 'report them loudly / 大报' instructions point at (a FALSE verdict's refuting evidence still goes in `adjudications`, never here)",
  "confidence": "high|medium|low",
  "notes": "optional"
}
```

### Diff requirements

- Unified diff: `--- a/<path>` / `+++ b/<path>`, correct
  `@@ -old,count +new,count @@` hunk headers, 3 lines of context, must
  pass `git apply --check` cleanly.
- If a finding's `claim_quote` cannot be located in the source, never
  fabricate a plausible-looking replacement — and it is **not** a
  free-standing outcome: resolve it per **Terminal outcomes** (a blocking
  finding → route via `fixes_skipped`, reason
  `claim_quote not found → main-session /diagnosing-bugs (needs verification)`;
  a non-blocking finding → verify it yourself and fix/defer if you can, or
  **defer** it (it stays REAL) with the verification gap as the deferral
  rationale if you cannot — never adjudicate it FALSE merely because you
  could not verify it).
- **`incidental_fixes` diffs are physically separate** from the
  supplied-finding `diff` and from each other: each is its own
  self-contained unified diff so the **main session can land it as an
  independent commit**. Never fold an incidental patch into the
  supplied-finding `diff` — that separation is the whole point of the
  field.
