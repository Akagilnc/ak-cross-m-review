"""Behavioral tests for the Claude reviewer backend."""

import os
import stat
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "claude-review.sh"
REVIEW_TASK = (
    "Review fixed range 111...222 from this clone; run git diff --binary "
    "111...222; authority: AGENTS.md.\n"
)


def _stub_claude(stub_dir: Path, body: str) -> None:
    stub_dir.mkdir(parents=True, exist_ok=True)
    claude = stub_dir / "claude"
    claude.write_text(f"#!/bin/sh\n{body}")
    claude.chmod(claude.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run_claude(
    stub_dir: Path,
    mode: str = "code",
    cwd: Path | None = None,
    **env_extra: str,
):
    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env.pop("CMR_CLAUDE_MODEL", None)
    env.pop("CMR_CLAUDE_EFFORT", None)
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT), mode],
        input=REVIEW_TASK,
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
        timeout=30,
    )


def _read_argv(path: Path) -> list[str]:
    argv = path.read_bytes().split(b"\0")
    if argv and argv[-1] == b"":
        argv = argv[:-1]
    return [arg.decode() for arg in argv]


def test_success_passes_review_prose_through_verbatim(tmp_path):
    _stub_claude(tmp_path / "bin", 'printf "grounded prose review\\n"\nexit 0\n')

    result = _run_claude(tmp_path / "bin")

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout == "grounded prose review\n"


def test_default_invocation_is_one_tool_enabled_nonpersistent_review(tmp_path):
    argv_dump = tmp_path / "argv"
    prompt_dump = tmp_path / "prompt"
    _stub_claude(
        tmp_path / "bin",
        ': > "$CLAUDE_ARGV_DUMP"\n'
        'for arg in "$@"; do printf "%s\\0" "$arg" >> "$CLAUDE_ARGV_DUMP"; done\n'
        'cat > "$CLAUDE_PROMPT_DUMP"\n'
        'printf "review complete\\n"\n'
        'exit 0\n',
    )

    result = _run_claude(
        tmp_path / "bin",
        CLAUDE_ARGV_DUMP=str(argv_dump),
        CLAUDE_PROMPT_DUMP=str(prompt_dump),
        ANTHROPIC_MODEL="claude-fable-5",
    )

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert _read_argv(argv_dump) == [
        "-p",
        "--model",
        "claude-opus-4-8",
        "--effort",
        "high",
        "--output-format",
        "text",
        "--no-session-persistence",
    ]
    assert prompt_dump.read_text() == REVIEW_TASK


def test_model_and_effort_overrides_pass_through_as_single_arguments(tmp_path):
    argv_dump = tmp_path / "argv"
    _stub_claude(
        tmp_path / "bin",
        ': > "$CLAUDE_ARGV_DUMP"\n'
        'for arg in "$@"; do printf "%s\\0" "$arg" >> "$CLAUDE_ARGV_DUMP"; done\n'
        'printf "review complete\\n"\n'
        'exit 0\n',
    )

    result = _run_claude(
        tmp_path / "bin",
        CLAUDE_ARGV_DUMP=str(argv_dump),
        CMR_CLAUDE_MODEL="custom claude model",
        CMR_CLAUDE_EFFORT="xhigh",
    )

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    argv = _read_argv(argv_dump)
    assert argv[argv.index("--model") + 1] == "custom claude model"
    assert argv[argv.index("--effort") + 1] == "xhigh"


def test_reviewer_inherits_the_callers_writable_clone(tmp_path):
    clone = tmp_path / "reviewer-clone"
    clone.mkdir()
    cwd_dump = tmp_path / "cwd"
    _stub_claude(
        tmp_path / "bin",
        'pwd > "$CLAUDE_CWD_DUMP"\n'
        'printf "probe" > reviewer-tool-probe\n'
        'printf "review complete\\n"\n'
        'exit 0\n',
    )

    result = _run_claude(
        tmp_path / "bin",
        cwd=clone,
        CLAUDE_CWD_DUMP=str(cwd_dump),
    )

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert Path(cwd_dump.read_text().strip()) == clone
    assert (clone / "reviewer-tool-probe").read_text() == "probe"


def test_doc_mode_runs_the_same_review_transport(tmp_path):
    _stub_claude(tmp_path / "bin", 'printf "document review\\n"\nexit 0\n')

    result = _run_claude(tmp_path / "bin", mode="doc")

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout == "document review\n"


def test_invalid_mode_degrades_before_claude_runs(tmp_path):
    _stub_claude(tmp_path / "bin", 'printf "should not run\\n"\nexit 0\n')

    result = _run_claude(tmp_path / "bin", mode='bad"\nmode')

    assert result.returncode == 1
    assert result.stdout == ""
    assert "invalid MODE" in result.stderr
    assert "本轮缺 claude" in result.stderr
    assert "should not run" not in result.stdout


def test_nonzero_claude_exit_degrades_without_leaking_partial_review(tmp_path):
    _stub_claude(
        tmp_path / "bin",
        'printf "P1-looking but failed review\\n"\n'
        'printf "provider failure\\n" >&2\n'
        'exit 7\n',
    )

    result = _run_claude(tmp_path / "bin")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "provider failure" in result.stderr
    assert "claude exit rc=7" in result.stderr
    assert "本轮缺 claude" in result.stderr


def test_empty_claude_output_degrades_visibly(tmp_path):
    _stub_claude(
        tmp_path / "bin",
        'printf "provider returned no final answer\\n" >&2\n'
        'exit 0\n',
    )

    result = _run_claude(tmp_path / "bin")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "provider returned no final answer" in result.stderr
    assert "empty output" in result.stderr
    assert "本轮缺 claude" in result.stderr
