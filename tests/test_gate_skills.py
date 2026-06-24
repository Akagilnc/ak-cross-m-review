"""The two gate skills must stay thin named wrappers over the engine.

Design (user-directed, 2026-06-24): instead of a `--lens` flag the agent
might forget or mis-set, the completeness and correctness gates are each
their own NAMED skill that just invokes `ak-cross-m-review` with the right
lens. These tests pin that both wrappers exist, name themselves correctly,
delegate to the engine, and each carry their own lens — so the explicit
two-gate entry point can't silently regress.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPLETENESS = ROOT / "skills" / "ak-cmr-completeness" / "SKILL.md"
CORRECTNESS = ROOT / "skills" / "ak-cmr-correctness" / "SKILL.md"
INSTALL = ROOT / "scripts" / "install-skills.sh"


def _frontmatter(path: Path) -> str:
    txt = path.read_text(encoding="utf-8")
    assert txt.startswith("---\n"), f"{path.name}: no frontmatter fence"
    end = txt[4:].find("\n---")
    assert end != -1, f"{path.name}: frontmatter not closed"
    return txt[4 : 4 + end]


def test_both_gate_skills_exist():
    assert COMPLETENESS.is_file(), "ak-cmr-completeness gate skill missing"
    assert CORRECTNESS.is_file(), "ak-cmr-correctness gate skill missing"


def test_gate_skills_name_themselves():
    assert "name: ak-cmr-completeness" in _frontmatter(COMPLETENESS)
    assert "name: ak-cmr-correctness" in _frontmatter(CORRECTNESS)


def test_completeness_gate_delegates_with_completeness_lens():
    txt = COMPLETENESS.read_text(encoding="utf-8")
    assert "ak-cross-m-review" in txt, "completeness gate must invoke the engine"
    assert "--lens completeness" in txt, "completeness gate must pass --lens completeness"
    assert "--lens correctness" not in txt  # not the wrong lens


def test_correctness_gate_delegates_with_correctness_lens():
    txt = CORRECTNESS.read_text(encoding="utf-8")
    assert "ak-cross-m-review" in txt, "correctness gate must invoke the engine"
    assert "--lens correctness" in txt, "correctness gate must pass --lens correctness"


def test_gate_skills_stay_thin():
    # A wrapper must NOT re-implement the engine — guard against it growing a
    # copy of the dispatch/merge/loop machinery (the duplication we avoided).
    for path in (COMPLETENESS, CORRECTNESS):
        body = path.read_text(encoding="utf-8")
        # no backend invocation / squad machinery inside the wrapper
        assert "codex-review.sh" not in body, f"{path.parent.name} re-implements dispatch"
        assert "two-phase" not in body.lower(), f"{path.parent.name} re-implements the engine"


def test_install_script_links_all_three():
    txt = INSTALL.read_text(encoding="utf-8")
    for name in ("ak-cross-m-review", "ak-cmr-completeness", "ak-cmr-correctness"):
        assert name in txt, f"install-skills.sh does not link {name}"
