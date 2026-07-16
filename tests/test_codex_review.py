"""Minimal contract tests for the Codex reviewer transport."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "codex-review.sh"
PACKET = "Review fixed range 111...222; authority: AGENTS.md.\n"


def _stub(path: Path, body: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    exe = path / "codex"
    exe.write_text(
        "#!/bin/sh\n"
        'OUT=""\n'
        ': > "${ARGV_DUMP:-/dev/null}"\n'
        'for arg in "$@"; do printf "%s\\0" "$arg" >> "${ARGV_DUMP:-/dev/null}"; done\n'
        'while [ $# -gt 0 ]; do case "$1" in -o) OUT="$2"; shift 2;; *) shift;; esac; done\n'
        + body
    )
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run(stub: Path, cwd: Path | None = None, **extra: str):
    env = dict(os.environ)
    env.update(
        PATH=f"{stub}{os.pathsep}{env['PATH']}",
        CMR_CODEX_TIMEOUT="15",
        CMR_CODEX_IDLE_POLL="1",
    )
    env.update(extra)
    return subprocess.run(
        ["bash", str(SCRIPT), "code"], input=PACKET, cwd=cwd,
        capture_output=True, text=True, env=env, timeout=60,
    )


def _argv(path: Path) -> list[str]:
    return [part.decode() for part in path.read_bytes().split(b"\0") if part]


def test_official_argv_prompt_cwd_and_last_message(tmp_path):
    argv_dump, prompt_dump, cwd_dump = (
        tmp_path / "argv", tmp_path / "prompt", tmp_path / "cwd"
    )
    clone = tmp_path / "clone"
    clone.mkdir()
    _stub(
        tmp_path / "bin",
        'cat > "$PROMPT_DUMP"\n'
        'pwd > "$CWD_DUMP"\n'
        'echo "transport trace, not review"\n'
        'printf "grounded review\\n" > "$OUT"\n',
    )
    result = _run(
        tmp_path / "bin", cwd=clone, ARGV_DUMP=str(argv_dump),
        PROMPT_DUMP=str(prompt_dump), CWD_DUMP=str(cwd_dump),
    )
    argv = _argv(argv_dump)
    assert argv[:7] == [
        "exec", "--ephemeral", "-c", "model_reasoning_effort=medium",
        "--model", "gpt-5.6-sol", "-o",
    ]
    assert Path(argv[7]).is_absolute() and argv[8] == "-"
    assert prompt_dump.read_text() == PACKET
    assert Path(cwd_dump.read_text().strip()) == clone
    assert result.returncode == 0 and result.stdout == "grounded review\n"
    assert "transport trace" not in result.stdout


def test_model_and_effort_overrides_keep_the_same_invocation_shape():
    env = dict(os.environ, CMR_CODEX_MODEL="luna", CMR_CODEX_EFFORT="high")
    result = subprocess.run(
        ["bash", str(SCRIPT), "--selftest"], capture_output=True, text=True,
        env=env, timeout=30,
    )
    assert result.returncode == 0
    assert "model_reasoning_effort=high" in result.stdout
    assert "--model luna" in result.stdout


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ('echo "provider failed"; exit 7\n', "exited non-zero"),
        ('echo "trace only"; exit 0\n', "wrote no final message"),
    ],
)
def test_nonzero_or_empty_final_message_degrades(tmp_path, body, reason):
    _stub(tmp_path / "bin", body)
    result = _run(tmp_path / "bin")
    assert result.returncode == 1 and result.stdout == ""
    assert reason in result.stderr and "本轮缺 codex" in result.stderr


def test_streaming_is_idle_not_wall_clock_limited(tmp_path):
    _stub(
        tmp_path / "bin",
        'for i in 1 2 3 4; do echo "chunk $i"; sleep 1; done\n'
        'printf "review after long total time\\n" > "$OUT"\n',
    )
    result = _run(tmp_path / "bin", CMR_CODEX_TIMEOUT="2")
    assert result.returncode == 0
    assert result.stdout == "review after long total time\n"


def test_exit_during_watchdog_sleep_is_not_a_timeout(tmp_path):
    _stub(
        tmp_path / "bin",
        'echo started; sleep 3; printf "grounded review\\n" > "$OUT"\n',
    )
    result = _run(
        tmp_path / "bin", CMR_CODEX_TIMEOUT="2", CMR_CODEX_IDLE_POLL="2"
    )
    assert result.returncode == 0 and result.stdout == "grounded review\n"
    assert "timeout/kill" not in result.stderr


def test_silent_process_is_killed_after_idle_window(tmp_path):
    _stub(tmp_path / "bin", 'echo started; sleep 30\n')
    result = _run(tmp_path / "bin", CMR_CODEX_TIMEOUT="2")
    assert result.returncode == 1 and result.stdout == ""
    assert "started" in result.stderr
    assert "timeout/kill" in result.stderr and "本轮缺 codex" in result.stderr
