"""Behavioral tests for the Claude reviewer backend."""

import json
import os
import shutil
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


def _successful_stream(*chunks: str, final_result: str | None = None) -> str:
    events = [{"type": "system", "subtype": "init"}]
    events.extend(
        {
            "type": "stream_event",
            "event": {
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": chunk},
            },
        }
        for chunk in chunks
    )
    events.append(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": final_result if final_result is not None else "".join(chunks),
        }
    )
    stream = "\n".join(json.dumps(event) for event in events)
    return f"cat <<'EOF'\n{stream}\nEOF\nexit 0\n"


def _run_claude(
    stub_dir: Path,
    mode: str = "code",
    cwd: Path | None = None,
    **env_extra: str,
):
    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env.pop("CMR_CLAUDE_MODEL", None)
    env.update(env_extra)
    return subprocess.run(
        ["/bin/bash", str(SCRIPT), mode],
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
    _stub_claude(tmp_path / "bin", _successful_stream("grounded prose review\n"))

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
        + _successful_stream("review complete\n"),
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
        "--permission-mode",
        "acceptEdits",
        "--allowedTools",
        "Bash",
        "--output-format",
        "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--no-session-persistence",
    ]
    assert prompt_dump.read_text() == REVIEW_TASK


def test_model_override_passes_through_as_one_argument_without_effort(tmp_path):
    argv_dump = tmp_path / "argv"
    _stub_claude(
        tmp_path / "bin",
        ': > "$CLAUDE_ARGV_DUMP"\n'
        'for arg in "$@"; do printf "%s\\0" "$arg" >> "$CLAUDE_ARGV_DUMP"; done\n'
        + _successful_stream("review complete\n"),
    )

    result = _run_claude(
        tmp_path / "bin",
        CLAUDE_ARGV_DUMP=str(argv_dump),
        CMR_CLAUDE_MODEL="custom claude model",
    )

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    argv = _read_argv(argv_dump)
    assert argv[argv.index("--model") + 1] == "custom claude model"
    assert "--effort" not in argv


def test_reviewer_inherits_the_callers_writable_clone(tmp_path):
    clone = tmp_path / "reviewer-clone"
    clone.mkdir()
    cwd_dump = tmp_path / "cwd"
    _stub_claude(
        tmp_path / "bin",
        'pwd > "$CLAUDE_CWD_DUMP"\n'
        'printf "probe" > reviewer-tool-probe\n'
        + _successful_stream("review complete\n"),
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
    _stub_claude(tmp_path / "bin", _successful_stream("document review\n"))

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


def test_missing_jq_degrades_before_claude_runs(tmp_path):
    stub_dir = tmp_path / "bin"
    ran = tmp_path / "claude-ran"
    _stub_claude(
        stub_dir,
        ': > "$CLAUDE_RAN"\n'
        'printf "should not run\\n"\n'
        'exit 0\n',
    )
    for tool in ("mktemp", "rm"):
        resolved = shutil.which(tool)
        assert resolved is not None
        (stub_dir / tool).symlink_to(resolved)

    result = _run_claude(
        stub_dir,
        PATH=str(stub_dir),
        CLAUDE_RAN=str(ran),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert not ran.exists()
    assert "jq unavailable" in result.stderr
    assert "本轮缺 claude" in result.stderr


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


def test_result_without_text_deltas_degrades_visibly(tmp_path):
    _stub_claude(
        tmp_path / "bin",
        _successful_stream(final_result="result-only answer"),
    )

    result = _run_claude(tmp_path / "bin")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "no text deltas" in result.stderr
    assert "本轮缺 claude" in result.stderr


def test_late_background_notification_cannot_replace_the_review(tmp_path):
    _stub_claude(
        tmp_path / "bin",
        "cat <<'EOF'\n"
        '{"type":"system","subtype":"init"}\n'
        '{"type":"stream_event","event":{"type":"content_block_delta",'
        '"delta":{"type":"text_delta","text":"grounded main review\\n"}}}\n'
        '{"type":"user","message":{"content":['
        '{"type":"tool_result","tool_use_id":"wait-1",'
        '"content":"background wait timer completed"}]}}\n'
        '{"type":"stream_event","event":{"type":"content_block_delta",'
        '"delta":{"type":"text_delta","text":"leftover timer; no action needed\\n"}}}\n'
        '{"type":"result","subtype":"success","is_error":false,'
        '"result":"leftover timer; no action needed"}\n'
        "EOF\n"
        "exit 0\n",
    )

    result = _run_claude(tmp_path / "bin")

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout == (
        "grounded main review\nleftover timer; no action needed\n"
    )
