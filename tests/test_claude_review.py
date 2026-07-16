"""Minimal contract tests for the Claude reviewer transport."""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "claude-review.sh"
PACKET = "Review fixed range 111...222; authority: AGENTS.md.\n"


def _stream(*chunks: str) -> str:
    events = [
        {"type": "stream_event", "event": {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": chunk},
        }} for chunk in chunks
    ]
    events.append({
        "type": "result", "subtype": "success", "is_error": False,
        "result": chunks[-1] if chunks else "",
    })
    return "\n".join(json.dumps(event) for event in events)


def _stub(path: Path, body: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    exe = path / "claude"
    exe.write_text("#!/bin/sh\n" + body)
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run(stub: Path, cwd: Path | None = None, **extra: str):
    env = dict(os.environ)
    env["PATH"] = f"{stub}{os.pathsep}{env['PATH']}"
    env.pop("CMR_CLAUDE_MODEL", None)
    env.update(extra)
    return subprocess.run(
        ["/bin/bash", str(SCRIPT), "code"], input=PACKET, cwd=cwd,
        capture_output=True, text=True, env=env, timeout=30,
    )


def _argv(path: Path) -> list[str]:
    return [part.decode() for part in path.read_bytes().split(b"\0") if part]


@pytest.mark.parametrize(
    ("model", "expected"),
    [(None, "claude-opus-4-8"), ("custom claude model", "custom claude model")],
)
def test_official_argv_prompt_cwd_and_success(tmp_path, model, expected):
    argv_dump = tmp_path / "argv"
    prompt_dump = tmp_path / "prompt"
    cwd_dump = tmp_path / "cwd"
    clone = tmp_path / "clone"
    clone.mkdir()
    stream = _stream("grounded review\n")
    _stub(
        tmp_path / "bin",
        ': > "$ARGV_DUMP"\n'
        'for arg in "$@"; do printf "%s\\0" "$arg" >> "$ARGV_DUMP"; done\n'
        'cat > "$PROMPT_DUMP"\n'
        'pwd > "$CWD_DUMP"\n'
        f"cat <<'EOF'\n{stream}\nEOF\n",
    )
    extra = {
        "ARGV_DUMP": str(argv_dump), "PROMPT_DUMP": str(prompt_dump),
        "CWD_DUMP": str(cwd_dump),
    }
    if model is not None:
        extra["CMR_CLAUDE_MODEL"] = model
    result = _run(tmp_path / "bin", cwd=clone, **extra)
    assert _argv(argv_dump) == [
        "-p", "--model", expected, "--permission-mode", "acceptEdits",
        "--allowedTools", "Bash", "--output-format", "stream-json",
        "--verbose", "--include-partial-messages", "--no-session-persistence",
    ]
    assert prompt_dump.read_text() == PACKET
    assert Path(cwd_dump.read_text().strip()) == clone
    assert result.returncode == 0 and result.stdout == "grounded review\n"
    assert "--effort" not in _argv(argv_dump)


def test_jq_is_required_before_claude_runs(tmp_path):
    ran = tmp_path / "ran"
    _stub(tmp_path / "bin", ': > "$RAN"\n')
    for tool in ("mktemp", "rm"):
        (tmp_path / "bin" / tool).symlink_to(shutil.which(tool))
    result = _run(tmp_path / "bin", PATH=str(tmp_path / "bin"), RAN=str(ran))
    assert result.returncode == 1 and result.stdout == "" and not ran.exists()
    assert "jq unavailable" in result.stderr and "本轮缺 claude" in result.stderr


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ('echo "provider failed" >&2; exit 7\n', "claude exit rc=7"),
        ("exit 0\n", "empty output"),
    ],
)
def test_nonzero_or_empty_output_degrades(tmp_path, body, reason):
    _stub(tmp_path / "bin", body)
    result = _run(tmp_path / "bin")
    assert result.returncode == 1 and result.stdout == ""
    assert reason in result.stderr and "本轮缺 claude" in result.stderr


def test_background_notification_cannot_replace_main_review(tmp_path):
    stream = _stream("grounded main review\n", "leftover timer; no action needed\n")
    _stub(tmp_path / "bin", f"cat <<'EOF'\n{stream}\nEOF\n")
    result = _run(tmp_path / "bin")
    assert result.returncode == 0
    assert result.stdout == (
        "grounded main review\nleftover timer; no action needed\n"
    )
