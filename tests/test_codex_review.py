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

import os
import stat
import subprocess
from pathlib import Path

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


def _run_codex(stub_dir, **env_extra):
    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env["CMR_CODEX_TIMEOUT"] = "15"
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True, env=env, timeout=60,
    )


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


def _selftest(effort=None):
    """Run `codex-review.sh --selftest`, optionally pinning CMR_CODEX_EFFORT."""
    env = dict(os.environ)
    if effort is not None:
        env["CMR_CODEX_EFFORT"] = effort
    else:
        env.pop("CMR_CODEX_EFFORT", None)
    return subprocess.run(
        ["bash", str(SCRIPT), "--selftest"],
        capture_output=True, text=True, env=env, timeout=30,
    )


def test_selftest_passes_with_default_medium_effort():
    # Default (no env) → every scenario uses medium; selftest green + names the pin.
    r = _selftest()
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "model_reasoning_effort=medium" in r.stdout
    assert "--model gpt-5.6-sol" in r.stdout


def test_selftest_passes_with_explicit_medium_effort():
    # Explicit medium matches the uniform reviewer policy.
    r = _selftest("medium")
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "model_reasoning_effort=medium" in r.stdout
    assert "model_reasoning_effort=xhigh" not in r.stdout


def test_invalid_effort_is_rejected():
    # Only medium is valid for CMR review; stale scenario-dependent tiers
    # and typos must hard-fail, not silently run at the wrong depth.
    r = _selftest("high")
    assert r.returncode == 64, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "CMR_CODEX_EFFORT must be medium" in r.stderr


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
