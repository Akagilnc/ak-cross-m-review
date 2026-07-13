from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_CHECKLIST = ROOT / "UPSTREAM-CHECKLIST.md"


def test_upstream_checklist_keeps_agy_archaeology_until_sync():
    assert UPSTREAM_CHECKLIST.exists(), (
        "UPSTREAM-CHECKLIST.md must survive until the next wiki sync PR"
    )
    text = " ".join(UPSTREAM_CHECKLIST.read_text(encoding="utf-8").split())
    for key_sentence in (
        "**agy model-degradation ladder**",
        "`Claude Sonnet 4.6 (Thinking)` via agy",
        "不新建 `BACKENDS.md`",
    ):
        assert key_sentence in text, (
            f"UPSTREAM-CHECKLIST.md missing archaeology: {key_sentence}"
        )
