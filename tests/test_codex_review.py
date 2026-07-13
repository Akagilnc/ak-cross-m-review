"""Regression tests for backends/codex-review.sh.

Two pinned behaviors around the degrade gate:

1. A codex that exits NON-ZERO is a real outage (auth/quota/crash) and
   must degrade (exit 1 + synthetic empty findings), even if it printed a
   salvageable-looking body. Otherwise a failed codex silently counts as
   a valid zero-finding reviewer.

2. A codex that exits ZERO with a PROSE review (no JSON, no sentinel)
   must be PASSED THROUGH verbatim (exit 0), NOT degraded. Codex's
   strongest review is prose; the old sentinel-JSON gate dropped it as if
   codex were down — the divergence from the wiki (§「.result 是 review
   文本」: reviewers return prose, the orchestrator reads it) that lost the
   strongest reviewer to a format technicality across many rounds."""

import json
import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "codex-review.sh"


def test_degrades_when_codex_exits_nonzero_with_salvageable_body(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    codex = stub_dir / "codex"
    # Prints a JSON-ish error body but the process exits 1 — a real
    # outage (auth/quota/crash). Must degrade, never count as a review.
    codex.write_text('#!/bin/sh\necho \'{"error":"quota exceeded"}\'\nexit 1\n')
    codex.chmod(codex.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env["CMR_CODEX_TIMEOUT"] = "15"

    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True, env=env, timeout=60,
    )

    assert r.returncode == 1, (
        f"expected degrade exit 1, got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    # Synthetic degrade payload (compact, no spaces — see the printf).
    assert '"reviewer":"codex"' in r.stdout
    assert '"findings":[]' in r.stdout


def _codex_stub(stub_dir, body):
    """Drop an executable `codex` stub on PATH. `body` is the sh after the
    shebang; it can use $OUT (the path passed to codex's -o flag)."""
    stub_dir.mkdir(parents=True, exist_ok=True)
    codex = stub_dir / "codex"
    preamble = (
        "#!/bin/sh\n"
        'OUT=""\n'
        'while [ $# -gt 0 ]; do case "$1" in -o) OUT="$2"; shift 2;; *) shift;; esac; done\n'
    )
    codex.write_text(preamble + body)
    codex.chmod(codex.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return codex


def _run_codex(stub_dir, mode="code", **env_extra):
    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env["CMR_CODEX_TIMEOUT"] = "15"
    env.pop("CMR_DRY_RUN", None)
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT), mode],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True, env=env, timeout=60,
    )


def test_dry_run_is_unmistakably_non_review_and_nonzero(tmp_path):
    r = _run_codex(tmp_path / "bin", CMR_DRY_RUN="1")
    assert r.returncode == 2
    payload = json.loads(r.stdout)
    assert payload["dry_run"] is True
    assert payload["findings"] == []
    assert "NON-REVIEW" in r.stderr


@pytest.mark.parametrize("field", ["CMR_CODEX_TIMEOUT", "CMR_CODEX_IDLE_POLL"])
def test_invalid_watchdog_env_degrades_visibly(tmp_path, field):
    _codex_stub(tmp_path / "bin", "exit 1\n")
    watchdog_env = {"CMR_CODEX_TIMEOUT": "2", "CMR_CODEX_IDLE_POLL": "1"}
    watchdog_env[field] = "bogus"
    r = _run_codex(tmp_path / "bin", **watchdog_env)
    assert r.returncode == 1
    assert json.loads(r.stdout)["findings"] == []
    assert f"invalid {field}" in r.stderr
    assert "本轮缺 codex" in r.stderr


def test_invalid_mode_degrades_with_safe_json(tmp_path):
    _codex_stub(tmp_path / "bin", "exit 1\n")
    r = _run_codex(tmp_path / "bin", mode='bad"\nmode')
    assert r.returncode == 1
    payload = json.loads(r.stdout)
    assert payload == {"reviewer": "codex", "mode": "code", "findings": []}
    assert "invalid MODE" in r.stderr
    assert "本轮缺 codex" in r.stderr


