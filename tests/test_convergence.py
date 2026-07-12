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
    # every gap graded P0-P4
    assert "Grade every gap P0–P4" in txt or "Grade every gap P0-P4" in txt
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
    # re-qualify-from-scratch on a blocking finding in the confirmation round
    assert "re-qualifies from\nscratch" in SKILL.read_text(
        encoding="utf-8"
    ) or "re-qualifies from scratch" in txt


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
    # P3/P4 do not trigger a fix round
    assert "reported-but-Deferred" in loop and "do NOT block" in loop
    # the OLD flat "no P0/P1 → STOP" arm must be gone
    assert "no P0/P1     → STOP" not in loop, (
        "the pre-0.3.18.0 single-round 'no P0/P1 → STOP' arm must be "
        "replaced by the two-round rule"
    )
