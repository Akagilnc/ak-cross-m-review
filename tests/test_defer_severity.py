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
