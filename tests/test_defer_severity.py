"""P2/medium is BLOCKING and the terminal-outcome logic lives in ONE place
(0.3.18.1 → consolidated 0.3.18.21).

0.3.18.0 made P2 a blocking severity (a round is CLEAR only with no
P0/P1/P2; doc mode no P0/P1/P2/P3). But the fixer/defer protocol still
listed medium/P2 as deferrable ("SHOULD fix ... may defer"), so a fixer
could legitimately defer a P2 that still blocks convergence → the next
full round re-finds it → the loop never terminates. The first pins here
fixed the tiers: deferrable = the NON-blocking set (P3/P4 in
correctness/code mode, P4 only in doc mode); a blocking finding is
must-fix-or-route, NEVER deferred.

Then 0.3.18.16 → .20 each patched ONE site that stated an incomplete
version of "what are the valid terminal outcomes for a finding" — the
First-duty overview, the Scope-rules routing tail, the Defer-protocol
closing paragraph, the JSON claim_quote instruction. Same rule-class,
new site each round = coverage drift. 0.3.18.21 (per the wiki Step-6
"coverage drift ≠ architectural drift" doctrine) consolidates the concept
into ONE authoritative `## Terminal outcomes` section that exhaustively
enumerates every valid exit for a supplied finding — FALSE (any severity),
REAL-blocking (fixed OR routed), REAL-non-blocking (fixed OR deferred) —
with the claim_quote-not-found case folded in as a NAMED blocking-route
reason rather than a free-floating unblessed 4th path. Every OTHER site is
now a pointer, not an independent restatement.

Pins below: (1) SKILL.md tier pins (unchanged); (2) Scope-rules
classification pins (WHICH findings are fixable); (3) the single
Terminal-outcomes section owns the exit enumeration; (4) the six
(FALSE/REAL)×(blocking/non-blocking)×(locatable/not) input traces each
resolve to exactly one exit; (5) negative pins that NO stray restatement
of terminal-outcome logic survives outside the single section.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
FIXER = ROOT / "prompts" / "cmr-fixer.md"


def _norm(path):
    # prose files hard-wrap at ~72 cols; assertions must not break on a
    # line wrap landing inside the asserted phrase
    return " ".join(path.read_text(encoding="utf-8").split())


def _section(name):
    """Normalized text of the `## <name> ...` section only — from its h2
    heading to the next h2 (or EOF). Lets a pin assert a phrase lives IN
    the single consolidated section and is absent from the others."""
    raw = FIXER.read_text(encoding="utf-8")
    out, capturing = [], False
    for ln in raw.splitlines():
        if ln.startswith("## "):
            if capturing:
                break
            capturing = ln[3:].strip().startswith(name)
            continue
        if capturing:
            out.append(ln)
    assert out, f"section '## {name}' not found in cmr-fixer.md"
    return " ".join(" ".join(out).split())


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


# --- cmr-fixer.md Scope rules: which findings are fixable (classification,
# --- NOT terminal routing — that lives in ## Terminal outcomes) ---


def test_fixer_medium_is_blocking_must_fix():
    sc = _section("Scope rules")
    assert "**and every `medium`** finding" in sc, (
        "medium must join critical/high in the MUST-fix (blocking) bullet"
    )
    assert (
        "`medium`/P2 carries the **same obligation as `critical`/`high`**"
    ) in sc, "medium must carry the same must-fix obligation as critical/high"
    assert "in doc mode, every `low` as well" in sc, (
        "doc mode also blocks low/P3 — the fixer must fix it, not defer it"
    )
    # the P2->P3 escape hatch is closed, mirroring the critical/high->medium ban
    assert (
        "never a real `medium` to `low` — P2→P3 is the same escape hatch "
        "and is closed"
    ) in sc, (
        "down-ranking a real medium to low to escape must be banned, "
        "mirroring the critical/high->medium ban"
    )


def test_fixer_scope_defines_unfixable_blocking_and_points_at_terminal():
    sc = _section("Scope rules")
    # Scope names the unfixable-blocking classification (WHICH), then points
    # at Terminal outcomes for WHERE it goes (route + reason strings).
    assert "A blocking finding you **cannot mechanically resolve**" in sc, (
        "Scope must classify the unfixable-blocking case (non-trivial OR "
        "MUST-NOT-fix-blocked)"
    )
    assert (
        "one that is mechanical by classification but blocked by a "
        "**MUST-NOT-fix condition** below"
    ) in sc, (
        "Scope must name the mechanical-but-MUST-NOT-fix case — the round-5 "
        "three-way trap — as an unfixable-blocking classification"
    )
    assert (
        "its `suggested_fix` is `n/a`/empty, reviewers disagree on the "
        "correction, or a real fix would require inventing new "
        "behavior/content"
    ) in sc, (
        "all three MUST-NOT-fix conditions must be named so the trap is "
        "closed for disagreement / new-content too, not only empty-fix"
    )
    # Scope POINTS at Terminal outcomes — it does not re-derive the route.
    assert "**Terminal outcomes** is the single authority on that route" in sc, (
        "Scope's routing language must point at the single Terminal-outcomes "
        "section, not re-derive the route inline"
    )


def test_fixer_clarity_not_unconditionally_fix_banned():
    sc = _section("Scope rules")
    # the MUST-NOT-fix list is declared severity-blind, and a clarity finding
    # with a concrete fix / no disagreement / no new content is fix-eligible
    assert "This list is **severity-blind**" in sc, (
        "the MUST-NOT-fix list must be marked severity-blind — being "
        "clarity severity is not by itself a fix-ban"
    )
    assert (
        "A `clarity` finding that HAS a concrete `suggested_fix`, has no "
        "reviewer disagreement, and needs no new-content invention is "
        "fix-eligible under the SHOULD-fix-by-default rule above"
    ) in sc, (
        "a mechanically-fixable clarity finding must be stated as "
        "fix-eligible, matching SKILL.md's cheap/low-risk P3/P4 SHOULD-fix"
    )


def test_fixer_should_fix_bullet_names_clarity_for_code_mode():
    sc = _section("Scope rules")
    # the SHOULD-fix set names the full code-mode non-blocking tier
    assert (
        "the defer-eligible `low`/`clarity` findings (correctness/code mode; "
        "in **doc mode `low` is blocking**, see above, so only `clarity` is "
        "defer-eligible there)"
    ) in sc, (
        "the SHOULD-fix bullet must name low AND clarity for code mode "
        "(doc mode: only clarity)"
    )
    # the follow-up drift clause covers the whole non-blocking tier
    assert (
        "If fixing these non-blocking findings keeps surfacing **new** "
        "findings (drift)"
    ) in sc, (
        "the drift stop-condition must cover the whole non-blocking tier "
        "(low + clarity), not only 'the lows'"
    )


# --- cmr-fixer.md Defer protocol: the non-blocking branch's structured
# --- deferral (three parts), keyed off low/clarity only ---


def test_fixer_deferrable_set_is_low_clarity_only():
    df = _section("Defer protocol")
    assert (
        "Any `low`/`clarity` finding you do not fix MUST become a structured "
        "deferral"
    ) in df, (
        "the structured-deferral obligation must key off low/clarity, not "
        "the old medium/low/clarity set"
    )
    assert "doc mode: `clarity` only" in df, (
        "doc mode's deferrable set is clarity only (low/P3 blocks there)"
    )


# --- cmr-fixer.md: the SINGLE ## Terminal outcomes section owns the whole
# --- enumeration of valid exits for a supplied finding (0.3.18.21) ---


def test_terminal_outcomes_section_is_the_single_authority():
    ts = _section("Terminal outcomes")
    assert "the **one** authority on *where an adjudicated finding goes*" in ts, (
        "the Terminal-outcomes section must declare itself the single "
        "authority on where a finding goes"
    )


def test_terminal_false_is_valid_resolution_any_severity_before_branch():
    ts = _section("Terminal outcomes")
    assert (
        "**FALSE — any severity.** A finding you adjudicate FALSE against "
        "the actual source, with the refuting evidence recorded in an "
        "`adjudications` entry, is **itself a complete, valid resolution**"
    ) in ts, (
        "outcome 1 must recognize a FALSE-adjudicated finding as a complete "
        "valid resolution, not a silent drop"
    )
    assert (
        "It resolves **before** any severity branch, since a finding can be "
        "judged FALSE whether it was labelled blocking or non-blocking."
    ) in ts, (
        "FALSE must resolve BEFORE the tier branch and apply at ANY severity"
    )
    assert (
        "Only a finding adjudicated **REAL** proceeds to the two branches "
        "below."
    ) in ts, "only REAL findings may reach the blocking/non-blocking branches"


def test_terminal_real_blocking_is_fixed_or_routed_with_three_reasons():
    ts = _section("Terminal outcomes")
    assert (
        "**REAL, blocking** (`critical`/`high`/`medium` = P0/P1/P2; **doc "
        "mode also `low`/P3**) → **fixed** OR **routed**, never deferred"
    ) in ts, (
        "the blocking branch's valid exits are fixed OR routed (never "
        "deferred)"
    )
    assert "Routing **is a resolution, not a protocol violation**." in ts, (
        "routing a blocking finding via fixes_skipped must be declared a "
        "resolution, NOT a protocol violation"
    )
    # all three routed-reason strings, including the folded-in claim_quote case
    assert "`non-trivial → main-session /diagnosing-bugs`" in ts, (
        "the non-trivial-by-nature routed reason must be enumerated here"
    )
    assert (
        "`blocking-but-unfixable → main-session /diagnosing-bugs "
        "(no safe suggested_fix)`"
    ) in ts, (
        "the MUST-NOT-fix-blocked routed reason must be enumerated here, "
        "distinct from the behavioral-complexity one"
    )
    assert (
        "`claim_quote not found → main-session /diagnosing-bugs "
        "(needs verification)`"
    ) in ts, (
        "claim_quote-not-found must be folded in as a NAMED blocking-route "
        "reason, not a free-floating unblessed 4th outcome"
    )


def test_terminal_real_non_blocking_is_fixed_or_deferred_never_routed():
    ts = _section("Terminal outcomes")
    assert (
        "**REAL, non-blocking** (`low`/`clarity` in correctness/code mode; "
        "**doc mode: `clarity` only**, since `low`/P3 is blocking there) → "
        "**fixed** OR **deferred**, never routed."
    ) in ts, (
        "the non-blocking branch's valid exits are fixed OR deferred (never "
        "routed — no /diagnosing-bugs hand-back for non-blocking work)"
    )
    # a non-blocking finding whose claim_quote can't be located is adjudicated
    # FALSE (outcome 1), NOT parked in a bare fixes_skipped
    assert (
        "that inability is itself grounds to adjudicate it **FALSE** "
        "(outcome 1"
    ) in ts, (
        "an unlocatable claim on a NON-blocking finding routes to a FALSE "
        "adjudication, not a stray park"
    )
    assert "never silently park it." in ts


def test_terminal_violation_clause_scoped_to_real_silent_drops_only():
    ts = _section("Terminal outcomes")
    assert (
        "The **only** protocol violation is a **REAL** finding that reaches "
        "**none** of the outcomes above"
    ) in ts, (
        "the violation must be redefined as a REAL finding reaching NONE of "
        "its outcomes (a silent drop), not the tier-blind 'neither fixed nor "
        "deferred'"
    )
    assert (
        "a REAL non-blocking finding silently dropped, or a REAL blocking "
        "finding silently dropped."
    ) in ts, (
        "the silent-drop set must be scoped to REAL findings, since a FALSE "
        "verdict is a resolution"
    )
    assert (
        "A FALSE adjudication is a resolution, **not** among the drops."
    ) in ts, "a FALSE adjudication must be explicitly excluded from the drops"


# --- cmr-fixer.md: the six (FALSE/REAL)×(blocking/non-blocking)×(locatable/
# --- not) input traces each resolve to exactly one exit in the section ---


def test_six_input_traces_each_resolve_cleanly():
    ts = _section("Terminal outcomes")
    # (a) FALSE at blocking severity + (b) FALSE at non-blocking severity →
    # outcome 1, which is severity-independent and resolves before the branch
    assert (
        "**FALSE — any severity.**" in ts
        and "whether it was labelled blocking or non-blocking" in ts
    ), "(a)/(b) FALSE at any severity must resolve via outcome 1"
    # (c) REAL blocking mechanical → fixed here
    assert "**fixed** here when it is mechanical per the Scope header." in ts, (
        "(c) REAL blocking mechanical must resolve to a fix here"
    )
    # (d) REAL blocking non-trivial → routed, non-trivial reason
    assert (
        "`non-trivial → main-session /diagnosing-bugs` — non-trivial by "
        "nature"
    ) in ts, "(d) REAL blocking non-trivial must resolve to the non-trivial route"
    # (e) REAL non-blocking cheap → fixed by default
    assert (
        "**fixed** — the default for cheap, low-risk findings "
        "(SHOULD-fix-by-default"
    ) in ts, "(e) REAL non-blocking cheap must resolve to a default fix"
    # (f) REAL non-blocking with claim_quote unlocatable → FALSE adjudication
    assert (
        "If you genuinely cannot locate a non-blocking finding's "
        "`claim_quote`, verify it yourself if you can and fix/defer normally; "
        "if you truly cannot verify it, that inability is itself grounds to "
        "adjudicate it **FALSE** (outcome 1"
    ) in ts, (
        "(f) REAL non-blocking with unlocatable claim_quote must resolve to "
        "a FALSE adjudication, not a park"
    )


# --- cmr-fixer.md: NO stray restatement of terminal-outcome logic survives
# --- outside the single ## Terminal outcomes section (0.3.18.21) ---


def test_terminal_enumeration_lives_only_in_the_one_section():
    # the exit enumeration ("fixed OR routed") must NOT be independently
    # restated in Scope rules or Defer protocol — those sections point at it
    assert "**fixed** OR **routed**" not in _section("Scope rules"), (
        "the fixed-OR-routed enumeration must not be re-derived in Scope"
    )
    assert "**fixed** OR **routed**" not in _section("Defer protocol"), (
        "the fixed-OR-routed enumeration must not be re-derived in Defer"
    )
    # the routed reason strings are owned by Terminal outcomes; Scope/Defer
    # only reference the route, they do not restate the reason strings
    for section in ("Scope rules", "Defer protocol"):
        body = _section(section)
        assert "blocking-but-unfixable →" not in body, (
            f"the routed reason strings must not be restated in {section}"
        )
        assert "`non-trivial → main-session /diagnosing-bugs`" not in body, (
            f"the routed reason strings must not be restated in {section}"
        )


def test_no_free_floating_claim_quote_bare_fixes_skipped_wording_negative():
    full = _norm(FIXER)
    # the old free-floating "add it to fixes_skipped with reason
    # 'claim_quote not found'" — unqualified by the terminal-outcomes
    # framework — must be gone; claim_quote-not-found is now a NAMED reason
    # under the blocking route (or a FALSE adjudication for non-blocking).
    assert 'with reason `"claim_quote not found"`' not in full, (
        "the old bare 'fixes_skipped with reason `\"claim_quote not found\"`' "
        "wording must be gone — it was an unblessed 4th outcome"
    )
    assert '`"claim_quote not found"`' not in full, (
        "the old quoted bare `\"claim_quote not found\"` reason literal must "
        "be gone — replaced by the terminal-outcomes-framed reason string"
    )


def test_old_scattered_terminal_restatements_are_gone_negative():
    full = _norm(FIXER)
    # the old tier-blind closing sentence (0.3.18.19 target)
    assert (
        "A finding that is neither fixed nor deferred-with-all-three-parts "
        "is a protocol violation"
    ) not in full, "the old tier-blind 'neither fixed nor deferred' must be gone"
    # the old un-REAL-qualified drop set (0.3.18.20 target)
    assert (
        "a non-blocking finding silently dropped (no fix, no structured "
        "deferral), or a blocking finding silently dropped (no fix, no "
        "route)"
    ) not in full, "the old drop set without a REAL qualifier must be gone"
    # the old First-duty inline REAL-route assertion (now a pointer)
    assert (
        "a non-trivial one is routed to the main session's `/diagnosing-bugs` "
        "per the Scope rules below"
    ) not in full, (
        "the First-duty REAL bullet must point at Terminal outcomes, not "
        "assert the route inline"
    )
    # the old intro summary line that implied ALL non-trivial route
    assert (
        "non-trivial → main session `/diagnosing-bugs`; lower-priority → "
        "defer protocol"
    ) not in full, "the old intro summary restatement must be gone"
    # the old low-only SHOULD-fix body and the pre-0.3.18.18 non-trivial-only
    # routing scope
    assert "the defer-eligible `low` findings (correctness/code mode" not in full
    assert "If fixing the lows keeps surfacing" not in full
    assert "A blocking finding that is **non-trivial** is NOT yours" not in full


def test_fixer_drops_medium_deferrable_wording_negative():
    full = _norm(FIXER)
    assert "`medium`/`low`/`clarity`" not in full, (
        "the old 'any medium/low/clarity finding ... structured deferral' "
        "set must be gone — medium is blocking"
    )
    assert "`medium` / `low` findings that are cheap" not in full, (
        "the old 'SHOULD fix by default: medium/low' deferrable framing "
        "must be gone"
    )
    assert "P2/P3/P4" not in full, "no P2/P3/P4-deferrable wording in the fixer"


def test_fixer_drops_blanket_clarity_fix_ban_negative():
    full = _norm(FIXER)
    assert "`clarity` findings (author judgment);" not in full, (
        "the standalone '`clarity` findings (author judgment)' MUST-NOT-fix "
        "bullet must be gone — it contradicted the SHOULD-fix-by-default rule"
    )


# --- cmr-fixer.md: the `deferred[]` schema severity is a pipe-delimited enum
# --- representing the full legal set (low|clarity) (0.3.18.20) ---


def test_fixer_deferred_severity_enum_includes_clarity():
    full = _norm(FIXER)
    assert '"severity": "low|clarity"' in full, (
        "deferred[].severity must be a pipe-delimited enum (low|clarity), "
        "matching the prose's doc-mode clarity deferral and the other "
        "severity fields' enum syntax"
    )
    assert '"severity": "low",' not in full, (
        "the old single-literal deferred[].severity `\"low\"` must be gone — "
        "it could not represent a legal doc-mode `clarity` deferral"
    )