def test_emits_last_message_not_stdout_echo(tmp_path):
    # THE fix: codex's strongest output is a PROSE review, written to the
    # -o (--output-last-message) file; its STDOUT is the ~1.5MB prompt
    # echo + reasoning trace. The backend must emit the -o review (exit 0,
    # not degrade) and must NOT emit the verbose stdout — that's the ~99%
    # size cut and the whole point.
    review = (
        "I reviewed the diff. One real issue:\\n"
        "P1: route.ts:96 route() treats a non-reviewer output as 0 findings, "
        "letting a malformed step bypass the P0/P1 gate.\\n"
        "CMR-VERDICT: findings"
    )
    _codex_stub(tmp_path / "bin", (
        'echo "VERBOSE_ECHO_PROMPT_TRACE_NOISE — 1.5MB of echo would be here"\n'
        f'[ -n "$OUT" ] && printf \'%b\\n\' "{review}" > "$OUT"\n'
        "exit 0\n"
    ))
    r = _run_codex(tmp_path / "bin")
    assert r.returncode == 0, (
        f"a real review must pass through (exit 0), not degrade; got "
        f"{r.returncode}\nstdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert "route() treats a non-reviewer output" in r.stdout, (
        f"codex's -o review was not emitted. stdout={r.stdout!r}"
    )
    assert "VERBOSE_ECHO_PROMPT_TRACE_NOISE" not in r.stdout, (
        "the verbose codex stdout echo was emitted instead of the clean "
        f"-o last message — the size cut is not happening. stdout={r.stdout!r}"
    )
    assert "本轮缺 codex" not in r.stderr


