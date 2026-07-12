"""Severity-aware convergence must stay pinned (0.3.18.0, ADR-adjacent).

User ratification 2026-07-12; wiki §终止信号 sync done by the main session.
The unified rule: a round is CLEAR when it has NO BLOCKING finding, and
blocking severity is mode-dependent —

- correctness / per-slice AND the ship-pre completeness gate on CODE:
  blocking = P0/P1/P2; P3/P4 defer.
- doc mode (design-text review): blocking = P0/P1/P2/P3; only P4 defers.
- P4 never blocks in any mode.

Positive termination = TWO consecutive clear rounds (a qualifying round +
a full-re-review confirmation round, both clear) — extended from doc-only
to ALL modes. Every finding is still graded and REPORTED regardless of
severity (交卷契约); P3/P4 go to Deferred, they do not block the approve
vote.

These are phrase pins (positive + negative counterpart), so a wiki
re-sync that reverts to "zero-finding = approve" / "single clear round
converges" / "no P0/P1 → STOP" fails here.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWER = ROOT / "prompts" / "cmr-reviewer.md"
COMPLETENESS = ROOT / "prompts" / "cmr-completeness.md"
SKILL = ROOT / "SKILL.md"


def _norm(path):
    # prose files hard-wrap at ~72 cols; assertions must not break on a
    # line wrap landing inside the asserted phrase
    return " ".join(path.read_text(encoding="utf-8").split())


# --- correctness lens: converged = no blocking, NOT zero-finding


def test_reviewer_converged_is_no_blocking_not_zero_finding():
    txt = _norm(REVIEWER)
    # positive: converged means no critical/high/medium (P0/P1/P2)
    assert (
        "use when you raised **no critical / high / medium defect** this "
        "round"
    ) in txt, (
        "converged must be defined as 'no blocking (critical/high/medium)', "
        "not 'no defects at all'"
    )
    assert "P0 / P1 / P2 in the wiki's scale" in txt
    # a leg MAY still raise low/clarity and stay converged
    assert "do **not** cost your converged vote" in txt
    # findings verdict = at least one blocking
    assert (
        "use when you raised **at least one critical / high / medium**"
    ) in txt
    assert (
        "A round with only `low` / `clarity` findings is still `converged`"
    ) in txt


def test_reviewer_drops_zero_finding_converged_wording_negative():
    txt = _norm(REVIEWER)
    # the OLD criterion ("use when you found no defects") must be gone —
    # it would let a single low/clarity finding falsely flip to `findings`
    assert "use when you found no defects" not in txt, (
        "the pre-0.3.18.0 zero-defect converged criterion must be replaced "
        "by the no-blocking criterion"
    )


# --- completeness lens: severity grading + no-blocking gate


def test_completeness_grades_gaps_and_gate_is_no_blocking():
    txt = _norm(COMPLETENESS)
    # every gap graded P0–P4 (the prompt uses the en-dash form only)
    assert "Grade every gap P0–P4" in txt
    # the gate is now "no BLOCKING gap", not "zero NOT-DONE/PARTIAL/..."
    assert "Pass = no BLOCKING gap" in txt, (
        "the completeness gate must be no-blocking, not the old "
        "zero-any-verdict binary"
    )
    # the OLD binary gate wording must be gone
    assert (
        "Pass = zero NOT-DONE, zero PARTIAL, zero VIOLATES, zero "
        "UNVERIFIED-GAP" not in txt
    ), "the pre-0.3.18.0 zero-any-verdict gate wording must be replaced"
    # mode-dependent blocking thresholds spelled out
    assert "code / ship-pre" in txt and "blocking = P0 / P1 / P2" in txt
    assert "doc mode" in txt and "blocking = P0 / P1 / P2 / P3" in txt
    assert "P4 never blocks in any mode" in txt
    # non-blocking gaps deferred, never dropped
    assert "goes to Deferred" in txt and "never" in txt


def test_completeness_verdict_complete_is_no_blocking_gap():
    txt = _norm(COMPLETENESS)
    assert "no BLOCKING gap** this round" in txt, (
        "complete must mean 'no blocking gap', allowing reported-Deferred "
        "P3/P4 (P4 in doc mode) to remain"
    )
    assert "at least one blocking gap** above" in txt


# --- SKILL Step 5: concur = no blocking, two consecutive clear rounds


def test_skill_step5_concur_is_no_blocking_two_round():
    txt = _norm(SKILL)
    assert "**concur = no blocking finding.**" in txt, (
        "concur must be redefined as 'no blocking finding', not 'no finding'"
    )
    assert "Positive termination = two consecutive clear rounds" in txt, (
        "positive termination must require two consecutive clear rounds"
    )
    assert "ALL modes, not just doc" in txt, (
        "the two-round rule must be declared as extended to all modes"
    )
    # blocking severity spelled out, doc mode also P3
    assert "blocking = **P0 / P1 / P2**" in txt
    assert "doc mode also P3" in txt
    assert "P4 never blocks in any mode" in txt
    # re-qualify-from-scratch on a blocking finding in the confirmation
    # round. `txt` is already whitespace-collapsed by _norm, so the
    # normalized operand matches across the prompt's hard line-wrap.
    assert "re-qualifies from scratch" in txt


# --- 0.3.18.7 codex r7 P2: the Deferred-disposition sentence in the
#     concur definition must be MODE-QUALIFIED. The old wording said
#     "P3/P4 findings ... do not cost its concur vote" with no mode
#     qualifier, contradicting the first half (doc mode: P3 IS blocking).


def test_skill_step5_concur_defer_sentence_is_mode_qualified():
    txt = _norm(SKILL)
    # positive: the disposition sentence names the two modes separately —
    # P3/P4 non-blocking only in correctness/code mode; P4 only in doc mode
    assert (
        "**non-blocking** findings (P3/P4 in correctness/code mode; "
        "**P4 only** in doc mode); those go to Deferred and do **not** "
        "cost its concur vote" in txt
    ), (
        "the Deferred-disposition sentence must mode-qualify which "
        "severities are non-blocking (P3/P4 code, P4-only doc)"
    )
    # positive: doc-mode P3 is explicitly called out as blocking + vote-costing
    assert (
        "In doc mode P3 **is** blocking and **does** cost the concur vote"
        in txt
    ), (
        "the sentence must state that doc-mode P3 blocks and costs the "
        "concur vote, matching the first half of the paragraph"
    )
    # negative: the old mode-blind wording is gone — an unqualified
    # "P3/P4 findings; those go to Deferred and do **not** cost its concur
    # vote" (no correctness/doc-mode split attached) must not survive.
    assert (
        "P3/P4 findings; those go to Deferred and do **not** cost its "
        "concur vote" not in txt
    ), (
        "the old unqualified 'P3/P4 findings ... do not cost its concur "
        "vote' wording must be removed — it contradicts doc mode"
    )


# --- 0.3.18.3 finding #1: doc mode is the EXPLICIT exception to
#     all-legs-concur; its ledger check spans ALL legs so a dissenting
#     blocking finding cannot be swallowed under a majority-complete vote


def test_skill_step5_doc_mode_is_explicit_concur_exception_positive():
    txt = _norm(SKILL)
    # Step 5 names doc mode as the explicit exception to all-legs-concur
    assert "Doc mode is the explicit exception to all-legs-concur" in txt, (
        "Step 5 must flag doc mode as the explicit exception, so the "
        "all-modes two-round rule and doc-mode's majority form don't clash"
    )
    assert (
        "**Doc mode does NOT\n> require all-legs-concur**"
        in SKILL.read_text(encoding="utf-8")
    ), "Step 5 must state doc mode does NOT require all-legs-concur"
    # doc-mode clear form = majority-complete AND zero-blocking ledger that
    # aggregates EVERY leg (dissenter included)
    assert (
        "majority of\n> legs judge `complete`" in SKILL.read_text(encoding="utf-8")
        or "majority of legs judge `complete`" in txt
    ), "doc-mode convergence keeps its majority-complete form"
    assert (
        "aggregating ALL legs' findings,\n> including any leg that dissented"
        in SKILL.read_text(encoding="utf-8")
        or "aggregating ALL legs' findings, including any leg that dissented"
        in txt
    ), "the ledger check must span ALL legs, dissenters included"
    # the safety property: a single dissenting blocking finding blocks
    # convergence regardless of the majority vote
    assert "the dissent cannot be swallowed" in txt, (
        "the point of the all-legs ledger is that a minority blocking "
        "finding is not swallowed by a majority-complete vote"
    )


def test_skill_step5_doc_mode_exception_negative():
    """Negative: correctness/code modes must NOT be softened to majority —
    only doc mode is the exception; the others stay all-legs-concur."""
    txt = _norm(SKILL)
    # the correctness/code path still requires EVERY leg to concur
    assert (
        "In\n> correctness / code modes a round is clear only when **every**"
        in SKILL.read_text(encoding="utf-8")
        or "In correctness / code modes a round is clear only when **every**"
        in txt
    ), "correctness/code modes must stay all-legs-concur, not majority"
    # the doc-mode ②(c) ledger clause must carry the all-legs framing too
    doc_c = txt[txt.index("### ② Fix-classification ledger") : txt.index("### ③")]
    assert "aggregating ALL legs' findings, including any leg dissenting" in doc_c, (
        "②(c)'s qualifying-round ledger must span all legs incl. dissenters"
    )
    assert "again spanning ALL legs, dissenters included" in doc_c, (
        "②(c)'s confirmation-round ledger must also span all legs"
    )
    assert (
        "a single dissenting\n  leg's blocking finding (original-defect, fix-fix, or invention — all\n  count) keeps the ledger"
        in SKILL.read_text(encoding="utf-8")
        or "a single dissenting leg's blocking finding (original-defect, "
        "fix-fix, or invention — all count) keeps the ledger" in txt
    ), "②(c) must state the dissent-blocks-convergence safety property"
    # 0.3.18.9: the dissent property must NOT be filtered to original-defect
    assert "single dissenting leg's blocking original-defect finding" not in txt, (
        "②(c)'s dissent-blocks-convergence property must count blocking "
        "findings of any classification, not only original-defect"
    )


# --- SKILL Step 7: loop uses two-round + severity form


def test_skill_step7_loop_two_round_severity():
    raw = SKILL.read_text(encoding="utf-8")
    loop = raw[raw.index("## Step 7 — the loop") : raw.index("After every fix")]
    assert "blocking finding (P0/P1/P2; doc mode also P3)" in loop, (
        "the loop's fix arm must key off the blocking severity set"
    )
    assert "two consecutive clear rounds" in loop, (
        "the loop must require two consecutive clear rounds to STOP"
    )
    assert "confirmation round (FULL re-review)" in loop
    assert "re-qualify from" in loop
    # P3/P4 do not block and do not force a new round — but that CLEAR
    # status is orthogonal to fixing: cheap ones are still FIXED by default
    # (codex round-13 P2: the flow line used to read "→ reported-but-Deferred"
    # as the ACTION, which an orchestrator reads as "defer P3/P4 by default")
    assert "do NOT block, do NOT by themselves trigger another fix" in loop
    assert "counts as" in loop and "CLEAR regardless" in loop
    assert "ORTHOGONAL to whether" in loop
    assert "should still be FIXED" in loop, (
        "the loop must say cheap P3/P4 are still fixed now, not deferred"
    )
    assert "SHOULD-fix-by-default rule" in loop and "cmr-fixer.md" in loop, (
        "the loop must cross-reference the fixer's SHOULD-fix-by-default rule"
    )
    assert "Deferred is the" in loop and "narrow exception" in loop, (
        "deferral must be framed as the narrow exception, not the default"
    )
    assert "NOT banked as backlog debt" in loop
    # NEGATIVE: the old action-form "→ reported-but-Deferred" (defer as the
    # default outcome for a P3/P4-only round) must be gone
    assert "reported-but-Deferred" not in loop, (
        "the Step-7 flow must not present deferral as the default action "
        "for P3/P4 — fixing is the default, Deferred is the exception"
    )
    # the OLD flat "no P0/P1 → STOP" arm must be gone
    assert "no P0/P1     → STOP" not in loop, (
        "the pre-0.3.18.0 single-round 'no P0/P1 → STOP' arm must be "
        "replaced by the two-round rule"
    )
