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
