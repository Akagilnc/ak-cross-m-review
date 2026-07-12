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
SKILL = ROOT / "SKILL.md"


def _norm(path):
    # prose files hard-wrap at ~72 cols; assertions must not break on a
    # line wrap landing inside the asserted phrase
    return " ".join(path.read_text(encoding="utf-8").split())


def _nail_section():
    # slice ONLY the nail-token section: from its header up to the next
    # section header (`## Grade every gap …`, which the convergence commit
    # inserted between the nail token and the doc-mode addendum). Scoping to
    # the immediately-following header keeps the grade-severity section OUT
    # of the slice, so ADR 0130 / blocking pins bind to THIS section alone.
    txt = _norm(COMPLETENESS)
    start = txt.index("## 钉子令牌")
    end = txt.index("## Grade every gap")
    assert start < end, "the nail-token section must precede the grade-severity section"
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


# --- 0.3.18.3 finding #4: the DONE-and-nailed cross-round state is
#     PERSISTED + INJECTED by the orchestrator (unenforceable otherwise —
#     a fresh reviewer has no field telling it which surfaces are nailed)


def test_done_and_nailed_list_injected_into_packet_positive():
    sec = _nail_section()
    # the completeness lens states the packet carries the list + tokens
    assert "**`DONE-and-nailed surfaces`**" in sec, (
        "the dispatch packet must carry a DONE-and-nailed surfaces list, or "
        "the jurisdiction hand-off is unenforceable across rounds"
    )
    assert "nail's **authorization token**" in sec, (
        "each nailed surface on the list carries its nail's auth token"
    )
    assert "out of your jurisdiction" in sec and "do NOT\nre-audit" in COMPLETENESS.read_text(
        encoding="utf-8"
    ) or "do NOT re-audit it" in sec, (
        "a listed nailed surface is out-of-jurisdiction; the reviewer does "
        "not re-audit it"
    )
    # 0.3.18.5 codex r5 P1 (the 3-way interaction bug): a diff that modifies
    # a nailed surface *beyond its nail-authorization baseline* is a
    # nail-tamper → blocking — NOT any diff that merely touches the surface.
    # The cumulative-diff full-re-review means the original authorized-and-
    # nailed change ALWAYS still appears; keying tamper to "any touch" would
    # mis-flag it every confirmation round, so the two-round convergence
    # could never complete.
    assert "beyond the nail-authorization baseline" in sec, (
        "nail-tamper must be scoped to change BEYOND the nail baseline, not "
        "any touch on the nailed surface"
    )
    assert (
        "relative to the state at which its nail was authorized" in sec
    ), "the tamper test is keyed to change relative to the nail's authorized state"
    assert "nail-tamper → blocking" in sec, (
        "a post-nail modification of a nailed surface is a nail-tamper "
        "(blocking), not a re-opened completeness audit"
    )


def test_nail_tamper_scoped_to_baseline_not_any_touch():
    """0.3.18.5 codex r5 P1 — the 3-way interaction bug fix.

    nail-tamper × cumulative-diff full-re-review × two-round convergence
    collide: SKILL.md re-reviews the CUMULATIVE diff every round, so an
    already-DONE-and-nailed surface's *original authorized* change is always
    present in later/confirmation rounds. The old "any diff touching a
    nailed surface → tamper" mis-flagged that authorized change → the
    confirmation round could never come back clean → the two-round
    convergence could never complete. Fix: tamper is scoped to change
    BEYOND the nail-authorization baseline; the original nailed change is
    explicitly NOT re-flagged.
    """
    sec = _nail_section()
    # negative: the mis-flagging "any touch" wording must be GONE from both
    # the completeness lens and SKILL.md Step 5
    assert "any diff that touches a nailed surface" not in sec, (
        "the 'any touch = tamper' wording mis-flags the original authorized "
        "nailed change every cumulative-diff round — it must be gone"
    )
    step5 = _norm(SKILL)[
        _norm(SKILL).index("## Step 5 — termination signals") : _norm(SKILL).index(
            "## Step 6"
        )
    ]
    assert "any diff touching a nailed surface" not in step5, (
        "SKILL.md Step 5 must not key tamper to any touch either"
    )
    # positive: the original nailed change legitimately remains and is NOT
    # re-flagged (the crux of the convergence fix)
    assert "**NOT** tamper" in sec and "do **not** re-flag it" in sec, (
        "the original authorized-and-nailed change in the cumulative diff "
        "must be explicitly declared NOT tamper / not re-flagged"
    )
    assert "unchanged since its nail" in sec, (
        "a nailed surface unchanged since its nail = out-of-jurisdiction, "
        "skip — the other side of the baseline scoping"
    )
    # the DONE-and-nailed entry now carries a BASELINE REF (both files) so
    # 'changed since the nail' is checkable
    assert "its **baseline ref**" in sec, (
        "the completeness-lens DONE-and-nailed entry must carry a baseline ref"
    )
    assert "**baseline ref**" in step5, (
        "SKILL.md Step 5 DONE-and-nailed entry must carry the nail's "
        "baseline ref so tamper is checkable"
    )


def test_orchestrator_persists_done_and_nailed_list_mode_general():
    """0.3.18.4 codex r4 P1: the ORCHESTRATOR persistence+injection of the
    DONE-and-nailed list must live in a MODE-GENERAL completeness location
    (Step 5 termination), NOT confined to §Doc mode discipline ②(a). The
    钉子令牌 hand-off applies to EVERY completeness round — the ship-pre
    code gate AND doc mode — so a plain code/ship-pre multi-round loop must
    build that state too; scoping it to doc mode left code mode's
    nail-tamper detection unenforceable."""
    txt = _norm(SKILL)
    # the instruction now lives in Step 5, outside the doc-mode section
    step5 = txt[txt.index("## Step 5 — termination signals") : txt.index("## Step 6")]
    assert "persists a `DONE-and-nailed surfaces` list across rounds" in step5, (
        "Step 5 must say the orchestrator PERSISTS the DONE-and-nailed list "
        "across rounds — mode-general, not doc-only"
    )
    assert "injects it into every round's dispatch packet" in step5, (
        "Step 5 must say the orchestrator INJECTS the list into each packet"
    )
    # explicitly mode-general: names both completeness modes
    assert "ALL completeness modes" in step5 and "ship-pre" in step5 and "doc mode" in step5, (
        "the hand-off must be stated for EVERY completeness round — the "
        "ship-pre code gate AND doc mode — not doc-mode-scoped"
    )
    assert "For EVERY completeness round" in step5
    assert "nail-tamper → **blocking**" in step5, (
        "Step 5 must carry the nail-tamper → blocking rule so code mode "
        "enforces it too"
    )
    # regression: the instruction must NOT be confined to the doc-mode
    # discipline section (the r4 P1 placement error)
    doc = txt[txt.index("## Doc mode discipline") : txt.index("## Anti-patterns")]
    assert "persists a `DONE-and-nailed surfaces` list across rounds" not in doc, (
        "the persistence instruction must be hoisted OUT of the doc-mode "
        "section — leaving it there re-scopes the hand-off to doc mode"
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
