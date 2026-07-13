"""Doc-mode discipline must stay pinned across SKILL.md, DOC-MODE.md,
and the completeness lens.

The doc-mode defenses (constitution kill-axis, fix-classification ledger,
bloat audit line, full confirmation-round early stop, round-10 escalation
gate, dead-leg standing degrade, self-check 三连) are a skill-local
RECORDED RULE (user decision 2026-07-06; upstreamed same day). A wiki
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
DOC_MODE = ROOT / "DOC-MODE.md"
COMPLETENESS = ROOT / "prompts" / "cmr-completeness.md"
ADR_0001 = ROOT / "docs" / "adr" / "0001-progressive-disclosure.md"
CONTEXT = ROOT / "CONTEXT.md"
CLAUDE = ROOT / "CLAUDE.md"


def _norm(txt):
    # prose files hard-wrap at ~72 cols; assertions must not break on a
    # line wrap landing inside the asserted phrase
    return " ".join(txt.split())


def _skill_text():
    return _norm(SKILL.read_text(encoding="utf-8"))


def _doc_mode_text():
    return _norm(DOC_MODE.read_text(encoding="utf-8"))


def test_progressive_disclosure_adr_has_authority_map():
    assert ADR_0001.exists()
    adr = _norm(ADR_0001.read_text(encoding="utf-8"))
    assert "规则 → 唯一权威位置映射" in adr
    assert "宿主差异不外置" in adr
    assert "不得另建 `BACKENDS.md`" in adr
    assert "拆分本身产生两个 freeze boundary" in adr


def test_context_glossary_exists():
    assert CONTEXT.exists()
    context = _norm(CONTEXT.read_text(encoding="utf-8"))
    assert "## 域词表" in context
    assert "disclosed file" in context
    assert "`DOC-MODE.md` 是该模式" in context


def test_claude_sync_mapping_covers_disclosed_union():
    claude = _norm(CLAUDE.read_text(encoding="utf-8"))
    assert "转写 = `SKILL.md` + `DOC-MODE.md` 的并集" in claude
    assert "docs/adr/0001-progressive-disclosure.md" in claude


def _doc_mode_section():
    txt = _skill_text()
    start = txt.index("## Doc mode discipline")
    end = txt.index("## Anti-patterns")
    assert start < end, "doc-mode section must precede the anti-patterns list"
    return txt[start:end]


def _external_doc_mode_section():
    return _doc_mode_text()


def test_doc_mode_sections_have_one_owner_each():
    skill = _skill_text()
    doc = _doc_mode_text()
    assert "### ① Constitution packet + kill-axis" in skill
    assert "### ① Constitution packet + kill-axis" not in doc
    for heading in (
        "### ② Fix-classification ledger + stop signals",
        "### ③ Anti-minutes-ification",
        "### ④ Dead-leg standing degrade",
        "### ⑤ Fix self-check becomes 三连",
    ):
        assert heading not in skill
        assert heading in doc


def test_shared_doc_mode_rationale_survives_once_in_external_file():
    skill = _skill_text()
    doc = _doc_mode_text()
    assert doc.count("58% fix-fix") == 1
    assert "58% fix-fix" not in skill
    assert doc.count("are the **root** fixes") == 1
    assert doc.count("are **backstops**") == 1
    assert "are the **root** fixes" not in skill
    assert "are **backstops**" not in skill


def test_doc_mode_section_exists_and_is_recorded_rule():
    skill_sec = _doc_mode_section()
    external_sec = _external_doc_mode_section()
    assert "RECORDED RULE ①" in skill_sec, (
        "the constitution must retain its own recorded-rule boundary"
    )
    assert "RECORDED RULE ②–⑤" in external_sec, (
        "doc-mode discipline must be marked a recorded rule so a wiki "
        "re-sync does not silently drop it"
    )
    assert "upstreamed to the wiki 2026-07-06" in external_sec, (
        "the banner must record that (and when) the upstream landed"
    )
    assert "NOT drop this section on a wiki re-sync" in skill_sec
    assert "NOT drop this section on a wiki re-sync" in external_sec, (
        "the do-not-drop instruction is the operative half of the marker"
    )


def test_doc_mode_scoped_to_design_text_except_constitution():
    sec = _doc_mode_section()
    # 2026-07-12 owner decision: ② -⑤ stay doc-mode-only, but ① (constitution
    # packet + kill-axis) applies to EVERY review mode, code-diff included.
    assert "Code-diff mode keeps every OTHER rule unchanged" in sec
    assert "applies to" in sec and "EVERY review mode" in sec
    assert "ALL modes, not just doc" in sec
    assert "Before round 1 of ANY review" in sec


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
    sec = _external_doc_mode_section()
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
    sec = _external_doc_mode_section()
    assert "1.5×" in sec
    assert "NOT a death line" in sec, (
        "1.5× must trigger a ledger audit, not an unconditional stop — a "
        "genuinely complex design may lawfully grow"
    )
    # both branches of the audit: legit growth continues, runaway escalates
    assert "original-defect fixes → legitimate" in sec
    assert "fix-fix / invention → STOP, escalate" in sec


def test_early_stop_keeps_full_rereview_no_ap14_exception():
    sec = _external_doc_mode_section()
    assert "FULL confirmation round" in sec
    assert "no #14 exception" in sec, (
        "the early stop must NOT open a spot-check exception to "
        "anti-pattern #14 — the confirmation round stays a full re-review"
    )
    # the trigger condition and the terminal state, not just the mechanism
    assert "majority of legs judge `complete`" in sec
    # 0.3.18.0 severity-aware convergence + 0.3.18.9 classification-blind
    # clear gate: the early-stop predicate is "zero BLOCKING findings
    # REGARDLESS of classification" — blocking in doc mode = P0/P1/P2/P3,
    # only P4 exempt. The original-defect/fix-fix/invention split is the
    # ②(b) bloat-audit trigger ONLY; it must NOT filter what counts toward
    # the clear/convergence gate (a dissenting leg's fix-fix/invention
    # blocking finding must still block).
    assert "zero blocking (P0/P1/P2/P3) findings regardless of classification" in sec, (
        "the early-stop predicate must count ALL blocking findings by "
        "severity (P0/P1/P2/P3), not filter to the original-defect "
        "classification"
    )
    # negative: the classification-FILTERED clear check must be gone — a
    # fix-fix/invention blocking finding was silently excluded before
    assert "zero blocking (P0/P1/P2/P3) original-defect findings" not in sec, (
        "the clear/convergence gate must NOT filter blocking findings to "
        "the original-defect classification — all classifications count"
    )
    # the split survives, but only as ②(b)'s bloat-audit trigger, never the gate
    assert "never for filtering the clear/convergence gate" in sec, (
        "the ledger explicitly says classification does not filter the gate"
    )
    assert "only P4 exempt" in sec, (
        "doc mode blocks P0-P3; only P4 (clarity) is exempt and "
        "reported-but-Deferred — the exemption must be pinned"
    )
    assert "original-design" not in sec, (
        "unified vocabulary: the taxonomy key is original-defect; no "
        "synonym drift"
    )
    assert "converged, stop" in sec
    # the TERMINAL condition must carry the SAME blocker-free predicate as
    # the trigger — "again majority-complete" alone would let a
    # confirmation round converge while swallowing a fresh original-defect
    # finding raised by the dissenting leg (cmr correctness P1, 2026-07-06)
    terminal = sec[
        sec.index("Confirmation round again majority-complete")
        : sec.index("converged, stop")
    ]
    assert "zero blocking (P0/P1/P2/P3) findings regardless of classification" in terminal, (
        "the confirmation round's convergence must require zero blocking "
        "findings (any classification) again, not bare majority-complete"
    )
    assert "zero blocking (P0/P1/P2/P3) original-defect findings" not in terminal, (
        "the confirmation-round clear gate must not filter by classification"
    )


def test_round_gate_is_10_and_escalates_not_terminates():
    sec = _external_doc_mode_section()
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
    sec = _external_doc_mode_section()
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
    sec = _external_doc_mode_section()
    assert "三连" in sec
    assert "mandatory self-check 二连 with a third check" in sec, (
        "三连 must be defined as extending the existing mandatory 二连, "
        "not replacing it"
    )
    assert "mechanism itself actually hold" in sec
    assert "contradiction with sibling issues" in sec


def test_anti_minutes_fix_discipline():
    sec = _external_doc_mode_section()
    assert "changes the conclusion" in sec
    assert "decrease-only" in sec
    assert "stated justification in the round report" in sec
    assert "comments or the review ledger" in sec, (
        "argumentation/history needs a licit destination outside the "
        "body, or the append pressure just returns"
    )


def test_completeness_prompt_carries_doc_mode_addendum():
    txt = _norm(COMPLETENESS.read_text(encoding="utf-8"))
    assert "## Doc mode addendum + constitution check (ALL modes)" in txt
    assert "## Doc mode addendum (ONLY" not in txt
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
    assert "Constitution check + kill-axis applies in **every review mode**" in txt
    assert (
        "In code mode, skip only this doc-mode-specific ②–⑤ / anti-minutes "
        "discipline; the constitution check + kill-axis still applies."
    ) in txt
    assert "In code mode this section does not apply" not in txt


def test_fixer_uses_mode_conditional_self_check_at_both_fix_sites():
    txt = _norm((ROOT / "prompts" / "cmr-fixer.md").read_text(encoding="utf-8"))
    contract = (
        "mode-conditional self-check: `fixer_mode: code` = 二连; "
        "`fixer_mode: doc` = 三连 per `DOC-MODE.md` ⑤"
    )
    assert txt.count(contract) == 2


def test_wiki_wins_contract_carries_recorded_rule_exception():
    """The unconditional wiki-wins contract contradicted the RECORDED RULE
    do-not-drop blocks (cmr correctness r2 P1): a re-sync operator had two
    incompatible instructions. The contract sentence in BOTH surfaces must
    carry the recorded-rule exception."""
    skill = _skill_text()
    start = skill.index("the wiki wins")
    contract = skill[start : start + 400]
    assert "RECORDED" in contract, (
        "SKILL.md's wiki-wins sentence must state the RECORDED RULE "
        "exception, or re-sync has two incompatible instructions"
    )
    readme = _norm((ROOT / "README.md").read_text(encoding="utf-8"))
    rstart = readme.index("the wiki wins")
    assert "RECORDED" in readme[rstart : rstart + 400], (
        "README's wiki-wins sentence must state the same exception"
    )


def test_no_stale_pending_upstream_claims():
    """The doc-mode discipline + 15min hang rule WERE upstreamed to the
    wiki on 2026-07-06 (vault b5495e8 / da04ff5 / e06bcfe). Claims that
    the wiki 'still says 8min' or that upstream is 'pending' are now
    false statements and must not survive in SKILL.md or the backend."""
    skill = _skill_text()
    assert "pending wiki upstream" not in skill, (
        "stale: the upstream landed 2026-07-06 — say 'upstreamed', don't "
        "claim pending"
    )
    assert "still says 8min" not in skill
    backend = _norm(
        (ROOT / "backends" / "codex-review.sh").read_text(encoding="utf-8")
    )
    assert "still says 8min" not in backend
    assert "pending wiki upstream" not in backend
    assert "pending upstream" not in backend
    # r3 residue (same class, new surface — centralize the scan): the
    # sibling test file's comments and the CHANGELOG heading must not
    # keep the divergence alive either
    sibling = _norm(
        (ROOT / "tests" / "test_codex_review.py").read_text(encoding="utf-8")
    )
    assert "still says 8min" not in sibling
    changelog = _norm((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    assert "recorded wiki divergence" not in changelog, (
        "the 0.3.15.1 heading must not call it a live divergence — the "
        "wiki was updated the same day (in sync)"
    )
    # the do-not-drop guard itself STAYS (it protects against a re-sync
    # from a stale wiki checkout; the golden hash enforces it)
    assert "NOT drop this section on a wiki re-sync" in skill
    assert "NOT drop this section on a wiki re-sync" in _doc_mode_text()


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
    Recompute SKILL.md: python3 -c "import hashlib;t=open('SKILL.md').read();n=' '.join(t.split());s=n[n.index('## Doc mode discipline'):n.index('## Anti-patterns')];print(hashlib.sha256(s.encode()).hexdigest())"
    Recompute DOC-MODE.md: python3 -c "import hashlib;t=open('DOC-MODE.md').read();n=' '.join(t.split());print(hashlib.sha256(n.encode()).hexdigest())"
    """
    import hashlib

    skill_sec = _doc_mode_section()
    assert hashlib.sha256(skill_sec.encode()).hexdigest() == (
        "f0c27d0e6604974e77260fbac014d3e09751aa55e34b14ba1ecaa533ce7df748"
    ), (
        "SKILL.md doc-mode section text changed — if intentional, update "
        "this hash in the same commit (see docstring); if you did not "
        "edit it, a re-sync just silently mutated the recorded rule"
    )

    external_sec = _external_doc_mode_section()
    assert hashlib.sha256(external_sec.encode()).hexdigest() == (
        "5bfd84837596a4257fc50cc43a953b8bda86cb08530d68c48e6d5b905e4436a5"
    ), (
        "DOC-MODE.md text changed — if intentional, update this hash in "
        "the same commit; if not, investigate"
    )

    txt = _norm(COMPLETENESS.read_text(encoding="utf-8"))
    add = txt[txt.index("## Doc mode addendum") : txt.index("## The gate")]
    assert hashlib.sha256(add.encode()).hexdigest() == (
        "a4ae3926a81152c859fa6178ead818721099756d8bf9bd865555720c56f72e79"
    ), (
        "cmr-completeness.md doc-mode addendum changed — if intentional, "
        "update this hash in the same commit; if not, investigate"
    )


def test_step0_points_at_doc_mode_discipline():
    txt = _skill_text()
    step0 = txt[txt.index("## Step 0") : txt.index("## Step 1")]
    assert "review 对象是 ADR/spec/plan → 先 Read `DOC-MODE.md` 再派单" in step0, (
        "Step 0's design-doc bullet must give a hard read-before-dispatch "
        "instruction for DOC-MODE.md"
    )
    assert (
        "constitution kill-axis (① below); fix-classification ledger, "
        "bloat audit line, full confirmation-round early stop, round-10 "
        "escalation gate (②–⑤ in `DOC-MODE.md`)"
    ) in step0, (
        "Step 0's completeness list must keep ① below and route externalized "
        "②–⑤ to DOC-MODE.md"
    )
