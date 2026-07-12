"""P2/medium is BLOCKING — the defer tiers must align with severity-aware
convergence (0.3.18.1).

0.3.18.0 made P2 a blocking severity (a round is CLEAR only with no
P0/P1/P2; doc mode no P0/P1/P2/P3). But the fixer/defer protocol still
listed medium/P2 as deferrable ("SHOULD fix ... may defer"), so a fixer
could legitimately defer a P2 that still blocks convergence → the next
full round re-finds it → the loop never terminates. This pins the
corrected tiers: deferrable = the NON-blocking set (P3/P4 in
correctness/code mode, P4 only in doc mode); a blocking finding is
must-fix-or-route, NEVER deferred.

Caught by the codex outside-voice review of the submission-contract
branch; wiki tdd-autonomous-dev §切片内纪律 was synced by the main session
(P2 moved into the 必修/阻塞级 row with P0/P1, deferrable row = P3/P4 only).

Phrase pins (positive + negative counterpart) in the test_doc_mode.py
style, so a re-sync that reverts to "medium is deferrable" / "explicit
P2/P3/P4" fails here.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
FIXER = ROOT / "prompts" / "cmr-fixer.md"


def _norm(path):
    # prose files hard-wrap at ~72 cols; assertions must not break on a
    # line wrap landing inside the asserted phrase
    return " ".join(path.read_text(encoding="utf-8").split())


# --- SKILL.md defer protocol: deferrable = non-blocking tier only ---


def test_skill_defer_protocol_deferrable_is_non_blocking_tier():
    txt = _norm(SKILL)
    assert (
        "Deferral is ONLY for the **non-blocking tier** — **P3/P4** in "
        "correctness/code mode, **P4 only** in doc mode"
    ) in txt, (
        "the defer protocol must restrict deferral to the non-blocking "
        "tier (P3/P4 in code, P4 in doc) — P2 is no longer deferrable"
    )
    assert (
        "A **blocking** finding (P0/P1/P2; doc mode also P3) is NEVER "
        "deferred"
    ) in txt, (
        "a blocking finding must be declared never-deferred, "
        "must-fix-or-route"
    )
    assert "not converged" in txt and "escalate to the user" in txt, (
        "trying to defer a blocking finding must read as 'not converged' + "
        "escalate, not silent staging as converged"
    )


def test_skill_defer_protocol_drops_p2_deferrable_negative():
    txt = _norm(SKILL)
    assert "P2/P3/P4" not in txt, (
        "the old 'explicit P2/P3/P4' deferrable list must be gone — P2 is "
        "blocking now"
    )
    assert "[P2]" not in txt, (
        "the deferred-staging example must not use a [P2] tag — P2 is not "
        "a deferrable severity"
    )


# --- cmr-fixer.md: medium = blocking / must-fix-or-route ---


def test_fixer_medium_is_blocking_must_fix():
    txt = _norm(FIXER)
    assert "**and every `medium`** finding" in txt, (
        "medium must join critical/high in the MUST-fix (blocking) bullet"
    )
    assert (
        "`medium`/P2 carries the **same obligation as `critical`/`high`**"
    ) in txt, "medium must carry the same must-fix obligation as critical/high"
    assert "in doc mode, every `low` as well" in txt, (
        "doc mode also blocks low/P3 — the fixer must fix it, not defer it"
    )
    # the P2->P3 escape hatch is closed, mirroring the critical/high->medium ban
    assert (
        "never a real `medium` to `low` — P2→P3 is the same escape hatch "
        "and is closed"
    ) in txt, (
        "down-ranking a real medium to low to escape must be banned, "
        "mirroring the critical/high->medium ban"
    )


def test_fixer_deferrable_set_is_low_clarity_only():
    txt = _norm(FIXER)
    assert (
        "Any `low`/`clarity` finding you do not fix MUST become a structured "
        "deferral"
    ) in txt, (
        "the structured-deferral obligation must key off low/clarity, not "
        "the old medium/low/clarity set"
    )
    assert "doc mode: `clarity` only" in txt, (
        "doc mode's deferrable set is clarity only (low/P3 blocks there)"
    )


# --- cmr-fixer.md: clarity is NOT unconditionally fix-banned (0.3.18.16) ---
#
# The MUST-NOT-fix list used to carry a standalone "`clarity` findings
# (author judgment)" bullet — an unconditional severity-based ban that
# directly contradicted the SHOULD-fix-by-default bullet immediately above
# (which says cheap/low-risk non-blocking findings, clarity included per
# SKILL.md's "cheap/low-risk P3/P4 should still be FIXED", must be fixed
# now). Removed: the remaining three conditions (no concrete suggested_fix,
# reviewer disagreement, needs new content) already gate out the
# un-fixable clarity subset on their own merits, severity-blind.


def test_fixer_clarity_not_unconditionally_fix_banned():
    txt = _norm(FIXER)
    # positive: the MUST-NOT-fix list is declared severity-blind, and a
    # clarity finding with a concrete fix / no disagreement / no new content
    # is explicitly fix-eligible
    assert "This list is **severity-blind**" in txt, (
        "the MUST-NOT-fix list must be marked severity-blind — being "
        "clarity severity is not by itself a fix-ban"
    )
    assert (
        "A `clarity` finding that HAS a concrete `suggested_fix`, has no "
        "reviewer disagreement, and needs no new-content invention is "
        "fix-eligible under the SHOULD-fix-by-default rule above"
    ) in txt, (
        "a mechanically-fixable clarity finding must be stated as "
        "fix-eligible, matching SKILL.md's cheap/low-risk P3/P4 SHOULD-fix"
    )


def test_fixer_drops_blanket_clarity_fix_ban_negative():
    txt = _norm(FIXER)
    # negative: the old standalone blanket ban is gone
    assert "`clarity` findings (author judgment);" not in txt, (
        "the standalone '`clarity` findings (author judgment)' MUST-NOT-fix "
        "bullet must be gone — it contradicted the SHOULD-fix-by-default rule"
    )


def test_fixer_drops_medium_deferrable_wording_negative():
    txt = _norm(FIXER)
    assert "`medium`/`low`/`clarity`" not in txt, (
        "the old 'any medium/low/clarity finding ... structured deferral' "
        "set must be gone — medium is blocking"
    )
    assert "`medium` / `low` findings that are cheap" not in txt, (
        "the old 'SHOULD fix by default: medium/low' deferrable framing "
        "must be gone"
    )
    assert "P2/P3/P4" not in txt, "no P2/P3/P4-deferrable wording in the fixer"


# --- cmr-fixer.md: the fixes_skipped route covers EVERY unresolvable
# --- blocking finding, not only "non-trivial" ones (0.3.18.18) ---
#
# Round-5 ship-pre found a three-way routing trap. Concrete example:
# a finding that is medium/P2, classified MECHANICAL by nature (per the
# header allowlist: typo/dead-anchor/stale-label/date/whitespace +
# zero-executing-code + single-site + provably-inert), whose `suggested_fix`
# is `n/a`/empty (reviewer flagged it without concrete replacement text).
#
# Trace through the PRE-fix rules on that input:
#   * MUST-fix: "every `medium` ... that is mechanical" → should be fixed.
#     This qualifies (mechanical + medium).
#   * MUST-NOT-fix: "any finding whose `suggested_fix` is `n/a`/empty" →
#     MUST NOT be patched. This ALSO qualifies → contradicts MUST-fix.
#   * Non-trivial routing: scoped to a finding that is "non-trivial". But
#     the header makes mechanical and non-trivial DISJOINT, so a
#     mechanical-by-classification finding does not satisfy that clause's
#     literal precondition → the route didn't cover it either.
#   * Defer protocol: only `low`/`clarity` — P2/medium is excluded.
# Net: could not be fixed, could not be deferred, and the routing clause's
# stated trigger didn't apply → "neither fixed nor deferred = protocol
# violation" with no valid exit.
#
# Fix (0.3.18.18): the routing trigger is reworded from "non-trivial" to
# "a blocking finding you cannot mechanically resolve", explicitly covering
# BOTH non-trivial-by-nature AND mechanical-but-blocked-by-a-MUST-NOT-fix-
# condition (empty suggested_fix / reviewer disagreement / needs new
# content). Uses the EXISTING `fixes_skipped` field + EXISTING main-session
# hand-back — no new field / tier / defer category. Post-fix, the same
# example has exactly ONE route: fixes_skipped → main-session
# /diagnosing-bugs (via the `blocking-but-unfixable` reason), no
# contradiction against MUST-fix or MUST-NOT-fix (routing is not patching).


def test_fixer_unresolvable_blocking_routes_via_fixes_skipped():
    txt = _norm(FIXER)
    # positive: the route trigger is "cannot mechanically resolve", not just
    # "non-trivial" by nature
    assert "A blocking finding you **cannot mechanically resolve**" in txt, (
        "the fixes_skipped/main-session route must trigger on ANY "
        "unresolvable blocking finding, not only non-trivial-by-nature ones"
    )
    # positive: it explicitly names the MUST-NOT-fix-condition case
    assert (
        "one that is mechanical by classification but blocked by a "
        "**MUST-NOT-fix condition** below"
    ) in txt, (
        "the route must explicitly cover a mechanical-by-classification "
        "finding that a MUST-NOT-fix condition blocks (e.g. empty "
        "suggested_fix) — the round-5 three-way trap"
    )
    # positive: all three MUST-NOT-fix conditions are the scope, so the trap
    # is closed for reviewer-disagreement and needs-new-content too, not just
    # the empty-suggested_fix case
    assert (
        "its `suggested_fix` is `n/a`/empty, reviewers disagree on the "
        "correction, or a real fix would require inventing new "
        "behavior/content"
    ) in txt, (
        "the route must scope to ALL three MUST-NOT-fix conditions so the "
        "trap is closed for disagreement / new-content too, not only "
        "empty-suggested_fix"
    )
    # positive: the distinct fixes_skipped reason string for this case exists
    assert (
        "`blocking-but-unfixable → main-session /diagnosing-bugs "
        "(no safe suggested_fix)`"
    ) in txt, (
        "the MUST-NOT-fix-blocked case must have its own fixes_skipped "
        "reason string, distinct from the behavioral-complexity one"
    )


def test_fixer_route_uses_existing_machinery_only_negative():
    txt = _norm(FIXER)
    # negative: the old scoping that pinned the route to "non-trivial" alone
    # must be gone — that phrasing left the mechanical-but-blocked finding
    # with no exit
    assert "A blocking finding that is **non-trivial** is NOT yours" not in txt, (
        "the old 'A blocking finding that is non-trivial is NOT yours' "
        "scoping must be gone — it excluded mechanical-but-MUST-NOT-fix "
        "blocking findings from the route"
    )


# --- cmr-fixer.md: the Defer-protocol terminal rule enumerates the valid
# --- outcomes per tier — routing a blocking finding is NOT a violation
# --- (0.3.18.19) ---
#
# 0.3.18.18 added a THIRD valid outcome for a BLOCKING finding: route via
# `fixes_skipped` to main-session /diagnosing-bugs when it "cannot
# mechanically resolve". But the Defer-protocol section's closing terminal
# rule still read "A finding that is neither fixed nor deferred-with-all-
# three-parts is a protocol violation." The section's substantive rules
# (doc-mode carve-out, 3-part checklist) are all scoped to low/clarity, so
# that closing sentence contextually meant low/clarity — yet a fixer
# reading it literally, in isolation, could misapply it to a blocking
# finding it just VALIDLY ROUTED (technically "not fixed" — routed instead
# — and "not deferred" — defer excludes blocking findings), flagging its
# own correct output as a violation.
#
# Trace (post-fix) — a blocking (medium/P2) finding, mechanical by
# classification, `suggested_fix` empty → routed via fixes_skipped to
# main-session /diagnosing-bugs (0.3.18.18 route). Walk the reworded
# terminal rule: it is blocking, so its terminal outcomes are "fixed OR
# validly routed"; it was validly routed; the rule states that route "is a
# resolution, not a protocol violation." → explicitly NOT a violation. The
# only violation is a finding reaching NONE of its tier's outcomes (a
# silent drop). Gap closed.


def test_fixer_terminal_rule_recognizes_valid_routing_for_blocking():
    txt = _norm(FIXER)
    # positive: the terminal rule enumerates outcomes scoped by tier, and a
    # validly-routed blocking finding is explicitly NOT a protocol violation
    assert (
        "A **blocking** finding (P0/P1/P2; doc mode also P3) must be "
        "**fixed** OR **validly routed**"
    ) in txt, (
        "the terminal rule must state a blocking finding's valid outcomes "
        "are fixed OR validly-routed, not only fixed-or-deferred"
    )
    assert (
        "that route **is a resolution, not a protocol violation**"
    ) in txt, (
        "routing a blocking finding via fixes_skipped must be declared a "
        "resolution, NOT a protocol violation — the 0.3.18.18 third outcome"
    )
    assert (
        "A **non-blocking** (`low`/`clarity`) finding must be **fixed** OR "
        "**deferred-with-all-three-parts** per this section"
    ) in txt, (
        "the non-blocking tier's terminal outcomes (fixed OR deferred) must "
        "stay scoped to low/clarity, distinct from the blocking tier"
    )
    assert (
        "Only a finding that reaches *none* of these" in txt
        and "silently dropped" in txt
    ), (
        "the violation must be redefined as reaching NONE of the tier's "
        "outcomes (a silent drop), not the tier-blind 'neither fixed nor "
        "deferred'"
    )


def test_fixer_terminal_rule_drops_tier_blind_neither_nor_negative():
    txt = _norm(FIXER)
    # negative: the old tier-blind closing sentence — which a fixer could
    # misapply to a validly-routed blocking finding — must be gone
    assert (
        "A finding that is neither fixed nor deferred-with-all-three-parts "
        "is a protocol violation"
    ) not in txt, (
        "the old tier-blind 'neither fixed nor deferred = violation' "
        "sentence must be gone — it ignored the valid-routing third outcome "
        "for blocking findings"
    )


# --- cmr-fixer.md: the SHOULD-fix-by-default bullet names the FULL
# --- code-mode non-blocking tier (low AND clarity), not `low` alone
# --- (0.3.18.19) ---
#
# The SHOULD-fix bullet enumerated only `low` in its body ("the
# defer-eligible `low` findings ... fix them ... If fixing the lows keeps
# surfacing new findings"), never naming `clarity` for code mode. But the
# immediately-following MUST-NOT-fix section back-references THIS rule to
# make a fixable `clarity` finding fix-eligible ("fix-eligible under the
# SHOULD-fix-by-default rule above") — a rule whose own text didn't include
# clarity — and SKILL.md's "cheap/low-risk P3/P4 should still be FIXED now"
# (P4 = clarity) says the same. Two independent legs (Claude P3 + codex P2)
# found the gap.
#
# Trace (post-fix) — a cheap/low-risk `clarity` (P4) finding WITH a concrete
# suggested_fix, no reviewer disagreement, no new content, in code mode.
# Walk the reworded SHOULD-fix bullet: it names "the defer-eligible
# `low`/`clarity` findings (correctness/code mode ...)" as the fix-by-default
# set → the clarity finding is explicitly in-set → fix now. This is
# consistent with the MUST-NOT-fix back-reference ("fix-eligible under the
# SHOULD-fix-by-default rule above") and SKILL.md's P3/P4 default-fix rule.


def test_fixer_should_fix_bullet_names_clarity_for_code_mode():
    txt = _norm(FIXER)
    # positive: the SHOULD-fix set names the full code-mode non-blocking tier
    assert (
        "the defer-eligible `low`/`clarity` findings (correctness/code mode; "
        "in **doc mode `low` is blocking**, see above, so only `clarity` is "
        "defer-eligible there)"
    ) in txt, (
        "the SHOULD-fix bullet must name low AND clarity for code mode "
        "(doc mode: only clarity), matching the MUST-NOT-fix back-reference "
        "and SKILL.md's cheap/low-risk P3/P4 SHOULD-fix"
    )
    # positive: the follow-up drift clause covers the whole non-blocking tier,
    # not just "the lows"
    assert (
        "If fixing these non-blocking findings keeps surfacing **new** "
        "findings (drift)"
    ) in txt, (
        "the drift stop-condition must cover the whole non-blocking tier "
        "(low + clarity), not only 'the lows'"
    )


def test_fixer_should_fix_bullet_drops_low_only_wording_negative():
    txt = _norm(FIXER)
    # negative: the old low-only body must be gone
    assert "the defer-eligible `low` findings (correctness/code mode" not in txt, (
        "the old low-only 'the defer-eligible `low` findings' body must be "
        "gone — it omitted clarity for code mode"
    )
    assert "If fixing the lows keeps surfacing" not in txt, (
        "the old 'If fixing the lows' drift clause must be gone — it "
        "excluded clarity from the fix-by-default sweep"
    )


# --- cmr-fixer.md: the Defer-protocol terminal rule recognizes a FALSE
# --- adjudication as a valid resolution, at ANY severity, BEFORE the
# --- blocking/non-blocking branch (0.3.18.20) ---
#
# 0.3.18.19 reworded the terminal rule to enumerate outcomes per tier
# (blocking → fixed-or-routed; non-blocking → fixed-or-deferred). But the
# First-duty § establishes THREE per-finding actions: REAL → resolve
# (fix/route), FALSE → reject with evidence in `adjudications`, incidental
# → separate patch. The reworded terminal rule enumerated only the two
# REAL-outcome branches, so a finding correctly adjudicated FALSE — neither
# fixed, nor routed, nor deferred — literally "reaches none of these" and
# would trip the violation flag. A finding can be judged FALSE at ANY
# severity, so the FALSE resolution must sit BEFORE (and independent of)
# the blocking/non-blocking branch: only REAL findings proceed to that
# branch.
#
# Trace (post-fix) — a supplied medium/P2 (blocking-labelled) finding the
# fixer reads against source and adjudicates FALSE, recording refuting
# evidence in `adjudications`. Walk the terminal rule: a FALSE adjudication
# is "itself a complete, valid resolution — at ANY severity", needs no
# fix/route/deferral, and "is not among the drops" → explicitly NOT a
# violation, even though it was labelled blocking (so never fixed, never
# routed) and blocking findings are never deferred. Gap closed.


def test_fixer_terminal_rule_false_adjudication_is_valid_resolution():
    txt = _norm(FIXER)
    # positive: a FALSE adjudication is a complete valid resolution at ANY
    # severity, resolved BEFORE the tier branch (only REAL proceeds)
    assert (
        "**A finding you adjudicate FALSE** (First-duty §, with the "
        "refuting evidence recorded in `adjudications`) is **itself a "
        "complete, valid resolution**"
    ) in txt, (
        "the terminal rule must recognize a FALSE-adjudicated finding as a "
        "complete valid resolution, not a silent drop"
    )
    assert (
        "at ANY severity, since a finding can be judged FALSE whether it "
        "was labelled blocking or non-blocking"
    ) in txt, (
        "FALSE must apply at ANY severity — a finding can be judged FALSE "
        "whether blocking or non-blocking"
    )
    assert (
        "Only a finding adjudicated **REAL** proceeds to the tier-scoped "
        "branch that follows"
    ) in txt, (
        "only REAL findings may reach the blocking/non-blocking terminal "
        "branch — FALSE resolves before it"
    )
    # the violation clause now explicitly exempts a FALSE adjudication and
    # scopes the drops to REAL findings
    assert "a FALSE adjudication is not among the drops" in txt, (
        "the violation clause must explicitly exclude a FALSE adjudication "
        "from the silent-drop set"
    )
    assert (
        "a REAL non-blocking finding silently dropped" in txt
        and "a REAL blocking finding silently dropped" in txt
    ), (
        "the silent-drop set must be scoped to REAL findings, since a FALSE "
        "verdict is a resolution"
    )


def test_fixer_terminal_rule_false_not_a_violation_negative():
    txt = _norm(FIXER)
    # negative: the pre-fix drop set was severity/tier only, with no REAL
    # qualifier — it would have swept a FALSE-adjudicated finding into the
    # violation. That un-qualified phrasing must be gone.
    assert (
        "a non-blocking finding silently dropped (no fix, no structured "
        "deferral), or a blocking finding silently dropped (no fix, no "
        "route)"
    ) not in txt, (
        "the old drop set (no REAL qualifier) must be gone — it would have "
        "flagged a validly-adjudicated FALSE finding as a violation"
    )


# --- cmr-fixer.md: the `deferred[]` schema severity is a pipe-delimited
# --- enum representing the full legal set (low|clarity), matching the
# --- other severity fields' syntax and the doc-mode clarity deferral the
# --- prose allows (0.3.18.20) ---
#
# The strict JSON `deferred[]` example hardcoded `"severity": "low"` — a
# single literal, not an enum. But the defer-protocol prose (part 1)
# explicitly allows a doc-mode `clarity` deferral ("`low`/`clarity`
# (doc mode: `clarity` only)"), and the sibling severity fields
# (adjudications verdict, incidental_fixes, reported_defects) all use a
# pipe-delimited enum showing the valid set. The single `"low"` broke that
# convention and could not represent a legal doc-mode clarity deferral.


def test_fixer_deferred_severity_enum_includes_clarity():
    full = _norm(FIXER)
    # positive: the deferred[] severity is the pipe-delimited legal set
    assert '"severity": "low|clarity"' in full, (
        "deferred[].severity must be a pipe-delimited enum (low|clarity), "
        "matching the prose's doc-mode clarity deferral and the other "
        "severity fields' enum syntax"
    )
    # negative: the old single-literal `"low"` must be gone
    assert '"severity": "low",' not in full, (
        "the old single-literal deferred[].severity `\"low\"` must be gone — "
        "it could not represent a legal doc-mode `clarity` deferral"
    )
