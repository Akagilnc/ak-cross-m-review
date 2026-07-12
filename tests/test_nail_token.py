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
    # 0.3.18.9: a nail permanently leaves jurisdiction only for ALL
    # SUBSEQUENT rounds — i.e. AFTER the confirmation round confirms it —
    # not immediately on the qualifying round.
    assert (
        "permanently leave\ncompleteness's jurisdiction for ALL subsequent rounds"
        in COMPLETENESS.read_text(encoding="utf-8")
        or "permanently leave completeness's jurisdiction for ALL subsequent rounds"
        in sec
    ), (
        "a DONE-and-nailed surface hands off out of the completeness lens "
        "for all SUBSEQUENT rounds — but only after the confirmation round"
    )
    assert (
        "rounds after the confirmation round do NOT re-litigate an "
        "already-confirmed DONE-and-nailed surface" in sec
    )
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


def test_nail_token_confirmation_round_reaudits_qualifying_nail():
    """0.3.18.9 finding #1: a surface nailed in the QUALIFYING round is
    still audited by the CONFIRMATION round — nailing takes permanent
    effect only after it survives the confirmation round, so the
    confirmation round has something substantive to re-verify."""
    sec = _nail_section()
    # positive: the confirmation round re-audits the qualifying-round nail
    assert "the very next **confirmation round**\nstill audits it" in (
        COMPLETENESS.read_text(encoding="utf-8")
    ) or "the very next **confirmation round** still audits it" in sec, (
        "a qualifying-round nail must still be audited by the next "
        "confirmation round — that is what makes it substantive"
    )
    # positive: permanent only AFTER the confirmation round confirms
    assert "Only after the confirmation round\nindependently confirms DONE-and-nailed" in (
        COMPLETENESS.read_text(encoding="utf-8")
    ) or "Only after the confirmation round independently confirms DONE-and-nailed" in sec, (
        "permanent jurisdiction exit is gated on the confirmation round "
        "independently confirming DONE-and-nailed"
    )
    # positive: a not-yet-confirmed qualifying nail is NOT on the
    # out-of-jurisdiction list, so it stays auditable
    assert "not yet confirmed" in sec and "is NOT on this list" in sec, (
        "a qualifying-round nail not yet confirmed must not be on the "
        "DONE-and-nailed (out-of-jurisdiction) list yet"
    )
    # negative: the old immediate-on-qualifying wording must be gone
    assert "permanently leaves completeness's jurisdiction: later rounds" not in sec, (
        "the old wording that a nail permanently leaves jurisdiction "
        "immediately (before the confirmation round) must be removed"
    )
    assert "later rounds do NOT re-litigate an already-DONE-and-nailed surface" not in sec, (
        "the old 'later rounds' (immediate) phrasing must be replaced by "
        "'rounds after the confirmation round'"
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
    # 0.3.18.12 codex r12 P2: tamper-scoping now defers to the entry's
    # (confirmation-round-refreshed) baseline ref via the single authoritative
    # definition — NOT the stale "nail-authorization time / state at which its
    # nail was authorized" phrasing (that predated 0.3.18.11's refresh rule and
    # contradicted it).
    assert "beyond the entry's baseline ref" in sec, (
        "nail-tamper must be scoped to change BEYOND the entry's baseline ref, "
        "not any touch on the nailed surface"
    )
    assert (
        "beyond that baseline ref" in sec
    ), "the tamper test is keyed to change beyond the entry's (refreshed) baseline ref"
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
    BEYOND the entry's baseline ref; the original nailed change is
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


def test_baseline_ref_refreshes_to_confirmation_round_at_handoff():
    """0.3.18.11 codex r11 P2 — the baseline-refresh-at-permanent-handoff fix.

    The baseline ref is captured at QUALIFYING-round nail-eligibility time
    (0.3.18.5 beyond-baseline tamper scoping). But if the surface is
    legitimately modified BETWEEN the qualifying round and the confirmation
    round (e.g. a non-blocking P3 fix the confirmation round re-audits and
    approves on the UPDATED surface), the stale qualifying-round baseline would
    make subsequent rounds misclassify that already-reviewed update as
    post-nail tampering — a false-positive nail-tamper flag. Fix: at the
    permanent hand-off the baseline ref is REFRESHED to the confirmation
    round's state. Must land in BOTH files (two-file sync discipline).
    """
    sec = _nail_section()
    step5 = _norm(SKILL)[
        _norm(SKILL).index("## Step 5 — termination signals") : _norm(SKILL).index(
            "## Step 6"
        )
    ]
    # positive — completeness lens (§钉子令牌): baseline recorded for the
    # permanent entry is the CONFIRMATION round's state, not qualifying's
    assert "Baseline refresh at permanent hand-off:" in sec, (
        "the completeness lens must name the baseline-refresh rule"
    )
    assert (
        "is the **CONFIRMATION round's state**, NOT the original "
        "qualifying-round baseline" in sec
    ), (
        "the completeness lens must record the CONFIRMATION round's state as "
        "the permanent-entry baseline, not the original qualifying baseline"
    )
    # positive — SKILL.md Step 5 mirror: same rule, both files agree
    assert "Baseline refresh at permanent hand-off (0.3.18.11):" in step5, (
        "SKILL.md Step 5 must carry the same baseline-refresh rule"
    )
    assert (
        "is the **CONFIRMATION round's state**, NOT the original "
        "qualifying-round baseline" in step5
    ), (
        "SKILL.md Step 5 must record the CONFIRMATION round's state as the "
        "permanent-entry baseline, mirroring the completeness lens"
    )
    # positive (both) — nail-tamper is now scoped beyond the REFRESHED
    # baseline, and the refresh happens exactly once at hand-off. Both `sec`
    # and `step5` are _norm()'d (single-spaced), so match the collapsed form.
    for text, name in ((sec, "completeness lens"), (step5, "SKILL.md Step 5")):
        assert (
            "scoped beyond THIS refreshed (confirmation-round) baseline" in text
        ), f"{name}: tamper must be scoped beyond the REFRESHED baseline"
        assert (
            "refreshed exactly once, at this permanent hand-off" in text
        ), f"{name}: the ref is refreshed exactly once, at permanent hand-off"
    # negative (both) — the old "baseline stays at the qualifying-round commit
    # forever" implication must NOT be reintroduced: no wording that the
    # permanent entry retains / keeps / is left at the qualifying baseline
    for text, name in ((sec, "completeness lens"), (step5, "SKILL.md Step 5")):
        for bad in (
            "baseline stays at the qualifying",
            "left pointing at the qualifying",
            "retains the original qualifying-round baseline",
            "keeps the qualifying-round baseline",
        ):
            assert bad not in text, (
                f"{name}: the stale-qualifying-baseline-forever wording "
                f"('{bad}') must not be present"
            )


def test_no_stale_nail_authorization_time_baseline_phrasing_whole_file():
    """0.3.18.12 codex r12 P2 — the same-file stale-phrase contradiction.

    0.3.18.11 added the baseline-refresh rule: a PERMANENTLY nailed surface's
    `DONE-and-nailed` entry records the CONFIRMATION-round state as its
    baseline ref, not the original qualifying-round baseline. But older
    prose (predating the refresh rule) still described the baseline ref
    generically as 'captured at nail-authorization time' / scoped 'beyond the
    nail-authorization baseline' / 'relative to the state at which its nail
    was authorized' — the qualifying-round state. A reviewer reading those
    lines in isolation would revert to the stale baseline and reproduce the
    exact false-positive nail-tamper flag 0.3.18.11 eliminated.

    Fix: ONE authoritative definition of the baseline ref (= the ref
    currently recorded on the entry, refreshed once at permanent hand-off);
    every other mention just says 'the baseline ref'. This is a WHOLE-FILE
    guard (not scoped to one sub-section) so a future re-introduction of the
    stale phrasing ANYWHERE in either file is caught.
    """
    # negative — the stale, refresh-contradicting phrasings must be GONE from
    # the ENTIRE file (both files), wherever they might describe the
    # current/tamper-scoping baseline. (Bare "nail-authorization" as a verb —
    # e.g. "prevents nail-authorization" — is fine; only these baseline
    # re-descriptions are banned.)
    stale = (
        "captured at nail-authorization time",
        "captured at nail-authorization",
        "beyond the nail-authorization baseline",
        "relative to the state at which its nail was authorized",
    )
    for path, name in ((COMPLETENESS, "cmr-completeness.md"), (SKILL, "SKILL.md")):
        whole = _norm(path)
        for bad in stale:
            assert bad not in whole, (
                f"{name}: stale baseline phrasing '{bad}' contradicts the "
                f"0.3.18.11 confirmation-round refresh rule — a reviewer "
                f"reading it in isolation reverts to the qualifying-round "
                f"baseline and reproduces the false-positive tamper flag"
            )
    # positive — the SINGLE authoritative definition is present in both files:
    # the baseline ref is whatever is currently recorded on the entry, which
    # per the refresh rule is the confirmation-round state.
    comp = _norm(COMPLETENESS)
    assert (
        "**currently recorded on the entry**, which\nper the".replace("\n", " ")
        in comp
    ), (
        "cmr-completeness.md must define the baseline ref as the ref currently "
        "recorded on the entry (the single authoritative definition)"
    )
    assert (
        "per the **baseline refresh**\nrule above is the **confirmation-round** state".replace(
            "\n", " "
        )
        in comp
    ), "cmr-completeness.md's authoritative definition must tie the ref to the refresh rule"
    step5 = _norm(SKILL)[
        _norm(SKILL).index("## Step 5 — termination signals") : _norm(SKILL).index(
            "## Step 6"
        )
    ]
    assert "**currently recorded on the\nentry**".replace("\n", " ") in step5, (
        "SKILL.md Step 5 must mirror the 'currently recorded on the entry' "
        "authoritative baseline definition"
    )
    assert (
        "per the **baseline refresh** rule below is the\nconfirmation-round state".replace(
            "\n", " "
        )
        in step5
    ), "SKILL.md Step 5's authoritative definition must tie the ref to the refresh rule"


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


# --- 0.3.18.8 codex r8 P1: nail authorization requires round-wide
#     merged-ledger agreement. A single leg judging a surface DONE must NOT
#     nail it when ANOTHER leg reports a blocking gap on the same surface
#     that round — otherwise the surface leaves jurisdiction (later rounds
#     skip it) and neither the dissenting leg's gap nor the DONE judgment
#     ever gets the two-round confirmation. Same principle as doc-mode ②(c):
#     a single dissenting leg's blocking finding prevents convergence — here
#     it prevents nail-authorization.


def test_nail_authorization_requires_round_wide_merged_ledger_positive():
    sec = _nail_section()
    # the authorization precondition is stated as DONE-judgment AND a clean
    # round-wide merged ledger for that specific surface
    assert "round-wide\nmerged ledger" in COMPLETENESS.read_text(
        encoding="utf-8"
    ) or "round-wide merged ledger" in sec, (
        "nail authorization must require the ROUND-WIDE MERGED LEDGER, not a "
        "single leg's DONE judgment"
    )
    assert "zero blocking finding on that specific surface" in sec, (
        "the merged ledger must show zero blocking finding on THAT surface "
        "before the surface may be nailed"
    )
    assert "necessary but not sufficient" in sec, (
        "one leg's DONE judgment is necessary but not sufficient to nail"
    )
    assert "NOT nailed this round" in sec, (
        "if another leg reports a blocking gap on the same surface the same "
        "round, the surface is NOT nailed that round"
    )
    # same aggregation the doc-mode zero-blocking-ledger check uses
    assert "the doc-mode zero-blocking-ledger check uses" in sec, (
        "the merged ledger is the same aggregation as the doc-mode "
        "zero-blocking-ledger check — cross-reference must be present"
    )
    # single-reviewer dispatch degrades gracefully (no special case)
    assert "single-reviewer" in sec and "degrades gracefully" in sec, (
        "a single-reviewer completeness dispatch must degrade gracefully — "
        "the round-wide ledger trivially holds just that one leg's findings"
    )


def test_nail_authorization_requires_round_wide_merged_ledger_negative():
    sec = _nail_section()
    # the OLD "single leg DONE = nail unconditionally" wording must be gone:
    # the section no longer says merely judging a surface DONE (+ nail) hands
    # it out of jurisdiction with no round-wide-ledger check.
    assert "Once you judge a surface DONE **and it has a nail**, that surface" not in sec, (
        "the old 'any one leg's DONE + nail = leaves jurisdiction' wording "
        "must be replaced by the round-wide-ledger precondition"
    )
    low = sec.lower()
    assert "one leg judging done is enough to nail" not in low
    assert "a single leg's done judgment nails the surface" not in low


def test_skill_step5_nail_authorization_round_wide_ledger():
    """0.3.18.8 codex r8 P1 — SKILL.md Step 5's mode-general orchestrator
    note must also gate nail-authorization on the round-wide merged ledger,
    so the orchestrator does not add a surface to DONE-and-nailed on one
    leg's DONE when another leg flagged a blocking gap that round."""
    step5 = _norm(SKILL)[
        _norm(SKILL).index("## Step 5 — termination signals") : _norm(SKILL).index(
            "## Step 6"
        )
    ]
    assert "round-wide merged ledger" in step5, (
        "Step 5 must gate nail-authorization on the round-wide merged ledger"
    )
    assert "zero blocking finding on\nthat surface" in SKILL.read_text(
        encoding="utf-8"
    ) or "zero blocking finding on that surface" in step5, (
        "Step 5 must require zero blocking finding on that surface before it "
        "earns a place on the DONE-and-nailed list"
    )
    assert "one leg's DONE judgment does NOT nail a surface" in step5, (
        "Step 5 must say one leg's DONE does NOT nail a surface another leg "
        "flagged as a blocking gap the same round"
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
