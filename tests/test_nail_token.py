"""The 钉子令牌 (nail token, ADR 0130) discipline must stay pinned in the
completeness lens — the second half of 0.3.17.0.

User ratification 2026-07-12; wiki §额外硬规则 #9. Two semantics, both
scoped to the COMPLETENESS lens (the DONE-precondition + jurisdiction
handoff live here, not in the correctness reviewer):

4. 辖区移交 — judging any spec-surface DONE has a PRECONDITION: that
   surface's contract test is already in the repo. A missing nail is
   itself a blocking finding (category 缺钉 / missing-nail) with a named
   suggested nail point. Once DONE-and-nailed, the surface permanently
   leaves completeness's jurisdiction; later rounds do NOT re-litigate it,
   its guard being test-red-at-write-point + the correctness channel.
5. 钉上刻字 — a contract-nail test's name / first-line comment carries an
   authorization token (e.g. 契约钉 #491·永不喂全知). Suggested nail points
   follow this naming convention; an engraved nail in the diff with no
   authorization provenance is blocking (same family as the existing
   preexistingAssertionTouched assertion-hunting + the #732
   silent-nail-flip prohibition).

Phrase pins (positive + negative counterpart each), so a wiki re-sync that
weakens the token — missing nail downgraded below blocking, or a
DONE-and-nailed surface re-pulled into completeness's jurisdiction — fails
here.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPLETENESS = ROOT / "prompts" / "cmr-completeness.md"


def _norm(path):
    # prose files hard-wrap at ~72 cols; assertions must not break on a
    # line wrap landing inside the asserted phrase
    return " ".join(path.read_text(encoding="utf-8").split())


def _nail_section():
    # the nail-token section sits BETWEEN the submission contract and the
    # golden-hashed doc-mode addendum; slice it out so ADR 0130 / blocking
    # assertions bind to THIS section, not to the whole file
    txt = _norm(COMPLETENESS)
    start = txt.index("## 钉子令牌")
    end = txt.index("## Doc mode addendum")
    assert start < end, "the nail-token section must precede the doc-mode addendum"
    return txt[start:end]


# --- semantics 4: DONE-precondition + jurisdiction handoff


def test_nail_token_done_precondition_positive():
    sec = _nail_section()
    assert "## 钉子令牌" in sec, (
        "the completeness lens must carry the 钉子令牌 section, or a DONE "
        "verdict can be signed with no contract test behind it"
    )
    assert "ADR 0130" in sec, "the nail token must cite its ratifying ADR"
    assert (
        "precondition: that surface's contract test is already in the repo"
    ) in sec, "semantics 4: DONE has the nail-in-repo precondition"
    assert "A missing nail is itself a **blocking** finding" in sec, (
        "a missing nail must itself be blocking, not a soft note"
    )
    assert "category **缺钉 (missing-nail)**" in sec, (
        "the missing-nail finding needs its own named category"
    )
    assert "**suggested nail point**" in sec, (
        "a 缺钉 finding must name a suggested nail point for the fixer"
    )


def test_nail_token_jurisdiction_handoff_positive():
    sec = _nail_section()
    assert "permanently leaves completeness's jurisdiction" in sec, (
        "a DONE-and-nailed surface must hand off out of the completeness "
        "lens, or later rounds re-verify closed surfaces forever"
    )
    assert "later rounds do NOT re-litigate an already-DONE-and-nailed surface" in sec
    assert "**test red at the write-point**" in sec, (
        "the handed-off surface's guard is the red test at the write point"
    )
    assert "**correctness channel**" in sec, (
        "plus the correctness channel — the other half of the guard"
    )
    assert "The boundary is temporal, and the token is the test." in sec, (
        "the completeness/correctness split is temporal and the token is "
        "the test — the load-bearing rationale sentence"
    )


def test_nail_token_jurisdiction_handoff_negative():
    sec = _nail_section().lower()
    # negative counterpart: the surface must LEAVE, never stay; and a
    # missing nail must never be reframed as advisory / non-blocking
    assert "stays in completeness's jurisdiction" not in sec, (
        "a DONE-and-nailed surface must not be told to STAY in the lens"
    )
    assert "re-verify every surface each round" not in sec
    assert "missing nail is advisory" not in sec, (
        "a missing nail must be blocking, never advisory"
    )
    assert "缺钉不阻断" not in sec
    assert "not blocking" not in sec


# --- semantics 5: engraving convention + provenance check


def test_nail_engraving_convention_positive():
    sec = _nail_section()
    assert "**钉上刻字 (engraving — the paired convention).**" in sec, (
        "the engraving convention must be carried alongside the token"
    )
    assert "carries an **authorization token**" in sec, (
        "a contract nail's name/first-line comment carries an auth token"
    )
    assert "`契约钉 #491·永不喂全知`" in sec, (
        "the worked engraving example must be preserved verbatim"
    )
    assert "When you suggest a nail point, name it by this convention." in sec, (
        "suggested nail points must follow the engraving naming convention"
    )
    assert "no authorization provenance" in sec, (
        "an engraved nail with no provenance is the blocking trigger"
    )
    assert "(issue AC / ADR / prior-round ruling)" in sec, (
        "the three licit provenance sources must be named"
    )
    assert "`preexistingAssertionTouched` assertion-hunting" in sec, (
        "the engraving check must be tied to the existing "
        "preexistingAssertionTouched assertion-hunting family"
    )
    assert "#732 silent-nail-flip prohibition" in sec, (
        "and to the #732 silent-nail-flip prohibition"
    )


def test_nail_engraving_convention_negative():
    sec = _nail_section().lower()
    # negative counterpart: an unprovenanced engraved nail must never be
    # waved through, and the check must not be softened to a suggestion
    assert "engraved nail without provenance is acceptable" not in sec
    assert "provenance is optional" not in sec
    assert "may add an engraved nail" not in sec, (
        "the reviewer flags engraved nails, never authorizes minting new "
        "ones outside a licit provenance"
    )


def test_nail_token_sits_after_submission_contract():
    # the nail token is the SECOND 0.3.17.0 half; it must land after the
    # 交卷契约 paragraph (added by 7bc9e9e) and before the golden-hashed
    # doc-mode addendum, so neither of those slices is disturbed
    txt = _norm(COMPLETENESS)
    assert (
        txt.index("## Submission contract")
        < txt.index("## 钉子令牌")
        < txt.index("## Doc mode addendum")
    ), (
        "order must be: submission contract → nail token → doc-mode "
        "addendum (the last is golden-hashed)"
    )
