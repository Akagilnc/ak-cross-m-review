"""Doc-mode discipline must stay pinned in SKILL.md + the completeness lens.

The doc-mode defenses (constitution kill-axis, fix-classification ledger,
bloat audit line, full confirmation-round early stop, round-10 escalation
gate, dead-leg standing degrade, self-check 三连) are a skill-local
RECORDED RULE (user decision 2026-07-06) pending wiki upstream. A wiki
re-sync must not silently drop them — the round gate N=10 itself was set
at cmr's founding and then forgotten by later versions; these tests are
the memory that prevents a second forgetting.

Evidence base: #440 — 34 rounds, 121 fixes (7% original / 58% fix-fix /
23% invention), 2.4× text bloat, majority-complete at round 3 ignored,
and the Step 6 drift triple never fired once (it is structurally blind
to additive-text runaway).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
COMPLETENESS = ROOT / "prompts" / "cmr-completeness.md"


def _norm(txt):
    # prose files hard-wrap at ~72 cols; assertions must not break on a
    # line wrap landing inside the asserted phrase
    return " ".join(txt.split())


def _skill_text():
    return _norm(SKILL.read_text(encoding="utf-8"))


def _doc_mode_section():
    txt = _skill_text()
    start = txt.index("## Doc mode discipline")
    end = txt.index("## Anti-patterns")
    assert start < end, "doc-mode section must precede the anti-patterns list"
    return txt[start:end]


def test_doc_mode_section_exists_and_is_recorded_rule():
    sec = _doc_mode_section()
    assert "RECORDED RULE" in sec, (
        "doc-mode discipline must be marked a recorded rule so a wiki "
        "re-sync does not silently drop it"
    )
    assert "pending wiki upstream" in sec
    assert "NOT drop this section on a wiki re-sync" in sec, (
        "the do-not-drop instruction is the operative half of the marker"
    )


def test_doc_mode_scoped_to_design_text_only():
    sec = _doc_mode_section()
    # doc-mode-only: code-diff mode's existing rules stay untouched
    assert "Code-diff mode keeps every existing rule unchanged" in sec


def test_constitution_kill_axis_and_delete_outranks_patch():
    sec = _doc_mode_section()
    assert "constitution" in sec.lower()
    assert "page one of the review packet" in sec, (
        "the constitution list must land on packet page one, not be an "
        "optional footnote"
    )
    assert (
        "the project's already-decided ADRs + the user's explicitly "
        "stated principles"
    ) in sec, "the constitution's two concrete sources must stay named"
    assert "second mission" in sec
    assert "DELETE" in sec
    assert "outranks a patch finding" in sec, (
        "subtraction must outrank patching, or the lens stays add-only"
    )


def test_fix_classification_ledger_taxonomy():
    sec = _doc_mode_section()
    assert "original-defect / fix-fix / invention" in sec, (
        "the ledger taxonomy is the measuring instrument for every stop "
        "signal — without it nothing below is measurable"
    )
    assert "原始缺陷 / fix修fix / 加戏" in sec
    assert "lands first" in sec, (
        "the ledger is the instrument the other signals read — it must "
        "land before any of them"
    )


def test_bloat_line_is_audit_trigger_not_death_line():
    sec = _doc_mode_section()
    assert "1.5×" in sec
    assert "NOT a death line" in sec, (
        "1.5× must trigger a ledger audit, not an unconditional stop — a "
        "genuinely complex design may lawfully grow"
    )
    # both branches of the audit: legit growth continues, runaway escalates
    assert "original-defect fixes → legitimate" in sec
    assert "fix-fix / invention → STOP, escalate" in sec


def test_early_stop_keeps_full_rereview_no_ap14_exception():
    sec = _doc_mode_section()
    assert "FULL confirmation round" in sec
    assert "no #14 exception" in sec, (
        "the early stop must NOT open a spot-check exception to "
        "anti-pattern #14 — the confirmation round stays a full re-review"
    )
    # the trigger condition and the terminal state, not just the mechanism
    assert "majority of legs judge `complete`" in sec
    assert "zero original-design findings" in sec
    assert "converged, stop" in sec


def test_round_gate_is_10_and_escalates_not_terminates():
    sec = _doc_mode_section()
    assert "round 10" in sec, "the round-gate value is the user's decided 10"
    assert "NOT a hard cap" in sec
    assert "escalate to the user with the ledger + current state" in sec, (
        "reaching the gate must escalate with the ledger AND the current "
        "state, never silently stop or auto-terminate"
    )
    assert "never auto-terminate" in sec
    # the gate is resumable: the user rules both ways
    assert "genuinely complex — continue" in sec
    assert "runaway — close" in sec
    # code mode's no-cap principle must survive alongside the doc gate
    assert "`3 rounds is not a hard cap`" in _skill_text()


def test_dead_leg_standing_degrade():
    sec = _doc_mode_section()
    assert "2 consecutive dead rounds" in sec
    assert "stop re-dispatching" in sec
    assert "standing-DEGRADED" in sec
    assert "in every subsequent round report" in sec, (
        "the standing flag must recur every round, or a silently absent "
        "leg reads as a zero-finding approve"
    )
    assert "re-probe" in sec, (
        "a standing-degraded leg must get one recovery probe at the "
        "escalation checkpoint, not be dropped forever"
    )


def test_self_check_becomes_sanlian():
    sec = _doc_mode_section()
    assert "三连" in sec
    assert "mandatory self-check 二连 with a third check" in sec, (
        "三连 must be defined as extending the existing mandatory 二连, "
        "not replacing it"
    )
    assert "mechanism itself actually hold" in sec
    assert "contradiction with sibling issues" in sec


def test_anti_minutes_fix_discipline():
    sec = _doc_mode_section()
    assert "changes the conclusion" in sec
    assert "decrease-only" in sec
    assert "stated justification in the round report" in sec
    assert "comments or the review ledger" in sec, (
        "argumentation/history needs a licit destination outside the "
        "body, or the append pressure just returns"
    )


def test_completeness_prompt_carries_doc_mode_addendum():
    txt = _norm(COMPLETENESS.read_text(encoding="utf-8"))
    assert "## Doc mode addendum" in txt
    assert "second mission" in txt
    assert "Page one of your dispatch packet" in txt, (
        "the prompt must tell the reviewer where the constitution lives, "
        "or the kill-axis has no ground truth to check against"
    )
    assert "constitution list" in txt
    assert "DELETE" in txt
    assert "outranks a patch finding" in txt
    assert "explicitly licensed to subtract" in txt, (
        "the reviewer must be explicitly licensed to subtract, or the "
        "completeness lens stays structurally add-only"
    )
    # the prompt side of anti-minutes, not just the SKILL side
    assert "Anti-minutes discipline" in txt
    assert "change the conclusion" in txt
    # scoped: code mode skips the addendum
    assert "In code mode this section does not apply" in txt


def test_golden_freeze_of_doc_mode_texts():
    """Exhaustive tail-stop (fix-coverage-drift centralization, round 2).

    Rounds 1-2 each found ANOTHER unpinned sub-phrase — phrase-by-phrase
    pinning is structurally non-exhaustive (a reviewer can always name a
    sixth word). This golden hash freezes the ENTIRE normalized doc-mode
    section and prompt addendum: dropping or rewording ANYTHING fails
    here, even wording no per-element test names. Editing the section is
    still allowed — deliberately: recompute and update the constant in
    the same commit, which is exactly the visible, conscious act the
    RECORDED RULE demands (vs. the silent forgetting that lost N=10).
    Recompute: python3 -c "import hashlib;t=open('SKILL.md').read();n=' '.join(t.split());s=n[n.index('## Doc mode discipline'):n.index('## Anti-patterns')];print(hashlib.sha256(s.encode()).hexdigest())"
    """
    import hashlib

    sec = _doc_mode_section()
    assert hashlib.sha256(sec.encode()).hexdigest() == (
        "e27e9b04c44d1fd31e813c050fdd3f30478d8d9da555bf64edf046e7cc1fcbea"
    ), (
        "SKILL.md doc-mode section text changed — if intentional, update "
        "this hash in the same commit (see docstring); if you did not "
        "edit it, a re-sync just silently mutated the recorded rule"
    )

    txt = _norm(COMPLETENESS.read_text(encoding="utf-8"))
    add = txt[txt.index("## Doc mode addendum") : txt.index("## The gate")]
    assert hashlib.sha256(add.encode()).hexdigest() == (
        "48bd9e6d0e0f5d270cff439f2efbaf84e6158516a987f1bd4dd2389628b7e3d6"
    ), (
        "cmr-completeness.md doc-mode addendum changed — if intentional, "
        "update this hash in the same commit; if not, investigate"
    )


def test_step0_points_at_doc_mode_discipline():
    txt = _skill_text()
    step0 = txt[txt.index("## Step 0") : txt.index("## Step 1")]
    assert "Doc mode discipline" in step0, (
        "Step 0's design-doc bullet must route the reader to the doc-mode "
        "discipline section, or it is undiscoverable at dispatch time"
    )
