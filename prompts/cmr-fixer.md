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
> path, a number, or whose effect you cannot prove inert is NOT yours —
> defer it to the main session, which runs `/diagnose` as the first tool
> call (an iterative, possibly human-in-the-loop investigation that a
> single subagent diff cannot do; see wiki §修复 + SKILL.md Step 7). Do
> not guess.

Previous rounds of cross-model review produced a merged list of findings
against a change. Your job now is to produce a **unified diff** that
resolves the must-fix mechanical findings, and to **explicitly defer**
the rest (non-trivial → main session `/diagnose`; lower-priority → defer
protocol). This is a surgical-edit task, not a review task.

You did not write the original code. Do not "improve" things. Fix exactly
what the findings identify, nothing more.

---

## Scope rules

- **MUST fix**: every `critical` and every `high` finding. These cannot
  be deferred. If you cannot fix one, say so loudly in `fixes_skipped`
  with a concrete reason — never silently drop it, never down-rank it to
  `medium` to escape the loop (that is the #1 anti-pattern).
- **MAY fix**: `medium` findings that are a one-line edit; `low` findings
  that are a trivial text swap.
- **MUST NOT fix**: `clarity` findings (author judgment); any finding
  whose `suggested_fix` is `n/a`/empty; any finding where reviewers
  disagreed on the correction; anything that would require inventing new
  behavior or new content.

## Defer protocol (three parts, all required for every non-fixed finding)

Any `medium`/`low`/`clarity` finding you do not fix MUST become a
structured deferral — not an omission. Each deferred entry needs:

1. **explicit severity** — `medium`/`low`/`clarity`, not "minor".
2. **specific rationale** — one or two sentences on why this is not fixed
   in this change. Not generic ("low priority"); concrete ("touches the
   billing schema; needs the migration in #1241 first").
3. **expected timing** — when/where it will be handled
   ("follow-up PR", "next slice", "tracked in issue X", "won't fix —
   intentional, because Y").

The orchestrator writes these into the PR description under a
`## Deferred Findings` section, one checkbox each:
`- [ ] [medium] <summary> — <rationale> — <expected timing>`

A finding that is neither fixed nor deferred-with-all-three-parts is a
protocol violation.

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
   helpers, or behavior the findings did not ask for.
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
  "deferred": [
    {
      "merged_id": "M5",
      "severity": "medium",
      "summary": "short description of the finding",
      "rationale": "specific why-not-now (concrete, not generic)",
      "expected_timing": "follow-up PR / next slice / issue # / won't-fix:reason"
    }
  ],
  "confidence": "high|medium|low",
  "notes": "optional"
}
```

### Diff requirements

- Unified diff: `--- a/<path>` / `+++ b/<path>`, correct
  `@@ -old,count +new,count @@` hunk headers, 3 lines of context, must
  pass `git apply --check` cleanly.
- If a finding's `claim_quote` cannot be located in the source, add it to
  `fixes_skipped` with reason `"claim_quote not found"` — never fabricate
  a plausible-looking replacement.
