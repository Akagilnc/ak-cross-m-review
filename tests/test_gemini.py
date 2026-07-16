"""Behavioral tests for agy's primary call and quota-only second pool."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "gemini.sh"
REVIEW_TASK = (
    "Review fixed range 111...222 from this clone; run git diff --binary "
    "111...222; authority: AGENTS.md.\n"
)


def _stub_agy(stub_dir: Path, body: str) -> None:
    """Drop an executable `agy` stub on PATH that runs `body`."""
    stub_dir.mkdir(parents=True, exist_ok=True)
    g = stub_dir / "agy"
    g.write_text(body)
    g.chmod(g.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _env_with_stub(stub_dir: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    # Keep default-model tests deterministic. Tests that want a caller-selected
    # model set it explicitly after this.
    env.pop("AGY_MODEL", None)
    env.pop("AGY_FALLBACK_MODEL", None)
    return env


def test_nonzero_agy_exit_preserves_native_diagnostic(tmp_path):
    # agy exits non-zero = a real outage (quota/crash). Even with a
    # non-empty body, a non-zero exit must degrade — never count as a
    # review (the G_RC gate).
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'printf "Authentication required by provider\\n"\n'
        'exit 1\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1, (
        f"expected degrade exit 1, got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert r.stdout == ""
    assert "Authentication required by provider" in r.stderr
    assert "本轮缺 gemini" in r.stderr


def test_invalid_mode_degrades_with_empty_stdout(tmp_path):
    _stub_agy(tmp_path / "bin", '#!/bin/sh\necho "should not run"\nexit 0\n')
    r = subprocess.run(
        ["bash", str(SCRIPT), 'bad"\nmode'],
        input=REVIEW_TASK,
        capture_output=True,
        text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1
    assert r.stdout == ""
    assert "invalid MODE" in r.stderr
    assert "本轮缺 gemini" in r.stderr
    assert "should not run" not in r.stdout


def test_auth_failure_degrades_after_one_agy_call(tmp_path):
    calls = tmp_path / "calls"
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'n=$(cat "$AGY_CALLS" 2>/dev/null || echo 0); n=$((n + 1))\n'
        'echo "$n" > "$AGY_CALLS"\n'
        'echo "Authentication required"\n'
        'exit 1\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_CALLS"] = str(calls)
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True,
        env=env,
        timeout=60,
    )
    assert r.returncode == 1
    assert r.stdout == ""
    assert calls.read_text().strip() == "1"
    assert "本轮缺 gemini" in r.stderr


def test_does_not_false_degrade_when_model_output_contains_auth_string(tmp_path):
    # If agy exits 0, even if the model output contains "Authentication required"
    # (because the reviewed repository touches auth logic), it remains a review.
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'echo "===CMR-FINDINGS-BEGIN==="\n'
        'echo "CMR-VERDICT: converged"\n'
        'echo "===CMR-FINDINGS-END==="\n'
        'echo "The reviewed source added: echo Authentication required"\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 0, (
        f"expected exit 0, got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    # Success → agy's review is passed through verbatim; the review body
    # (here a clean zero-finding result) reaches the orchestrator.
    assert "CMR-VERDICT: converged" in r.stdout
    assert "本轮缺 gemini" not in r.stderr


def test_degrades_with_clear_flag_when_agy_not_installed(tmp_path):
    # Empty stub dir → no `agy` on PATH → degrade up-front with the
    # post-EOL explanation, never silent / never crash.
    (tmp_path / "bin").mkdir()
    env = dict(os.environ)
    # Override PATH to ONLY contain the (empty) stub dir + system minimal
    # bin paths so `agy` is missing but coreutils still work.
    env["PATH"] = f"{tmp_path / 'bin'}{os.pathsep}/usr/bin{os.pathsep}/bin"

    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True, env=env, timeout=30,
    )
    assert r.returncode == 1
    assert r.stdout == ""
    assert "agy not installed" in r.stderr
    assert "本轮缺 gemini" in r.stderr


def test_review_packet_passes_to_agy_verbatim(tmp_path):
    packet = REVIEW_TASK
    prompt_dump = tmp_path / "prompt"
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'cat > "$AGY_PROMPT_DUMP"\n'
        'echo "grounded prose review"\n'
        'exit 0\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_PROMPT_DUMP"] = str(prompt_dump)
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=packet,
        capture_output=True, text=True,
        env=env,
        timeout=60,
    )
    assert r.returncode == 0, (
        f"expected exit 0, got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert prompt_dump.read_text() == packet


def test_default_invocation_pins_gemini_and_keeps_checkout_writable(tmp_path):
    # The transport chooses one explicit default model but does not impose a
    # read-only CLI sandbox. The reviewer receives the writable isolated
    # checkout selected by the orchestrator and may use its normal tools.
    dump = tmp_path / "argv.txt"
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        ': > "$AGY_ARGV_DUMP"\n'
        'for a in "$@"; do printf \'%s\\0\' "$a" >> "$AGY_ARGV_DUMP"; done\n'
        'echo "===CMR-FINDINGS-BEGIN==="\n'
        'echo "CMR-VERDICT: converged"\n'
        'echo "===CMR-FINDINGS-END==="\n'
        'exit 0\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_ARGV_DUMP"] = str(dump)
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    argv = dump.read_bytes().split(b"\0")
    if argv and argv[-1] == b"":
        argv = argv[:-1]  # drop the trailing-delimiter artifact only
    argv = [a.decode() for a in argv]
    log_path = argv[argv.index("--log-file") + 1]
    argv[argv.index("--log-file") + 1] = "<log-file>"
    assert Path(log_path).is_absolute()
    assert argv == [
        "--model",
        "Gemini 3.5 Flash (High)",
        "--print",
        "",
        "--print-timeout",
        "15m",
        "--log-file",
        "<log-file>",
    ]
    assert "--sandbox" not in argv


def test_surfaces_quota_reason_when_agy_swallows_429_to_logfile(tmp_path):
    # Real-world failure (8 empty rounds): agy hits RESOURCE_EXHAUSTED
    # (429) but routes it to its --log-file and exits 0 with EMPTY
    # stdout — so the round looked like a silent empty degrade with no
    # reason. gemini.sh now passes --log-file and greps it on degrade,
    # so the flag names the quota cause instead of just "empty output".
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in\n'
        '    --log-file) logf="$2"; shift 2 ;;\n'
        '    *) shift ;;\n'
        '  esac\n'
        'done\n'
        '[ -n "$logf" ] && printf \'%s\\n\' '
        '"E0611 agent executor error: RESOURCE_EXHAUSTED (code 429): '
        'Individual quota reached. Resets in 64h24m36s." > "$logf"\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert r.stdout == ""
    assert "本轮缺 gemini" in r.stderr
    assert "quota" in r.stderr
    assert "429" in r.stderr
    assert "Resets in 64h" in r.stderr


def test_prose_review_passes_through_not_degraded(tmp_path):
    # THE fix (gemini side, mirrors the codex one): agy exits 0 with a
    # PROSE review — no sentinel, no JSON. That is a REAL review (Gemini's
    # natural output), and must be passed through verbatim with exit 0,
    # NOT degraded to "本轮缺 gemini" as if Gemini were down. The old
    # extract_json sentinel gate dropped exactly this. The review body
    # here even quotes reviewed source containing `check_user_quota()/429` — that
    # must NOT trigger any false quota attribution either (there is no
    # degrade path to attribute, and the reason scan only reads agy's log,
    # never $RAW).
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'echo "Reviewed the diff. P2: check_user_quota() returns 429 on the"\n'
        'echo "wrong branch — see auth.py:see. Otherwise no findings."\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 0, (
        f"prose review must pass through (exit 0), not degrade; got "
        f"{r.returncode}\nstdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert "check_user_quota() returns 429 on the" in r.stdout, (
        f"gemini's prose review was not passed through. stdout={r.stdout!r}"
    )
    assert "本轮缺 gemini" not in r.stderr, (
        f"a real prose review was wrongly flagged as a missing vendor. "
        f"stderr={r.stderr!r}"
    )


def test_quota_log_without_resets_line_still_degrades_cleanly(tmp_path):
    # Cross-model review R2 (codex#2 raised an abort concern; refuted
    # empirically + by the Claude leg, locked here): when agy's log has a
    # 429/quota signature but NO "Resets in …" line, the optional
    # `resets="$(grep … | head -1)"` grep finds nothing. Under
    # `set -euo pipefail` this must NOT abort the script before it emits
    # the degrade contract — it must degrade cleanly and still name quota
    # (just without the reset-time suffix).
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in --log-file) logf="$2"; shift 2 ;; *) shift ;; esac\n'
        'done\n'
        '[ -n "$logf" ] && printf \'%s\\n\' '
        '"E agent executor error: RESOURCE_EXHAUSTED (code 429): '
        'Individual quota reached." > "$logf"\n'  # note: no "Resets in" line
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert r.stdout == ""
    assert "本轮缺 gemini" in r.stderr
    assert "quota" in r.stderr
    assert "Resets in" not in r.stderr  # no reset hint available


def test_nonempty_nonfatal_log_degrades_without_reason_suffix(tmp_path):
    # R2 companion: a non-empty agy log with neither a quota signature
    # NOR an "agent executor error:" line exercises the trailing
    # `execerr="$(grep … | head -1)"` no-match path. It too must not
    # abort under `set -euo pipefail`; degrade cleanly with no reason
    # suffix appended.
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in --log-file) logf="$2"; shift 2 ;; *) shift ;; esac\n'
        'done\n'
        '[ -n "$logf" ] && printf \'%s\\n\' '
        '"I0611 benign agy log line, nothing fatal here" > "$logf"\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert r.stdout == ""
    assert "本轮缺 gemini" in r.stderr
    assert "quota" not in r.stderr  # no false attribution from a benign log


def test_execerr_reason_is_not_truncated_at_colon(tmp_path):
    # Online R1 (sourcery): the executor-error grep used `[^:]*` and
    # truncated multi-colon messages at the first colon. It now matches
    # to end of line, so the full executor error reaches the flag.
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in --log-file) logf="$2"; shift 2 ;; *) shift ;; esac\n'
        'done\n'
        '[ -n "$logf" ] && printf \'%s\\n\' '
        '"E agent executor error: call failed: backend timeout" > "$logf"\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "agent executor error: call failed: backend timeout" in r.stderr, (
        "executor error was truncated at the first colon — should match to "
        f"end of line. stderr={r.stderr!r}"
    )


def test_quota_reason_resets_not_doubled_when_agy_logs_error_twice(tmp_path):
    # Live-surfaced bug: real agy writes the fatal error TWICE on one log
    # line ("…Resets in X.: …Resets in X."). `grep -m1 -o` caps matching
    # LINES, not matches-per-line, so it emitted both → the degrade flag
    # carried a doubled, newline-split "Resets in …". The reason must
    # contain exactly ONE "Resets in".
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in --log-file) logf="$2"; shift 2 ;; *) shift ;; esac\n'
        'done\n'
        '[ -n "$logf" ] && printf \'%s\\n\' '
        '"E RESOURCE_EXHAUSTED (code 429): Individual quota reached. Resets in 64h24m36s.: '
        'RESOURCE_EXHAUSTED (code 429): Individual quota reached. Resets in 64h24m36s." > "$logf"\n'
        'exit 0\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_MODEL"] = "x-explicit-model"
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert r.stderr.count("Resets in") == 1, (
        f"'Resets in' should appear exactly once (not doubled). stderr={r.stderr!r}"
    )
    assert "Resets in 64h24m36s" in r.stderr


def test_primary_quota_falls_back_once_to_second_pool(tmp_path):
    models = tmp_path / "models"
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""; model=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in\n'
        '    --log-file) logf="$2"; shift 2 ;;\n'
        '    --model) model="$2"; shift 2 ;;\n'
        '    *) shift ;;\n'
        '  esac\n'
        'done\n'
        'echo "$model" >> "$AGY_MODELS"\n'
        'if [ "$model" = "Gemini 3.5 Flash (High)" ]; then\n'
        '  printf \'%s\\n\' "E RESOURCE_EXHAUSTED (code 429): Individual quota reached." > "$logf"\n'
        '  exit 0\n'
        'fi\n'
        'echo "review from $model"\n'
        'exit 0\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_MODELS"] = str(models)
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True,
        env=env,
        timeout=60,
    )
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert models.read_text().splitlines() == [
        "Gemini 3.5 Flash (High)",
        "Claude Sonnet 4.6 (Thinking)",
    ]
    assert "review from Claude Sonnet 4.6 (Thinking)" in r.stdout
    assert "Claude Sonnet 4.6 (Thinking)" in r.stderr
    assert "NO Google family this round" in r.stderr


def test_bare_resource_exhausted_does_not_use_quota_fallback(tmp_path):
    models = tmp_path / "models"
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""; model=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in\n'
        '    --log-file) logf="$2"; shift 2 ;;\n'
        '    --model) model="$2"; shift 2 ;;\n'
        '    *) shift ;;\n'
        '  esac\n'
        'done\n'
        'echo "$model" >> "$AGY_MODELS"\n'
        'if [ "$model" = "primary-probe" ]; then\n'
        '  printf \'%s\\n\' "E agent executor error: RESOURCE_EXHAUSTED: backend worker pool exhausted" > "$logf"\n'
        '  exit 1\n'
        'fi\n'
        'echo "fallback review"\n'
        'exit 0\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_MODELS"] = str(models)
    env["AGY_MODEL"] = "primary-probe"
    env["AGY_FALLBACK_MODEL"] = "fallback-probe"
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n",
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert models.read_text().splitlines() == ["primary-probe"]
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert r.stdout == ""
    assert "本轮缺 gemini" in r.stderr


def test_both_quota_pools_degrade_after_exactly_two_calls(tmp_path):
    models = tmp_path / "models"
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""; model=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in\n'
        '    --log-file) logf="$2"; shift 2 ;;\n'
        '    --model) model="$2"; shift 2 ;;\n'
        '    *) shift ;;\n'
        '  esac\n'
        'done\n'
        'echo "$model" >> "$AGY_MODELS"\n'
        'printf \'%s\\n\' "E RESOURCE_EXHAUSTED (code 429): Individual quota reached." > "$logf"\n'
        'exit 0\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_MODELS"] = str(models)
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert r.stdout == ""
    assert models.read_text().splitlines() == [
        "Gemini 3.5 Flash (High)",
        "Claude Sonnet 4.6 (Thinking)",
    ]
    assert "本轮缺 gemini" in r.stderr
    assert "quota" in r.stderr


def test_empty_fallback_disables_second_quota_call(tmp_path):
    calls = tmp_path / "calls"
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'n=$(cat "$AGY_CALLS" 2>/dev/null || echo 0); n=$((n + 1))\n'
        'echo "$n" > "$AGY_CALLS"\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in --log-file) logf="$2"; shift 2 ;; *) shift ;; esac\n'
        'done\n'
        'printf \'%s\\n\' "E RESOURCE_EXHAUSTED (code 429): Individual quota reached." > "$logf"\n'
        'exit 0\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_CALLS"] = str(calls)
    env["AGY_FALLBACK_MODEL"] = ""
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert r.stdout == ""
    assert calls.read_text().strip() == "1"
    assert "本轮缺 gemini" in r.stderr
    assert "quota" in r.stderr


def test_quota_with_nonempty_banner_still_degrades(tmp_path):
    # agy can return zero and print a non-empty diagnostic banner even when
    # the selected model exhausted quota. The fatal log, not stdout shape,
    # distinguishes that outage from a real prose review.
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in --log-file) logf="$2"; shift 2 ;; *) shift ;; esac\n'
        'done\n'
        '[ -n "$logf" ] && printf \'%s\\n\' '
        '"E RESOURCE_EXHAUSTED (code 429): Individual quota reached." > "$logf"\n'
        'echo "agy: some diagnostic banner on stdout"\n'  # NON-empty stdout
        'exit 0\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_MODEL"] = "x-explicit-model"
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 1, (
        f"a quota-exhausted model with a non-empty banner must degrade, "
        f"not pass the banner through as a review; got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert "本轮缺 gemini" in r.stderr
    assert "quota" in r.stderr
    assert r.stdout == ""
    assert "some diagnostic banner" not in r.stdout, (
        "the quota banner was passed through as if it were a review"
    )


def test_default_gemini_review_passes_through(tmp_path):
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'echo "===CMR-FINDINGS-BEGIN==="\n'
        'echo "CMR-VERDICT: converged"\n'
        'echo "===CMR-FINDINGS-END==="\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "CMR-VERDICT: converged" in r.stdout  # Gemini's review passed through
    assert "NO Google family" not in r.stderr


def test_agy_explicit_override_note_when_non_google_model_used(tmp_path):
    # A caller may choose a different model, but the adapter must report its
    # actual non-Google family rather than pretending the leg was Gemini.
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'echo "===CMR-FINDINGS-BEGIN==="\n'
        'echo "CMR-VERDICT: converged"\n'
        'echo "===CMR-FINDINGS-END==="\n'
        'exit 0\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_MODEL"] = "Claude Sonnet 4.6 (Thinking)"
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "explicit AGY_MODEL override" in r.stderr
    assert "NO Google family this round" in r.stderr
    assert "3rd voice" not in r.stderr


def test_gpt_oss_override_is_flagged_as_non_google_family(tmp_path):
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'echo "review from GPT-OSS"\n'
        'exit 0\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_MODEL"] = "GPT-OSS 120B"
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "NO Google family this round" in r.stderr
    assert "GPT-OSS 120B" in r.stderr


def _run_gemini_in_cwd(cwd_dir: Path, tmp_path):
    """Run the real gemini.sh with cwd=cwd_dir and agy MISSING (so it
    degrades right after the hidden-path check). cwd_dir is a non-git
    directory, so REVIEW_ROOT = `git rev-parse … || pwd` resolves to
    cwd_dir itself — letting a test place the *reviewed repo root* under a
    hidden vs visible path to exercise both branches of the warning. (The
    warning now keys on REVIEW_ROOT, not the skill's own dir.)"""
    cwd_dir.mkdir(parents=True, exist_ok=True)
    bindir = tmp_path / "emptybin"
    bindir.mkdir(exist_ok=True)
    # Stub `git` to fail so gemini.sh's `git rev-parse --show-toplevel ||
    # pwd` deterministically falls back to pwd (= cwd_dir). Without this,
    # if the test tmpdir happens to sit inside a git repo (common in CI),
    # rev-parse would resolve to the ENCLOSING repo's toplevel and
    # REVIEW_ROOT would not be cwd_dir, false-failing the hidden/visible
    # assertions (online R2: gemini-code-assist).
    git_stub = bindir / "git"
    git_stub.write_text("#!/bin/sh\nexit 1\n")
    git_stub.chmod(git_stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    env = dict(os.environ)
    env["PATH"] = f"{bindir}{os.pathsep}/usr/bin{os.pathsep}/bin"
    env.pop("AGY_MODEL", None)
    return subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input=REVIEW_TASK,
        capture_output=True, text=True, env=env, cwd=str(cwd_dir), timeout=30,
    )


def test_warns_when_reviewed_repo_root_under_hidden_dir(tmp_path):
    # The reviewed repo (REVIEW_ROOT, = where cmr is invoked) is under a
    # hidden (dot) path → agy refuses it as a workspace folder, the
    # reviewer loses repo context. The backend must warn (not silently
    # degrade). NOTE this keys on the REVIEWED repo, not the skill's dir.
    if "/." in str(tmp_path):
        pytest.skip(f"base temp dir is itself under a hidden component: {tmp_path}")
    r = _run_gemini_in_cwd(tmp_path / ".hidden" / "repo", tmp_path)
    assert r.returncode == 1
    assert "agy not installed" in r.stderr  # degraded AFTER the warning
    assert "hidden" in r.stderr
    assert "without repo context" in r.stderr.lower()
    assert "reviewed repo root" in r.stderr  # not "the skill's dir"


def test_no_hidden_warning_when_reviewed_repo_root_visible(tmp_path):
    # The other branch: a normal (non-hidden) reviewed repo root must NOT
    # emit the hidden-path warning — the key fix is that the skill living
    # under ~/.claude/ (hidden) no longer makes this fire on every run.
    if "/." in str(tmp_path):
        pytest.skip(f"base temp dir is itself under a hidden component: {tmp_path}")
    r = _run_gemini_in_cwd(tmp_path / "visible" / "repo", tmp_path)
    assert r.returncode == 1
    assert "agy not installed" in r.stderr
    assert "hidden" not in r.stderr
