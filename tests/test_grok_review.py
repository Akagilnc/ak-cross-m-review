"""Minimal contract tests for the Grok reviewer transport."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "grok-review.sh"
PACKET = "Review fixed range 111...222; authority: AGENTS.md.\n"


def _stub(path: Path, body: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    exe = path / "grok"
    exe.write_text("#!/bin/sh\n" + body)
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run(stub: Path, cwd: Path | None = None, **extra: str):
    env = dict(os.environ)
    env["PATH"] = f"{stub}{os.pathsep}{env['PATH']}"
    env.pop("CMR_GROK_MODEL", None)
    env.pop("CMR_GROK_EFFORT", None)
    env.update(extra)
    return subprocess.run(
        ["bash", str(SCRIPT), "code"], input=PACKET, cwd=cwd,
        capture_output=True, text=True, env=env, timeout=30,
    )


def _argv(path: Path) -> list[str]:
    return [part.decode() for part in path.read_bytes().split(b"\0") if part]


@pytest.mark.parametrize(
    ("model", "effort"),
    [("grok-4.5", "high"), ("custom grok model", "xhigh")],
)
def test_official_argv_prompt_cwd_and_success(tmp_path, model, effort):
    argv_dump, prompt_dump, cwd_dump = (
        tmp_path / "argv", tmp_path / "prompt", tmp_path / "cwd"
    )
    clone = tmp_path / "clone"
    clone.mkdir()
    _stub(
        tmp_path / "bin",
        ': > "$ARGV_DUMP"; for arg in "$@"; do printf "%s\\0" "$arg" >> "$ARGV_DUMP"; done\n'
        'prompt=""; while [ $# -gt 0 ]; do case "$1" in --prompt-file) prompt="$2"; shift 2;; *) shift;; esac; done\n'
        'cp "$prompt" "$PROMPT_DUMP"; pwd > "$CWD_DUMP"\n'
        'printf "%s" "${RUST_LOG-unset}" > "$RUST_LOG_DUMP"\n'
        'printf "grounded review\\n"\n',
    )
    extra = {
        "ARGV_DUMP": str(argv_dump), "PROMPT_DUMP": str(prompt_dump),
        "CWD_DUMP": str(cwd_dump), "RUST_LOG_DUMP": str(tmp_path / "rust"),
    }
    if model != "grok-4.5":
        extra.update(CMR_GROK_MODEL=model, CMR_GROK_EFFORT=effort)
    result = _run(tmp_path / "bin", cwd=clone, **extra)
    argv = _argv(argv_dump)
    prompt_path = argv[argv.index("--prompt-file") + 1]
    argv[argv.index("--prompt-file") + 1] = "<prompt-file>"
    assert Path(prompt_path).is_absolute()
    assert argv == [
        "--no-memory", "--no-subagents", "--prompt-file", "<prompt-file>",
        "--model", model, "--reasoning-effort", effort,
        "--output-format", "plain",
    ]
    assert prompt_dump.read_text() == PACKET
    assert Path(cwd_dump.read_text().strip()) == clone
    assert (tmp_path / "rust").read_text() == "off"
    assert result.returncode == 0 and result.stdout == "grounded review\n"


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ('echo "provider failed" >&2; exit 7\n', "grok exit rc=7"),
        ("exit 0\n", "empty output"),
    ],
)
def test_nonzero_or_empty_output_degrades(tmp_path, body, reason):
    _stub(tmp_path / "bin", body)
    result = _run(tmp_path / "bin")
    assert result.returncode == 1 and result.stdout == ""
    assert reason in result.stderr and "本轮缺 grok" in result.stderr


def test_nonzero_stdout_diagnostic_is_preserved_before_degrade(tmp_path):
    _stub(tmp_path / "bin", 'echo "native grok fatal"; exit 7\n')
    result = _run(tmp_path / "bin")
    assert result.returncode == 1 and result.stdout == ""
    assert result.stderr.index("native grok fatal") < result.stderr.index(
        "grok-review: degrade"
    )
