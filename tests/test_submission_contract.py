"""The review submission contract (交卷契约, ADR 0130) must stay pinned.

User ratification 2026-07-12; wiki §额外硬规则 #8. Three semantics:

1. A review leg reports ALL findings it sees within one round — severity
   is a PROPERTY of a finding, not an admission threshold for whether to
   report it; delivery is complete only when every finding is written down
   ("dig up one or two nail-able ones and knock off" is no longer valid).
2. The fixer's FIRST duty = empirically adjudicate each supplied finding
   one by one: REAL → fix + same-class sweep; FALSE → reject WITH EVIDENCE
   in the summary for the next fresh reviewer; other real defects seen in
   passing → small-fix (committed independently) + report loudly.
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
    assert "②–⑤ anti-runaway discipline is untouched" in txt, (
        "doc-mode anti-runaway discipline must be declared unaffected"
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
    assert "②–⑤ anti-runaway discipline below is untouched" in txt, (
        "the doc-mode addendum's anti-runaway discipline stays unaffected"
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
    # FALSE → reject WITH EVIDENCE, adjudicated next round
    assert "**FALSE**" in txt
    assert "reject it **with evidence** written into your summary" in txt
    assert "a fresh reviewer next round adjudicates the rejection" in txt
    # other real defects seen in passing → small-fix + report loudly
    assert "Other real defects you see in passing" in txt
    assert "small-fix them, committed independently" in txt
    assert "**report them loudly**" in txt


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
