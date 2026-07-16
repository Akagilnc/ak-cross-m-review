"""Minimal contract tests for the OpenCode reviewer transport."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "opencode-review.sh"
PACKET = "Review fixed range 111...222; authority: AGENTS.md.\n"


def _stub(path: Path, body: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    exe = path / "opencode"
    exe.write_text("#!/bin/sh\n" + body)
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run(stub: Path, cwd: Path | None = None, **extra: str):
    env = dict(os.environ)
    env["PATH"] = f"{stub}{os.pathsep}{env['PATH']}"
    env.pop("CMR_OPENCODE_MODEL", None)
    env.pop("CMR_OPENCODE_VARIANT", None)
    env.update(extra)
    return subprocess.run(
        ["bash", str(SCRIPT), "code"], input=PACKET, cwd=cwd,
        capture_output=True, text=True, env=env, timeout=30,
    )


def _argv(path: Path) -> list[str]:
    return [part.decode() for part in path.read_bytes().split(b"\0") if part]


@pytest.mark.parametrize(
    ("model", "variant"),
    [("opencode-go/glm-5.2", None), ("provider/custom model", "max")],
)
def test_official_argv_prompt_cwd_and_success(tmp_path, model, variant):
    argv_dump, prompt_dump, cwd_dump = (
        tmp_path / "argv", tmp_path / "prompt", tmp_path / "cwd"
    )
    clone = tmp_path / "clone"
    subprocess.run(["git", "init", "-q", str(clone)], check=True)
    _stub(
        tmp_path / "bin",
        ': > "$ARGV_DUMP"; for arg in "$@"; do printf "%s\\0" "$arg" >> "$ARGV_DUMP"; done\n'
        'prompt=""; while [ $# -gt 0 ]; do case "$1" in --file) prompt="$2"; shift 2;; *) shift;; esac; done\n'
        'cp "$prompt" "$PROMPT_DUMP"; pwd > "$CWD_DUMP"\n'
        'printf "grounded review\\n"\n',
    )
    extra = {
        "ARGV_DUMP": str(argv_dump), "PROMPT_DUMP": str(prompt_dump),
        "CWD_DUMP": str(cwd_dump),
    }
    if variant:
        extra.update(CMR_OPENCODE_MODEL=model, CMR_OPENCODE_VARIANT=variant)
    result = _run(tmp_path / "bin", cwd=clone, **extra)
    argv = _argv(argv_dump)
    prompt_path = argv[argv.index("--file") + 1]
    argv[argv.index("--file") + 1] = "<prompt-file>"
    expected = ["run", "--pure", "--format", "default", "--model", model]
    if variant:
        expected += ["--variant", variant]
    expected += [
        "--file", "<prompt-file>", "--dir", str(clone),
        "Review the attached packet and return only the grounded prose review.",
    ]
    assert Path(prompt_path).is_absolute() and argv == expected
    assert prompt_dump.read_text() == PACKET
    assert Path(cwd_dump.read_text().strip()) == clone
    assert result.returncode == 0 and result.stdout == "grounded review\n"


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ('echo "provider failed" >&2; exit 7\n', "opencode exit rc=7"),
        ("exit 0\n", "empty output"),
    ],
)
def test_nonzero_or_empty_output_degrades(tmp_path, body, reason):
    _stub(tmp_path / "bin", body)
    result = _run(tmp_path / "bin")
    assert result.returncode == 1 and result.stdout == ""
    assert reason in result.stderr and "本轮缺 opencode" in result.stderr


def test_nonzero_stdout_diagnostic_is_preserved_before_degrade(tmp_path):
    _stub(tmp_path / "bin", 'echo "native opencode fatal"; exit 7\n')
    result = _run(tmp_path / "bin")
    assert result.returncode == 1 and result.stdout == ""
    assert result.stderr.index("native opencode fatal") < result.stderr.index(
        "opencode-review: degrade"
    )


def test_non_git_cwd_stops_before_opencode_and_preserves_git_error(tmp_path):
    ran = tmp_path / "ran"
    _stub(tmp_path / "bin", ': > "$RAN"; echo "unexpected review"\n')
    result = _run(tmp_path / "bin", cwd=tmp_path, RAN=str(ran))
    assert result.returncode != 0 and result.stdout == "" and not ran.exists()
    assert "fatal: not a git repository" in result.stderr
