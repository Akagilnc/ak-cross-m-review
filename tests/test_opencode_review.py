"""Behavioral tests for the OpenCode reviewer backend."""

import os
import stat
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "opencode-review.sh"
ROOT = SCRIPT.parents[1]


def _stub_opencode(stub_dir: Path, body: str) -> None:
    stub_dir.mkdir(parents=True, exist_ok=True)
    opencode = stub_dir / "opencode"
    opencode.write_text(f"#!/bin/sh\n{body}")
    opencode.chmod(
        opencode.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    )


def _run_opencode(
    stub_dir: Path,
    mode: str = "code",
    cwd: Path | None = None,
    **env_extra: str,
):
    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env.pop("CMR_OPENCODE_MODEL", None)
    env.pop("CMR_OPENCODE_VARIANT", None)
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT), mode],
        input="review packet\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
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
    _stub_opencode(tmp_path / "bin", 'printf "grounded prose review\\n"\nexit 0\n')

    result = _run_opencode(tmp_path / "bin")

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout == "grounded prose review\n"


def test_default_invocation_is_pure_attachment_based_and_repo_scoped(tmp_path):
    argv_dump = tmp_path / "argv"
    cwd_dump = tmp_path / "cwd"
    _stub_opencode(
        tmp_path / "bin",
        ': > "$OPENCODE_ARGV_DUMP"\n'
        'for arg in "$@"; do printf "%s\\0" "$arg" >> "$OPENCODE_ARGV_DUMP"; done\n'
        'pwd > "$OPENCODE_CWD_DUMP"\n'
        'printf "review complete\\n"\n'
        'exit 0\n',
    )

    result = _run_opencode(
        tmp_path / "bin",
        cwd=ROOT / "tests",
        OPENCODE_ARGV_DUMP=str(argv_dump),
        OPENCODE_CWD_DUMP=str(cwd_dump),
    )

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    argv = _read_argv(argv_dump)
    assert Path(argv[7]).is_absolute()
    argv[7] = "<prompt-file>"
    assert argv == [
        "run",
        "--pure",
        "--format",
        "default",
        "--model",
        "opencode-go/glm-5.2",
        "--file",
        "<prompt-file>",
        "--dir",
        str(ROOT),
        "Review the attached packet and return only the grounded prose review.",
    ]
    assert cwd_dump.read_text().strip() == str(ROOT)


def test_model_override_and_nonempty_variant_pass_through(tmp_path):
    argv_dump = tmp_path / "argv"
    _stub_opencode(
        tmp_path / "bin",
        ': > "$OPENCODE_ARGV_DUMP"\n'
        'for arg in "$@"; do printf "%s\\0" "$arg" >> "$OPENCODE_ARGV_DUMP"; done\n'
        'printf "review complete\\n"\n'
        'exit 0\n',
    )

    result = _run_opencode(
        tmp_path / "bin",
        OPENCODE_ARGV_DUMP=str(argv_dump),
        CMR_OPENCODE_MODEL="custom-provider/custom-model",
        CMR_OPENCODE_VARIANT="max",
    )

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    argv = _read_argv(argv_dump)
    assert argv[argv.index("--model") + 1] == "custom-provider/custom-model"
    assert argv[argv.index("--variant") + 1] == "max"


def test_attached_packet_enforces_review_only_without_modifying_or_fixing(tmp_path):
    prompt_dump = tmp_path / "prompt"
    _stub_opencode(
        tmp_path / "bin",
        'prompt_file=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in\n'
        '    --file) prompt_file="$2"; shift 2 ;;\n'
        '    *) shift ;;\n'
        '  esac\n'
        'done\n'
        'cp "$prompt_file" "$OPENCODE_PROMPT_DUMP"\n'
        'printf "review complete\\n"\n'
        'exit 0\n',
    )

    result = _run_opencode(
        tmp_path / "bin", OPENCODE_PROMPT_DUMP=str(prompt_dump)
    )

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    prompt = prompt_dump.read_text()
    assert "REVIEW ONLY" in prompt
    assert "Do NOT modify, create, rename, or delete any file" in prompt
    assert "do NOT fix findings yourself" in prompt
    assert "review packet\n--- BEGIN DIFF ---" in prompt


def test_invalid_mode_degrades_before_opencode_runs(tmp_path):
    _stub_opencode(tmp_path / "bin", 'printf "should not run\\n"\nexit 0\n')

    result = _run_opencode(tmp_path / "bin", mode='bad"\nmode')

    assert result.returncode == 1
    assert result.stdout == ""
    assert "invalid MODE" in result.stderr
    assert "本轮缺 opencode" in result.stderr
    assert "should not run" not in result.stdout


def test_doc_mode_runs_the_same_review_transport(tmp_path):
    _stub_opencode(tmp_path / "bin", 'printf "document review\\n"\nexit 0\n')

    result = _run_opencode(tmp_path / "bin", mode="doc")

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout == "document review\n"


def test_nonzero_opencode_exit_degrades_without_leaking_stdout(tmp_path):
    _stub_opencode(
        tmp_path / "bin",
        'printf "P1-looking but failed review\\n"\n'
        'printf "provider failure\\n" >&2\n'
        'exit 7\n',
    )

    result = _run_opencode(tmp_path / "bin")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "provider failure" in result.stderr
    assert "opencode exit rc=7" in result.stderr
    assert "本轮缺 opencode" in result.stderr


def test_empty_opencode_output_degrades_visibly(tmp_path):
    _stub_opencode(
        tmp_path / "bin",
        'printf "provider returned no final answer\\n" >&2\n'
        'exit 0\n',
    )

    result = _run_opencode(tmp_path / "bin")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "provider returned no final answer" in result.stderr
    assert "empty output" in result.stderr
    assert "本轮缺 opencode" in result.stderr


def test_missing_opencode_command_degrades_through_nonzero_path(tmp_path):
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()

    result = _run_opencode(
        empty_bin,
        PATH=f"{empty_bin}{os.pathsep}/usr/bin{os.pathsep}/bin",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "command not found" in result.stderr
    assert "opencode exit rc=127" in result.stderr
    assert "本轮缺 opencode" in result.stderr
