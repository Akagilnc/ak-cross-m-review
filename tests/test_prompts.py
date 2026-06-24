"""The two review lenses must each be a real, dispatchable prompt file.

The completeness lens used to exist ONLY as prose in SKILL.md ("append a
completeness lens to cmr-reviewer.md"), with no prompt artifact — so a
ship-pre run could dispatch nothing but the correctness prompt and the
Step-5 completeness gate silently never ran. These tests pin that BOTH
lenses are executable artifacts and stay distinct, and that SKILL.md wires
the completeness prompt in (so the selector can't regress to prose-only).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORRECTNESS = ROOT / "prompts" / "cmr-reviewer.md"
COMPLETENESS = ROOT / "prompts" / "cmr-completeness.md"
SKILL = ROOT / "SKILL.md"


def test_both_lens_prompts_exist():
    assert CORRECTNESS.is_file(), "correctness lens prompt missing"
    assert COMPLETENESS.is_file(), (
        "completeness lens prompt missing — the Step-5 gate has nothing to "
        "dispatch (the original prose-only bug)"
    )


def test_correctness_prompt_is_the_defect_lens():
    txt = CORRECTNESS.read_text(encoding="utf-8")
    assert "correctness defect" in txt or "correctness defects" in txt
    # its verdict line is the converged/findings pair, NOT completeness
    assert "CMR-VERDICT: converged" in txt
    assert "CMR-VERDICT: findings" in txt
    assert "UNVERIFIED-GAP" not in txt  # that taxonomy belongs to completeness


def test_completeness_prompt_is_the_delivery_lens():
    txt = COMPLETENESS.read_text(encoding="utf-8")
    # spec-delivery framing, explicitly NOT a correctness/defect lens
    assert "completeness" in txt.lower()
    # the completeness verdict taxonomy (both scales) must be present
    for verdict in ("DONE", "PARTIAL", "NOT-DONE", "CONFORMS", "VIOLATES", "UNVERIFIED-GAP"):
        assert verdict in txt, f"completeness prompt missing verdict '{verdict}'"
    # the two anti-hollow disciplines
    assert "reference chain" in txt.lower(), "missing chase-the-reference-chain rule"
    assert "exercise" in txt.lower(), "missing exercise-the-behavioral-keys rule"
    assert "NOT completeness evidence" in txt, "missing green-tests-≠-evidence rule"
    # its own verdict-line pair (distinct from correctness)
    assert "CMR-VERDICT: complete" in txt
    assert "CMR-VERDICT: gaps" in txt


def test_skill_dispatches_both_lenses():
    txt = SKILL.read_text(encoding="utf-8")
    # the selector must reference the completeness prompt by path, or the
    # gate is unreachable again
    assert "prompts/cmr-completeness.md" in txt or "cmr-completeness.md" in txt, (
        "SKILL.md never dispatches the completeness prompt — Step-5 gate "
        "unreachable"
    )
    assert "cmr-reviewer.md" in txt