def test_degrades_when_final_message_empty(tmp_path):
    # codex exits 0 but writes NO final message (only a trace, or -o
    # unsupported) → the -o file is empty. That must degrade, never emit
    # an empty review as a silent zero-finding approve.
    _codex_stub(tmp_path / "bin", (
        'echo "only a reasoning trace on stdout, no final message"\n'
        # deliberately do NOT write $OUT
        "exit 0\n"
    ))
    r = _run_codex(tmp_path / "bin")
    assert r.returncode == 1, (
        f"empty final message must degrade; got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert '"findings":[]' in r.stdout
    assert "本轮缺 codex" in r.stderr


def test_streaming_codex_survives_when_total_time_exceeds_idle_window(tmp_path):
    # Wiki §额外硬规则 #4: a hang is N seconds of NO stdout/stderr, NOT total
    # wall-clock. A codex that keeps streaming (a line every 1s for 5s) must
    # NOT be killed even though its TOTAL runtime (5s) exceeds the idle
    # window (2s) — only SILENCE longer than the window is a hang. (Under the
    # old `timeout 2s` total-cap this stub was killed at 2s; the idle
    # watchdog must let it finish.)
    _codex_stub(tmp_path / "bin", (
        'for i in 1 2 3 4 5; do echo "reasoning chunk $i"; sleep 1; done\n'
        '[ -n "$OUT" ] && printf \'%b\\n\' "P2 minor nit. CMR-VERDICT: findings" > "$OUT"\n'
        "exit 0\n"
    ))
    r = _run_codex(tmp_path / "bin", CMR_CODEX_TIMEOUT="2", CMR_CODEX_IDLE_POLL="1")
    assert r.returncode == 0, (
        f"a continuously-streaming codex must survive past the idle window "
        f"(total runtime > window is fine — only silence is a hang); got "
        f"{r.returncode}\nstdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert "P2 minor nit" in r.stdout
    assert "本轮缺 codex" not in r.stderr


def test_silent_codex_killed_after_idle_window(tmp_path):
    # The flip side: a codex that goes SILENT (one line, then no output for
    # longer than the idle window) is a hang → scoped-killed → degrade. It
    # must fire at ~the idle window (~2s), NOT wait for the stub's 30s sleep.
    _codex_stub(tmp_path / "bin", (
        'echo "first reasoning line"\n'
        "sleep 30\n"   # then silent, far longer than the idle window
        "exit 0\n"
    ))
    r = _run_codex(tmp_path / "bin", CMR_CODEX_TIMEOUT="2", CMR_CODEX_IDLE_POLL="1")
    assert r.returncode == 1, (
        f"a silent (hung) codex must degrade; got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert "本轮缺 codex" in r.stderr
    assert '"findings":[]' in r.stdout


def _selftest(effort=None, model=None):
    """Run `codex-review.sh --selftest`, optionally pinning CMR_CODEX_EFFORT
    and/or CMR_CODEX_MODEL."""
    env = dict(os.environ)
    if effort is not None:
        env["CMR_CODEX_EFFORT"] = effort
    else:
        env.pop("CMR_CODEX_EFFORT", None)
    if model is not None:
        env["CMR_CODEX_MODEL"] = model
    else:
        env.pop("CMR_CODEX_MODEL", None)
    return subprocess.run(
        ["bash", str(SCRIPT), "--selftest"],
        capture_output=True, text=True, env=env, timeout=30,
    )


def test_selftest_passes_with_default_medium_effort():
    # Default (no env) → medium + gpt-5.6-sol; selftest green + names the pin.
    r = _selftest()
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "model_reasoning_effort=medium" in r.stdout
    assert "--model gpt-5.6-sol" in r.stdout


def test_selftest_passes_with_explicit_medium_effort():
    # Explicit medium is just the default value passed through.
    r = _selftest("medium")
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "model_reasoning_effort=medium" in r.stdout
    assert "model_reasoning_effort=xhigh" not in r.stdout


def test_effort_override_low_passes_through_verbatim():
    # Owner ruling 2026-07-12: this file's only job is avoiding codex
    # pitfalls, NOT restricting effort. A caller who wants low gets low —
    # passed through verbatim to -c model_reasoning_effort=…, selftest still
    # green (no exit 64), the FORM check adapts to the override.
    r = _selftest("low")
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "model_reasoning_effort=low" in r.stdout
    assert "model_reasoning_effort=medium" not in r.stdout


def test_effort_override_high_passes_through_verbatim():
    # Same for a higher tier — no whitelist, no rejection.
    r = _selftest("high")
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "model_reasoning_effort=high" in r.stdout


def test_model_override_luna_passes_through_verbatim():
    # Model is symmetric with effort: default gpt-5.6-sol, but any override
    # (e.g. luna) flows through verbatim, selftest still green.
    r = _selftest(model="luna")
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "--model luna" in r.stdout
    assert "--model gpt-5.6-sol" not in r.stdout


def test_model_and_effort_override_together():
    # Both overridden at once (luna + high) — both pass through, form check
    # green.
    r = _selftest(effort="high", model="luna")
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "model_reasoning_effort=high" in r.stdout
    assert "--model luna" in r.stdout


def test_default_idle_timeout_is_900s():
    # User decision 2026-07-06 after an xhigh codex was false-killed at the
    # 8min threshold: the IDLE default is 900s = 15min (escalation history
    # 3min → 8min → 15min). The wiki (§额外硬规则 #4) was updated to 15min
    # the same day — in sync; this pin stops a wiki re-sync from silently
    # regressing the default to 480 (or the ancient 180).
    src = SCRIPT.read_text(encoding="utf-8")
    assert 'IDLE_TIMEOUT="${CMR_CODEX_TIMEOUT:-900}"' in src, (
        "codex idle-timeout default must be 900s (15min, user decision "
        "2026-07-06) — 480 was false-killing deep-reasoning runs"
    )


# --- Doc claims about CMR_CODEX_EFFORT must match the CURRENT backend: a
# --- DEFAULT of medium with a genuine verbatim override, NOT a "mandatory
# --- and uniform" pin (0.3.18.22, Finding 3). The exit-64 whitelist was
# --- removed in 0.3.18.15; the backend now passes any override verbatim,
# --- with `medium` only as the unset-default (see backend line: "NO
# --- whitelist" + CMR_CODEX_EFFORT="${CMR_CODEX_EFFORT:-medium}").

ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / "SKILL.md"
README_MD = ROOT / "README.md"


def _norm_doc(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def test_backend_effort_is_default_not_whitelisted():
    # ground the doc pins against the real backend contract they describe
    src = SCRIPT.read_text(encoding="utf-8")
    assert 'CMR_CODEX_EFFORT="${CMR_CODEX_EFFORT:-medium}"' in src, (
        "backend must treat medium as the UNSET-DEFAULT, not a hard pin"
    )
    assert "NO whitelist" in src, (
        "backend must document the whitelist removal (any override verbatim)"
    )


def test_skill_effort_doc_says_default_with_override_not_mandatory():
    txt = _norm_doc(SKILL_MD)
    assert "**The reasoning-effort pin defaults to `medium`**" in txt, (
        "SKILL.md must describe medium as the DEFAULT, matching the backend "
        "unset-default — not a mandatory/uniform pin"
    )
    assert (
        "`CMR_CODEX_EFFORT` stays a genuine override: the backend passes any "
        "value (`low`/`high`/`xhigh`/…) through verbatim, with no whitelist"
    ) in txt, (
        "SKILL.md must state the override is passed verbatim with no "
        "whitelist, matching the current backend"
    )
    # the pinning-prevents-drift rationale must survive (still true)
    assert "cannot silently inherit the machine's `~/.codex/config.toml`" in txt


def test_skill_effort_doc_drops_mandatory_and_uniform_negative():
    txt = _norm_doc(SKILL_MD)
    assert "reasoning-effort pin is mandatory and uniform" not in txt, (
        "the stale 'mandatory and uniform' effort claim must be gone — the "
        "exit-64 whitelist was removed in 0.3.18.15"
    )
    # Round-5 leftover: the retired absolute framing wasn't only that one
    # exact phrase — the Step-2 summary bullet still said "`medium`
    # uniformly", which reads just as absolute. Pin the retired shape too.
    assert "`medium` uniformly" not in txt, (
        "the absolute '`medium` uniformly' framing (no override caveat) must "
        "be gone — codex effort is a DEFAULT of medium, overridable via "
        "CMR_CODEX_EFFORT (round-5 Finding, same class as round-4 F3)"
    )


def test_skill_every_uniform_medium_claim_carries_override_caveat():
    # BROADER guard than the exact-phrase pins above. Round-4 fixed the L287
    # §调用规范 callout + README but MISSED the Step-2 per-leg summary bullet,
    # because the only negative pin matched one retired phrase. Catch the
    # whole class: anywhere SKILL.md pairs a "uniform…"/absolute framing with
    # "medium", an AFFIRMATIVE override word (overridable/override) must
    # appear in the same window. Note it deliberately requires "overrid…",
    # NOT the bare `CMR_CODEX_EFFORT` token: the round-4 leftover bullet DID
    # name CMR_CODEX_EFFORT — but only as the drift-guard ("pinned via -c so
    # host config cannot drift"), never as a genuine override. A bare-token
    # check would have passed the buggy text; requiring the affirmative
    # override word is what makes this catch the actual class.
    txt = _norm_doc(SKILL_MD)
    hits = list(re.finditer(r"\buniform\w*\b", txt))
    assert hits, "expected at least the per-leg summary bullet's 'uniform' claim"
    for m in hits:
        window = txt[max(0, m.start() - 220): m.end() + 220]
        if "medium" not in window:
            continue  # a 'uniform' unrelated to codex effort
        assert re.search(r"overrid", window), (
            "a 'uniform'+'medium' effort claim in SKILL.md lacks a nearby "
            "affirmative override word (overridable/override) — naming "
            "CMR_CODEX_EFFORT only as a drift-guard is NOT enough:\n"
            f"…{window}…"
        )


def test_skill_summary_bullet_states_effort_override():
    # The Step-2 "Reasoning-effort reality, per leg" summary table is the
    # FIRST place a reader meets codex's effort behavior — before the L287
    # §调用规范 callout. Round-4's fix reached the callout + README but not
    # this bullet, so a reader stopping here still saw "medium uniformly"
    # with no override. Pin BOTH the uniform-DEFAULT framing and the explicit
    # override so THIS bullet, read in isolation, tells the reader
    # CMR_CODEX_EFFORT is a working override — not a violation of "uniform".
    txt = _norm_doc(SKILL_MD)
    assert "**codex** = `medium` **uniform default** for both" in txt, (
        "the per-leg summary bullet must frame medium as a uniform DEFAULT, "
        "not an absolute '`medium` uniformly'"
    )
    assert "overridable via `CMR_CODEX_EFFORT`" in txt, (
        "the summary bullet itself must acknowledge CMR_CODEX_EFFORT is a "
        "working override — round-4's fix reached L287/README but not here"
    )


def test_readme_effort_doc_says_default_with_override():
    txt = _norm_doc(README_MD)
    assert (
        "Reasoning effort defaults to `medium` for ship-pre and per-slice "
        "(the operational convention); `CMR_CODEX_EFFORT` overrides it and "
        "the backend passes any value through verbatim (no whitelist)."
    ) in txt, (
        "README.md must describe medium as the default with a verbatim "
        "CMR_CODEX_EFFORT override"
    )


def test_readme_effort_doc_drops_uniform_absolute_negative():
    txt = _norm_doc(README_MD)
    assert "Reasoning effort is uniformly `medium` for ship-pre and per-slice." not in txt, (
        "the stale absolute 'effort is uniformly medium' claim (no override "
        "caveat) must be gone"
    )


TESTING_MD = ROOT / "TESTING.md"


def test_selftest_validates_effort_form_not_value():
    # ROOT fix for the 4th recurrence (round 7, F3) of "codex effort
    # documented as an absolute". Rounds 4/5/6 each added a NARROWER regex
    # chasing a specific PHRASING (retired phrase → "uniform*" family →
    # standalone `medium` token), and each new round's bug evaded the
    # previous guard via a new wording — round 7's TESTING.md bug wrote the
    # compound token `model_reasoning_effort=medium` (medium preceded by "=",
    # not a backtick), which the round-6 backtick-delimited `medium` guard
    # structurally could not see.
    #
    # Part (A) below ties the test to the REAL invariant (the actual
    # backend code): the selftest validates the invocation FORM, pinning
    # `model_reasoning_effort=${CMR_CODEX_EFFORT}` — whatever effort is in
    # effect — NOT the literal value `medium`. Part (B) is a narrower
    # textual safety net against the ONE specific value-token phrasing that
    # has recurred 4 times — it is not, and cannot be, an exhaustive guard
    # against every possible semantically-equivalent rewording (docs are
    # free text); that residual risk is accepted, not solved, per this
    # repo's own "don't over-defend with more mechanism" principle. Two
    # structural anchors:
    #
    #   (A) Backend: extract the selftest block from the ACTUAL script and
    #       confirm its canonical-form check interpolates ${CMR_CODEX_EFFORT}
    #       and hard-codes NO `model_reasoning_effort=medium`. The test now
    #       tracks the real code, not a wording pattern.
    #   (B) Docs: no .md may describe the selftest (window around every
    #       "selftest" mention) as checking a fixed
    #       `model_reasoning_effort=medium` — the value the selftest does
    #       NOT check. This catches the one recurring value-token phrasing,
    #       not every equivalent rewording (see the caveat above).
    src = SCRIPT.read_text(encoding="utf-8")

    # (A) isolate the selftest block: from the `--selftest` guard to EOF.
    marker = 'if [ "${1:-}" = "--selftest" ]'
    assert marker in src, "selftest guard block not found in backend"
    selftest_block = src[src.index(marker):]
    assert "model_reasoning_effort=${CMR_CODEX_EFFORT}" in selftest_block, (
        "the selftest's canonical-form check must interpolate "
        "${CMR_CODEX_EFFORT} — it validates the FORM (whatever effort is in "
        "effect), not a fixed value"
    )
    assert "model_reasoning_effort=medium" not in selftest_block, (
        "the selftest block must NOT hard-code model_reasoning_effort=medium "
        "— that would pin the VALUE instead of the form; the invariant is "
        "form-not-value (round-7 F3, 4th recurrence)"
    )

    # (B) no doc may present that fixed value as what the selftest validates.
    WINDOW = 250
    for label, path in (
        ("TESTING.md", TESTING_MD),
        ("SKILL.md", SKILL_MD),
        ("README.md", README_MD),
    ):
        txt = _norm_doc(path)
        for m in re.finditer(r"selftest", txt):
            window = txt[max(0, m.start() - WINDOW): m.end() + WINDOW]
            assert "model_reasoning_effort=medium" not in window, (
                f"{label}: text describing --selftest states a fixed "
                f"`model_reasoning_effort=medium`, but the selftest validates "
                f"the FORM (model_reasoning_effort=${{CMR_CODEX_EFFORT}}), not "
                f"that value — this is the round-4/5/6/7 recurrence:\n…{window}…"
            )


# --- Step 2 invocation-form contract (issue #30)

FABLE_MARKER = (
    "**⚠ RECORDED RULE（存续）— Fable 禁用：** cmr 不在任何腿使用 Fable；"
    "Claude 腿显式固定为 `opus`（Claude Opus 4.8）。这有意不同于 wiki 的"
    "最强可用 Claude 规则；sync 时不得重新加入 Fable。"
)
AGY_WARM_RETRY_MARKER = (
    "**⚠ RECORDED divergence（新建）— agy warm+retry：** 相对 wiki“agy "
    "1.0.8 无需 warm+retry”的结论，本 skill 仍保留每次预热 + 共 4 次尝试；"
    "sync 时不得删除。"
)
def _step2_raw():
    raw = SKILL_MD.read_text(encoding="utf-8")
    return raw[raw.index("## Step 2") : raw.index("## Step 3")]


def test_step2_has_two_sync_recognizable_recorded_markers_on_one_line():
    lines = [line.strip() for line in _step2_raw().splitlines()]
    markers = [line for line in lines if line.startswith("**⚠ RECORDED")]
    assert len(markers) == 2
    for marker in (FABLE_MARKER, AGY_WARM_RETRY_MARKER):
        assert marker in lines, f"RECORDED marker must be one physical line: {marker}"
    assert not any("strict REVIEW-ONLY" in line for line in lines)


def test_step2_contract_keeps_all_invocation_hard_bans():
    txt = " ".join(_step2_raw().split())
    for hard_ban in (
        "Never omit `--ephemeral`",
        "Never `codex exec \"$(...)\"`",
        "never `-C <dir>`",
        "never `codex review --base B \"PROMPT\"`",
        "never send a >10K-line prompt as one segment",
        "never a global `pkill -f codex`",
        "Never call `agy -p --sandbox`",
        "Never `agy --dangerously-skip-permissions`",
        "never the deprecated `gemini --approval-mode plan`",
        "Never relax the injected no-modify/no-fix discipline; reviewer inspection and verification commands are allowed",
        "Never use headless `claude -p` for this leg",
    ):
        assert hard_ban in txt, f"missing Step 2 hard ban: {hard_ban}"


def test_step2_keeps_four_element_structure_labels_for_all_three_legs():
    txt = _step2_raw()
    for label in ("**入口：**", "**硬禁令：**", "**降级旗：**"):
        assert txt.count(label) >= 3, (
            f"Step 2 must keep one {label} label per reviewer leg"
        )


def test_step2_gemini_step_down_is_not_google_family_diversity():
    txt = " ".join(_step2_raw().split())
    assert "NO Google voice this round" in txt
    assert "Google-family" in txt, "missing Step 2 Google-family diversity exclusion"
    assert "round report 必须带旗" in txt, "missing Step 2 round report flag requirement"


def test_step2_has_single_pending_guard_section_for_unguarded_behavior():
    raw = _step2_raw()
    assert raw.count("### 待补守护（暂不得删）") == 1
    pending = raw[raw.index("### 待补守护（暂不得删）") :]
    assert "无可执行守护" in pending
    assert "不得删" in pending
