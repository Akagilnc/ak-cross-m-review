"""The review submission contract (交卷契约, ADR 0130) must stay pinned.

User ratification 2026-07-12; wiki §额外硬规则 #8. Three semantics:

1. A review leg reports ALL findings it sees within one round — severity
   is a PROPERTY of a finding, not an admission threshold for whether to
   report it; delivery is complete only when every finding is written down
   ("dig up one or two nail-able ones and knock off" is no longer valid).
2. The fixer's FIRST duty = empirically adjudicate each supplied finding
   one by one: REAL → fix + same-class sweep; FALSE → reject WITH EVIDENCE
   recorded in the structured `adjudications` field for the next fresh
   reviewer; other real defects seen in passing → surface as a separate
   `incidental_fixes` patch (main session commits it) + report loudly.
3. Applies to ALL review modes; "report all" means FINDINGS, not "suggest
   adding text"; doc-mode ②–⑤ anti-runaway discipline is unaffected;
   progressive exposure (holes visible only after a fix) is NOT a failure.

These are phrase pins (positive + negative counterpart each), so a wiki
re-sync that softens the contract back to "report a couple" fails here.
Evidence base: #860 — 21+ serial rounds whose root cause was the missing
submission contract (no shaping language, legs self-collected after 2-3).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWER = ROOT / "prompts" / "cmr-reviewer.md"
COMPLETENESS = ROOT / "prompts" / "cmr-completeness.md"
FIXER = ROOT / "prompts" / "cmr-fixer.md"
SKILL = ROOT / "SKILL.md"


def _norm(path):
    # prose files hard-wrap at ~72 cols; assertions must not break on a
    # line wrap landing inside the asserted phrase
    return " ".join(path.read_text(encoding="utf-8").split())


# --- semantics 1 + 3: the reviewer (correctness lens) reports every finding


def test_reviewer_reports_every_finding_positive():
    txt = _norm(REVIEWER)
    assert "## Submission contract" in txt, (
        "the correctness reviewer must carry the 交卷契约 section, or the "
        "leg can still self-collect after two nail-able findings"
    )
    assert "ADR 0130" in txt, "the contract must cite its ratifying ADR"
    assert "Report **every** finding you see this round" in txt, (
        "semantics 1: report ALL findings, positively phrased"
    )
    assert "Severity is a label you attach to a finding" in txt, (
        "severity must be framed as a property/label, not a gate"
    )
    assert "not a threshold it must clear before it is worth reporting" in txt, (
        "the severity-is-not-an-admission-gate clause must be explicit"
    )
    assert "delivered only once every defect you saw is written down" in txt, (
        "delivery-complete-only-when-all-reported is the whole point"
    )


def test_reviewer_report_all_means_findings_not_padding_positive():
    txt = _norm(REVIEWER)
    # semantics 3: applies to all modes; "report all" = findings not text;
    # doc-mode anti-runaway unaffected; progressive exposure is not a breach
    assert "every review mode" in txt
    assert 'means the *findings* you actually see' in txt, (
        "'report all' must be scoped to findings, never to adding text"
    )
    assert (
        "②–⑤ anti-runaway discipline (now in DOC-MODE.md, "
        "dispatcher/orchestrator-side) is untouched"
    ) in txt, (
        "doc-mode anti-runaway discipline must be anchored to DOC-MODE.md"
    )
    assert "Progressive exposure" in txt
    assert "it is not a contract breach" in txt, (
        "progressive exposure must be excused as not-a-breach"
    )


def test_reviewer_contract_is_positive_not_negative_framing():
    # negative counterparts: the task forbids "不要只报一条"-style negative
    # framing — assert the anti-patterns are ABSENT (proves positive phrasing)
    txt = _norm(REVIEWER).lower()
    assert "不要只报" not in txt, "must state the target, not a 不要-prohibition"
    assert "don't just report" not in txt
    assert "only report critical" not in txt, (
        "severity must never be framed as a reporting gate"
    )
    assert "only the findings worth" not in txt
    # correctness lens must not borrow the completeness taxonomy token
    assert "unverified-gap" not in txt


# --- semantics 1 + 3: the completeness lens reports every gap


def test_completeness_reports_every_gap_positive():
    txt = _norm(COMPLETENESS)
    assert "## Submission contract" in txt, (
        "the completeness auditor must carry the 交卷契约 section too"
    )
    assert "ADR 0130" in txt
    assert "Report **every** gap you find this round" in txt, (
        "semantics 1 for the completeness lens: report ALL gaps"
    )
    assert (
        "The verdict (NOT-DONE / PARTIAL / VIOLATES / UNVERIFIED-GAP) is a "
        "label you attach to a gap"
    ) in txt, "the verdict must be framed as a label, not a reporting bar"
    assert "not a bar it must clear before it is worth reporting" in txt
    assert "delivered only once every gap you saw is written down" in txt


def test_completeness_report_all_means_gaps_not_padding_positive():
    txt = _norm(COMPLETENESS)
    assert "every review mode" in txt
    assert "means the *gaps* you actually find" in txt, (
        "'report all' must be scoped to gaps, not to padding the design"
    )
    assert (
        "②–⑤ anti-runaway discipline (now in DOC-MODE.md, "
        "dispatcher/orchestrator-side) is untouched"
    ) in txt, (
        "the doc-mode anti-runaway discipline must be anchored to DOC-MODE.md"
    )
    assert "Progressive exposure" in txt


def test_completeness_contract_is_positive_not_negative_framing():
    txt = _norm(COMPLETENESS).lower()
    assert "不要只报" not in txt
    assert "don't just report" not in txt
    assert "suggest padding the design with extra text" in txt, (
        "the anti-pattern named is 'suggest adding text' — kept as the "
        "thing 'report all' is NOT a licence for"
    )
    assert "only the gaps worth" not in txt


def test_contract_placed_before_completeness_doc_mode_addendum():
    # the completeness doc-mode addendum is golden-hashed in test_doc_mode;
    # the contract must sit BEFORE it so that hash slice is untouched
    txt = _norm(COMPLETENESS)
    assert txt.index("## Submission contract") < txt.index(
        "## Doc mode addendum"
    ), (
        "the contract section must precede the golden-hashed doc-mode "
        "addendum, or the addendum hash would need recomputing"
    )


# --- semantics 2: the fixer's first duty = empirical adjudication


def test_fixer_first_duty_adjudicates_each_finding_positive():
    txt = _norm(FIXER)
    assert "## First duty" in txt and "交卷契约" in txt, (
        "the fixer must carry the first-duty adjudication section"
    )
    assert "ADR 0130" in txt
    assert "adjudicate each against the actual source" in txt, (
        "semantics 2: empirically adjudicate each finding one by one"
    )
    # REAL → fix + same-class sweep (Concept sweep / EXAM-818 doctrine)
    assert "**REAL**" in txt
    assert "run the same-class sweep" in txt, (
        "a REAL finding must trigger the same-class sweep"
    )
    assert "**Concept sweep** doctrine below" in txt and "is unchanged" in txt, (
        "the existing EXAM-818/Concept-sweep doctrine must be cited as "
        "unchanged, not rewritten"
    )
    # FALSE → reject WITH EVIDENCE, recorded in the structured
    # `adjudications` field (NOT a vague "summary"), adjudicated next round
    assert "**FALSE**" in txt
    assert "reject it **with evidence**, recorded as a structured" in txt
    assert "`adjudications` entry" in txt
    assert (
        "so the next round's fresh reviewer can adjudicate the rejection"
        in txt
    )
    # negative: the old vague "written into your summary" sink is GONE — a
    # FALSE verdict now lands in a structured field, not free-text summary
    assert "written into your summary" not in txt, (
        "the FALSE adjudication must point at the structured `adjudications` "
        "field, not a vague summary with no schema slot"
    )
    # other real defects seen in passing → surface as a SEPARATE patch +
    # report loudly; the MAIN SESSION commits it (the subagent has no commit)
    assert "Other real defects you see in passing" in txt
    assert "surface each as its **own** `incidental_fixes` entry" in txt, (
        "an incidental defect must be surfaced as its own separate-patch "
        "entry, not folded into the supplied-finding diff"
    )
    assert (
        "a **separate** unified diff (never merged into the "
        "supplied-finding `diff`)"
    ) in txt, "the incidental patch must be physically separate"
    assert "**report them loudly**" in txt
    assert (
        "the **main session** lands each `incidental_fixes` entry as an "
        "independent commit"
    ) in txt, (
        "the independent commit is a MAIN-SESSION action — the subagent has "
        "no commit of its own"
    )
    # non-trivial incidental defect → report only, route to main session
    assert "reported_defects" in txt, (
        "a non-trivial incidental defect is reported, not risk-patched"
    )


def test_fixer_incidental_fix_is_separate_patch_not_subagent_commit():
    """The incidental-defect clause must be representable AND correctly
    leveled: a separate `incidental_fixes` patch surfaced by the subagent,
    committed by the MAIN SESSION — never a git commit run by the subagent.

    Regression pin for the codex round-2 outside-voice P2: the prompt used
    to tell the subagent to "commit it independently", but its only output
    is one strict-JSON response with a single unified diff — it has no
    commit mechanism, so the instruction was impossible to satisfy.
    """
    full = _norm(FIXER)
    low = full.lower()
    # the output schema must carry the dedicated incidental-fix field...
    assert '"incidental_fixes"' in full, (
        "the fixer output schema must expose an incidental_fixes array so "
        "an in-passing defect is representable without polluting the "
        "supplied-finding diff"
    )
    # ...each entry a separate self-contained diff with rationale + severity
    assert (
        "its OWN separate unified diff" in full
        and "NEVER merged into the supplied-finding `diff`" in full
    ), "each incidental_fixes entry must be its own separate patch"
    # negative pin: the old subagent-commits-it instruction must be GONE
    assert "committed independently" not in low, (
        "the subagent has no commit; 'committed independently' assigned an "
        "orchestration-level action to the subagent — must be removed"
    )
    assert "commit it independently" not in low
    assert "small-fix them, committed" not in low


def test_fixer_first_duty_no_scope_restriction_negative():
    # negative counterparts: the "in-scope only / only fix what you were
    # given" language would contradict "other real defects → small-fix +
    # report loudly"; it must NOT be present
    txt = _norm(FIXER).lower()
    assert "in-scope only" not in txt
    assert "only fix what you were given" not in txt
    assert "ignore other" not in txt
    assert "outside your assigned scope" not in txt
    # the Concept-sweep doctrine (EXAM-818) must survive verbatim
    full = _norm(FIXER)
    assert "Concept sweep (fix every occurrence, not just the first)" in full, (
        "the EXAM-818 sweep doctrine header must stay verbatim"
    )


def test_fixer_mechanical_repetition_exception_is_pinned_at_scope_and_sweep():
    txt = _norm(FIXER)
    clause = (
        "Verbatim-identical, provably-inert repetitions of the SAME mechanical "
        "fix across sites count as ONE mechanical fix; the sweep is mandatory. "
        "Anything requiring per-site adaptation is non-trivial → route."
    )
    header = txt[: txt.index("## First duty")]
    concept = txt[txt.index("## Concept sweep") : txt.index("## Safety rules")]
    assert clause in header
    assert clause in concept
    assert "唯一例外:逐字相同且可证明 inert 的同修多点传播,见 cmr-fixer.md" in _norm(SKILL)


# --- 0.3.18.3 finding #2: FALSE adjudication has a structured schema field


def test_fixer_adjudications_field_in_schema_positive():
    """A FALSE verdict must land in a structured `adjudications` schema
    slot (finding_id / verdict / evidence), not a vague free-text summary.

    Regression pin for codex round-3 P2: the first-duty told the fixer to
    write FALSE evidence "into the summary", but the strict JSON schema had
    no summary/adjudication field — the evidence had nowhere to go.
    """
    full = _norm(FIXER)
    # the schema exposes the array...
    assert '"adjudications"' in full, (
        "the fixer output schema must expose an adjudications array so a "
        "FALSE (or REAL) verdict is representable as structured data"
    )
    # ...with the three structured keys
    assert '"finding_id"' in full and '"verdict"' in full and '"evidence"' in full, (
        "each adjudications entry needs finding_id / verdict / evidence"
    )
    assert '"verdict": "REAL|FALSE"' in full, (
        "the verdict enumerates REAL|FALSE"
    )
    # the first-duty FALSE instruction points AT this field, not "summary"
    assert "recorded as a structured `adjudications` entry" in full, (
        "the FALSE-rejection instruction must reference the adjudications "
        "field, not a vague summary"
    )
    # negative: the old free-text-summary sink is gone
    assert "written into your summary" not in full


# --- 0.3.18.3 finding #3: incidental_fixes is the ONE scope-ban exception


def test_incidental_fixes_is_the_single_scope_exception_positive():
    """The `incidental_fixes` clause and the "nothing more" / no-scope-
    expansion bans must reference each other so there is no torn rule.

    The supplied-finding diff still fixes exactly the findings (no
    gold-plating); the ONE sanctioned exception is a real mechanical defect
    seen in passing, surfaced as its own separate patch.
    """
    full = _norm(FIXER)
    # the intro "nothing more" rule now names the one carve-out explicitly
    assert (
        "fixes **exactly what the findings identify and nothing more** "
        "(no gold-plating)" in full
    ), "the intro must still forbid gold-plating on the supplied diff"
    assert "with **one** sanctioned exception" in full, (
        "the intro must name incidental_fixes as the single exception"
    )
    assert "NOT a licence for general gold-plating" in full, (
        "the carve-out must not read as open season on scope expansion"
    )
    # Safety rule #2 carries the reciprocal carve-out and points back
    assert "The one\n   exception** is `incidental_fixes`" in FIXER.read_text(
        encoding="utf-8"
    ) or "The one exception** is `incidental_fixes`" in full, (
        "Safety rule #2 (no scope expansion) must carve out incidental_fixes"
    )
    assert "the single sanctioned scope exception" in full, (
        "Safety rule #2 must call incidental_fixes the single exception"
    )
    assert "still fixes exactly the findings and nothing more" in full, (
        "Safety rule #2 must reference the supplied-diff 'nothing more' rule "
        "so the two rules cross-reference and do not contradict"
    )


# --- 0.3.18.6 holistic schema completeness: every prose-required output is
# --- representable in the strict JSON (same class as the round-3 FALSE fix)


def test_fixer_incidental_fixes_severity_enum_includes_clarity():
    """A pure-formatting / typo / comment incidental defect is clarity/P4,
    so `incidental_fixes[].severity` must be able to represent `clarity`.

    Regression pin for codex round-6 P2 (~L186-192): the enum was the
    4-value `critical|high|medium|low`, so a clarity-level incidental had
    no representable severity — schema under-built vs the prose.
    """
    full = _norm(FIXER)
    # positive: the incidental_fixes severity enum carries clarity
    assert '"severity": "critical|high|medium|low|clarity"' in full, (
        "incidental_fixes[].severity must enumerate the full 5-value set "
        "including clarity, so a P4 incidental is representable"
    )
    # negative: the old 4-value enum (no clarity) is gone everywhere
    assert '"severity": "critical|high|medium|low"' not in full, (
        "the old clarity-less severity enum must not survive anywhere in "
        "the schema"
    )


def test_fixer_reported_defects_severity_enum_includes_clarity():
    """A non-trivial incidental defect reported for main-session routing
    can be clarity-level, so `reported_defects[].severity` must include
    clarity too — the schema uses one consistent 5-value set.
    """
    full = _norm(FIXER)
    # both incidental_fixes and reported_defects use the 5-value enum, so
    # the clarity-bearing enum string appears at least twice
    assert full.count('"severity": "critical|high|medium|low|clarity"') >= 2, (
        "both incidental_fixes and reported_defects severity enums must "
        "carry the full 5-value set including clarity"
    )


def test_fixer_summary_field_exists_and_report_loudly_points_at_it_positive():
    """The 'report them loudly / 大报' prose must point at a real schema
    field. The strict JSON now carries a top-level `summary` field and the
    report-loudly instructions reference it.

    Regression pin for codex round-6 P2 (~L51-60): the report-loudly duty
    required a summary the strict schema had no field for — output forbids
    text outside the schema, so the requirement was unrepresentable.
    """
    full = _norm(FIXER)
    # the dedicated top-level LOUD-report field exists (distinct from the
    # per-entry `summary` keys inside deferred/reported_defects)
    assert '"summary": "the LOUD report (大报)' in full, (
        "the fixer output schema must expose a top-level summary field that "
        "is the home for the report-loudly / 大报 narrative"
    )
    # the incidental-defect instruction now points AT the summary field
    assert "**report them loudly** in the `summary` field" in full, (
        "the incidental-defect report-loudly instruction must reference the "
        "concrete `summary` schema field"
    )
    # the non-trivial-defect instruction routes loudly into summary too
    assert "loudly in the `summary`" in full, (
        "the reported_defects report-loudly instruction must reference the "
        "`summary` field"
    )
    # the FALSE-verdict evidence still lands in adjudications, NOT summary
    assert "refuting evidence still goes in `adjudications`, never here" in full, (
        "the summary field must not become a re-opened sink for FALSE "
        "adjudication evidence (that stays in adjudications, round-3 rule)"
    )


def test_fixer_summary_field_negative_no_fieldless_report_loudly():
    """Negative counterpart: the report-loudly instructions must no longer
    point at a bare 'in your summary' with no backing schema field.
    """
    full = _norm(FIXER)
    assert "report them loudly** in your summary" not in full, (
        "the incidental report-loudly instruction must not reference a "
        "fieldless summary"
    )
    assert "loudly in your summary" not in full, (
        "the reported_defects report-loudly instruction must not reference "
        "a fieldless summary"
    )
    # the round-3 rule still holds: FALSE evidence never routed to a summary
    assert "written into your summary" not in full
