"""main=Codex host differences stay centralized in one substitution table."""

from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def _raw():
    return SKILL.read_text(encoding="utf-8")


def _norm():
    return " ".join(_raw().split())


def _table_section():
    txt = _norm()
    start = txt.index("## main=Codex 宿主替换表")
    end = txt.index("## Step 2", start)
    return txt[start:end]


def test_codex_host_substitution_table_covers_dispatch_and_claude_call():
    sec = _table_section()
    assert "ship-pre 顶层" in sec and "native subagent" in sec
    assert "per-slice" in sec and "`codex exec`" in sec
    assert "live-smoke" in sec and "CLAUDE_OK" in sec
    assert "`claude -p`" in sec and "`--model claude-opus-4-8`" in sec
    assert "无 `--effort max`" in sec
    assert "reviewer 不带 `--tools \"\"`" in sec
    assert "file/env" in sec
    assert "PROMPT_FILE" in sec
    assert "wiki hypothesis" in sec and "未在本 skill 实测" in sec


def test_codex_host_substitution_table_covers_degradation_rows():
    sec = _table_section()
    assert "Claude down" in sec and "Codex + Gemini" in sec
    assert "Gemini down" in sec and "Codex + Claude" in sec
    assert "Claude + Gemini both down" in sec and "Codex only" in sec
    assert "本轮缺 claude" in sec
    assert "本轮缺 gemini" in sec
    assert "本轮无 outside voice" in sec


def test_codex_host_substitution_table_pins_fixed_two_leg_scenario():
    sec = _table_section()
    assert "固定双腿场景" in sec
    assert "completeness (Step 5) 仍含 Claude 腿" in sec


def test_codex_solo_exception_is_scoped_away_from_completeness():
    sec = _table_section()
    assert "per-slice / correctness (Step 6)" in sec
    assert "codex solo" in sec
    assert "单腿 codex (agy down)，无 cross-vendor，质量降级" in sec
    assert "不适用于 Step 5 completeness" in sec


def test_old_codex_host_insets_are_absent_from_mainline_steps():
    raw = _raw()
    step2 = raw[raw.index("## Step 2") : raw.index("## Step 3")]
    step3 = raw[raw.index("## Step 3") : raw.index("## Step 4")]
    step5 = raw[raw.index("## Step 5") : raw.index("## Step 6")]
    assert "main=Codex host only" not in step2
    assert "only main=Codex completeness one-pass" not in step2
    assert "If the main session is Codex" not in step3
    assert "main=Codex correctness" not in step5
    assert "Explicit exception: main=Codex" not in step5
