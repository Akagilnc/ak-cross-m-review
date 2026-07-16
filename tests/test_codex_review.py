"""Regression tests for backends/codex-review.sh.

Two pinned behaviors around the degrade gate:

1. A codex that exits NON-ZERO must degrade (empty stdout + exit 1 + stderr
   flag) while preserving a bounded native diagnostic tail. Otherwise a failed
   codex silently counts as a valid zero-finding reviewer or hides its cause.

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

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "codex-review.sh"
REVIEW_TASK = (
    "Review fixed range 111...222 from this clone; run git diff --binary "
    "111...222; authority: AGENTS.md.\n"
)


def test_nonzero_codex_exit_preserves_native_error_and_degrades(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    codex = stub_dir / "codex"
    # Codex reports its actionable native failure on the captured process
    # stream, then exits non-zero. The backend must preserve that reason on
    # stderr while still degrading rather than counting it as a review.
    codex.write_text(
        "#!/bin/sh\n"
        'printf "EARLY_NATIVE_OUTPUT_PREFIX_MUST_BE_TRUNCATED\\n" >&2\n'
        "head -c 9000 /dev/zero | tr '\\0' x >&2\n"
        'printf "\\nInput exceeds the maximum length of 1048576 characters.\\n" >&2\n'
        "exit 1\n"
    )
    codex.chmod(codex.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env["CMR_CODEX_TIMEOUT"] = "15"

    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True, env=env, timeout=60,
    )

    assert r.returncode == 1, (
        f"expected degrade exit 1, got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert r.stdout == ""
    assert "EARLY_NATIVE_OUTPUT_PREFIX_MUST_BE_TRUNCATED" not in r.stderr, (
        "native diagnostics must be bounded to the final 8192 bytes; an "
        f"unbounded cat leaked the early prefix. stderr={r.stderr!r}"
    )
    assert "Input exceeds the maximum length of 1048576 characters." in r.stderr
    assert r.stderr.index("Input exceeds the maximum length") < r.stderr.index(
        "codex exited non-zero"
    )
    assert "本轮缺 codex" in r.stderr, (
        f"degrade must keep the visible flag — the stderr flag and the "
        f"nonzero exit are the ONLY two signals since #39\nstderr={r.stderr!r}"
    )


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
        input=REVIEW_TASK,
        capture_output=True, text=True, env=env, timeout=60,
    )


def test_review_packet_passes_to_codex_verbatim(tmp_path):
    prompt_dump = tmp_path / "prompt"
    packet = REVIEW_TASK
    _codex_stub(
        tmp_path / "bin",
        'cat > "$CODEX_PROMPT_DUMP"\n'
        '[ -n "$OUT" ] && printf "grounded prose review\\n" > "$OUT"\n'
        "exit 0\n",
    )

    result = _run_codex(
        tmp_path / "bin", CODEX_PROMPT_DUMP=str(prompt_dump)
    )

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert prompt_dump.read_text() == packet


def test_dry_run_is_unmistakably_non_review_and_nonzero(tmp_path):
    r = _run_codex(tmp_path / "bin", CMR_DRY_RUN="1")
    assert r.returncode == 2
    assert r.stdout == ""
    assert "NON-REVIEW" in r.stderr
    assert "本轮缺 codex (NON-REVIEW DRY_RUN)" in r.stderr


@pytest.mark.parametrize("field", ["CMR_CODEX_TIMEOUT", "CMR_CODEX_IDLE_POLL"])
def test_invalid_watchdog_env_degrades_visibly(tmp_path, field):
    _codex_stub(tmp_path / "bin", "exit 1\n")
    watchdog_env = {"CMR_CODEX_TIMEOUT": "2", "CMR_CODEX_IDLE_POLL": "1"}
    watchdog_env[field] = "bogus"
    r = _run_codex(tmp_path / "bin", **watchdog_env)
    assert r.returncode == 1
    assert r.stdout == ""
    assert f"invalid {field}" in r.stderr
    assert "本轮缺 codex" in r.stderr


def test_invalid_mode_degrades_with_empty_stdout(tmp_path):
    _codex_stub(tmp_path / "bin", "exit 1\n")
    r = _run_codex(tmp_path / "bin", mode='bad"\nmode')
    assert r.returncode == 1
    assert r.stdout == ""
    assert "invalid MODE" in r.stderr
    assert "本轮缺 codex" in r.stderr


def test_emits_last_message_not_stdout_echo(tmp_path):
    # THE fix: codex's strongest output is a PROSE review, written to the
    # -o (--output-last-message) file; its STDOUT is the task echo + reasoning
    # trace. The backend must emit the -o review (exit 0, not degrade) and must
    # not mix the verbose transport stream into review stdout.
    review = (
        "I reviewed the diff. One real issue:\\n"
        "P1: route.ts:96 route() treats a non-reviewer output as 0 findings, "
        "letting a malformed step bypass the P0/P1 gate.\\n"
        "CMR-VERDICT: findings"
    )
    _codex_stub(tmp_path / "bin", (
        'echo "VERBOSE_TASK_TRACE_NOISE would be here"\n'
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
    assert "VERBOSE_TASK_TRACE_NOISE" not in r.stdout, (
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
    assert r.stdout == ""
    assert "only a reasoning trace on stdout, no final message" in r.stderr
    assert r.stderr.index("only a reasoning trace") < r.stderr.index(
        "exited 0 but wrote no final message"
    )
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
    assert "first reasoning line" in r.stderr
    assert r.stderr.index("first reasoning line") < r.stderr.index("timeout/kill")
    assert r.stdout == ""


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


def test_selftest_ignores_invalid_watchdog_env():
    env = dict(os.environ)
    env["CMR_CODEX_TIMEOUT"] = "bogus"
    r = subprocess.run(
        ["bash", str(SCRIPT), "--selftest"],
        capture_output=True, text=True, env=env, timeout=30,
    )
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "invocation is on-convention" in r.stdout


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
