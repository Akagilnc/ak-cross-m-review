"""The 缺钉 (missing-nail) gate must stay pinned in the completeness lens.

0.3.18.14 REVERSAL (owner authorization 2026-07-12): the 钉子令牌 nail-token
jurisdiction-handoff apparatus (0.3.17.0 minus this gate, patched across
0.3.18.3–0.3.18.12) was removed — it required cross-round orchestrator
persistence the skill has no way to implement (no backing script/file
exists anywhere in the repo), and its tamper-detection logic had no
carve-out for a legitimate multi-commit fix on a currently-reported
surface. Only the ONE sound piece survives:

  缺钉 precondition — judging any spec-surface DONE has a PRECONDITION:
  that surface's contract test is already in the repo. A missing nail is
  itself a blocking finding (category 缺钉 / missing-nail) with a named
  suggested nail point. This is a SAME-ROUND, diff-and-repo-only check —
  no cross-round state, so the skill can actually run it.

These tests pin the survivor (positive) AND guard against the deleted
jurisdiction-handoff apparatus creeping back (negative).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPLETENESS = ROOT / "prompts" / "cmr-completeness.md"
SKILL = ROOT / "SKILL.md"


def _norm(path):
    # prose files hard-wrap at ~72 cols; assertions must not break on a
    # line wrap landing inside the asserted phrase
    return " ".join(path.read_text(encoding="utf-8").split())


def _gate_section():
    # slice ONLY the missing-nail gate section: from its header up to the
    # next section header (`## Grade every gap …`). Scoping to the
    # immediately-following header keeps the grade-severity section OUT of
    # the slice.
    txt = _norm(COMPLETENESS)
    start = txt.index("## 缺钉闸")
    end = txt.index("## Grade every gap")
    assert start < end, "the missing-nail gate must precede the grade-severity section"
    return txt[start:end]


# --- the survivor: the 缺钉 (missing-nail) precondition ---


def test_missing_nail_gate_precondition_positive():
    sec = _gate_section()
    assert "## 缺钉闸" in sec, (
        "the completeness lens must carry the 缺钉 (missing-nail) gate, or a "
        "DONE verdict can be signed with no contract test behind it"
    )
    assert "ADR 0130" in sec, "the gate must cite its ratifying ADR"
    assert (
        "precondition: that surface's contract test is already in the repo"
    ) in sec, "DONE has the nail-in-repo precondition"
    assert "A missing nail is itself a **blocking** finding" in sec, (
        "a missing nail must itself be blocking, not a soft note"
    )
    assert "category **缺钉 (missing-nail)**" in sec, (
        "the missing-nail finding needs its own named category"
    )
    assert "**suggested nail point**" in sec, (
        "a 缺钉 finding must name a suggested nail point for the fixer"
    )


def test_missing_nail_gate_is_same_round_diff_and_repo_only():
    """The whole reason the gate survived the reversal: it is checkable from
    the change + the current repo in a single round, with no cross-round
    state — unlike the deleted jurisdiction-handoff apparatus, which the
    skill (a stateless external-session invocation) had no way to run."""
    sec = _gate_section()
    assert "**same-round, diff-and-repo-only** check" in sec, (
        "the gate must be stated as a same-round, diff-and-repo-only check"
    )
    assert "no cross-round state" in sec, (
        "the gate must explicitly disclaim cross-round state — that is what "
        "distinguishes it from the reverted handoff apparatus"
    )


def test_missing_nail_gate_negative_not_downgraded():
    sec = _gate_section().lower()
    # a missing nail must never be reframed as advisory / non-blocking
    assert "missing nail is advisory" not in sec, (
        "a missing nail must be blocking, never advisory"
    )
    assert "缺钉不阻断" not in sec
    assert "not blocking" not in sec


def test_missing_nail_gate_sits_after_submission_contract():
    # the gate is the surviving second half of 0.3.17.0; it must land after
    # the 交卷契约 paragraph and before the golden-hashed doc-mode addendum,
    # so neither of those slices is disturbed
    txt = _norm(COMPLETENESS)
    assert (
        txt.index("## Submission contract")
        < txt.index("## 缺钉闸")
        < txt.index("## Doc mode addendum")
    ), (
        "order must be: submission contract → missing-nail gate → doc-mode "
        "addendum (the last is golden-hashed)"
    )


# --- the reversal guard: the deleted jurisdiction-handoff apparatus must
#     NOT creep back into either file (0.3.18.14) ---


def test_nail_jurisdiction_handoff_apparatus_is_gone():
    """0.3.18.14 reversal: every artefact of the nail-token
    jurisdiction-handoff mechanism must be absent from BOTH the completeness
    lens and SKILL.md. A future re-sync that re-introduces any of these
    (all describing the nonexistent cross-round orchestrator persistence)
    fails here."""
    # NOTE: "confirmation round" / "qualifying round" are NOT here — they are
    # shared with the surviving severity-aware two-round convergence machinery
    # (Step 5), and "dispatch packet" survives in the doc-mode addendum. Only
    # phrases UNIQUE to the reverted nail-token apparatus belong in this guard.
    dead_phrases = (
        "DONE-and-nailed",
        "nail-tamper",
        "baseline ref",
        "钉上刻字",
        "jurisdiction hand-off",
        "Cross-round jurisdiction hand-off",
        "round-wide merged ledger",
        "authorization token",
        "out-of-jurisdiction",
    )
    for path, name in ((COMPLETENESS, "cmr-completeness.md"), (SKILL, "SKILL.md")):
        whole = _norm(path)
        for bad in dead_phrases:
            assert bad not in whole, (
                f"{name}: the reverted nail-token jurisdiction-handoff phrase "
                f"'{bad}' must not be present (0.3.18.14 removed the "
                f"apparatus — it required cross-round persistence the skill "
                f"cannot implement)"
            )
