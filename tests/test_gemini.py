"""Minimal contract tests for agy's primary call and quota-only fallback."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "gemini.sh"
PACKET = "Review fixed range 111...222; authority: AGENTS.md.\n"


def _stub_agy(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    exe = path / "agy"
    exe.write_text(
        "#!/bin/sh\n"
        ': > "${ARGV_DUMP:-/dev/null}"\n'
        'for arg in "$@"; do printf "%s\\0" "$arg" >> "${ARGV_DUMP:-/dev/null}"; done\n'
        'model=""; log=""\n'
        'while [ $# -gt 0 ]; do case "$1" in\n'
        '  --model) model="$2"; shift 2;; --log-file) log="$2"; shift 2;; *) shift;;\n'
        'esac; done\n'
        'cat > "${PROMPT_DUMP:-/dev/null}"\n'
        'pwd > "${CWD_DUMP:-/dev/null}"\n'
        'echo "$model" >> "${MODEL_DUMP:-/dev/null}"\n'
        'case "${SCENARIO:-success}" in\n'
        '  success) echo "review from $model";;\n'
        '  nonzero) echo "provider failure"; exit 7;;\n'
        '  empty) exit 0;;\n'
        '  auth) echo "Authentication required"; exit 1;;\n'
        '  nonquota) echo "E agent executor error: RESOURCE_EXHAUSTED: worker pool" > "$log"; exit 1;;\n'
        '  unknown_log) echo "E UNKNOWN_NATIVE_FATAL: provider imploded" > "$log"; exit 1;;\n'
        '  quota_then_success)\n'
        '    case "$model" in *Gemini*) echo "E RESOURCE_EXHAUSTED (code 429): Individual quota reached." > "$log";; *) echo "review from $model";; esac;;\n'
        '  quota_then_auth)\n'
        '    case "$model" in *Gemini*) echo "E RESOURCE_EXHAUSTED (code 429): Individual quota reached." > "$log";; *) echo "Authentication required for fallback"; exit 7;; esac;;\n'
        '  quota_all) echo "E RESOURCE_EXHAUSTED (code 429): Individual quota reached." > "$log";;\n'
        'esac\n'
    )
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run(stub: Path, cwd: Path | None = None, **extra: str):
    env = dict(os.environ)
    env["PATH"] = f"{stub}{os.pathsep}{env['PATH']}"
    for key in ("AGY_MODEL", "AGY_FALLBACK_MODEL", "AGY_PRINT_TIMEOUT"):
        env.pop(key, None)
    env.update(extra)
    return subprocess.run(
        ["bash", str(SCRIPT), "code"], input=PACKET, cwd=cwd,
        capture_output=True, text=True, env=env, timeout=30,
    )


def _argv(path: Path) -> list[str]:
    parts = path.read_bytes().split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    return [part.decode() for part in parts]


@pytest.mark.parametrize(
    ("model", "timeout"),
    [("Gemini 3.5 Flash (High)", "15m"), ("Gemini custom", "42m")],
)
def test_official_argv_prompt_cwd_and_success(tmp_path, model, timeout):
    _stub_agy(tmp_path / "bin")
    clone = tmp_path / "clone"
    subprocess.run(["git", "init", "-q", str(clone)], check=True)
    argv_dump, prompt_dump, cwd_dump = (
        tmp_path / "argv", tmp_path / "prompt", tmp_path / "cwd"
    )
    extra = {
        "ARGV_DUMP": str(argv_dump), "PROMPT_DUMP": str(prompt_dump),
        "CWD_DUMP": str(cwd_dump), "MODEL_DUMP": str(tmp_path / "models"),
    }
    if model != "Gemini 3.5 Flash (High)":
        extra.update(AGY_MODEL=model, AGY_PRINT_TIMEOUT=timeout)
    result = _run(tmp_path / "bin", cwd=clone, **extra)
    argv = _argv(argv_dump)
    log_path = argv[argv.index("--log-file") + 1]
    argv[argv.index("--log-file") + 1] = "<log-file>"
    assert Path(log_path).is_absolute()
    assert argv == [
        "--model", model, "--print", "", "--print-timeout", timeout,
        "--log-file", "<log-file>",
    ]
    assert "--sandbox" not in argv
    assert prompt_dump.read_text() == PACKET
    assert Path(cwd_dump.read_text().strip()) == clone
    assert result.returncode == 0 and result.stdout == f"review from {model}\n"


@pytest.mark.parametrize(
    ("scenario", "reason"),
    [("nonzero", "agy exit rc=7"), ("empty", "empty output")],
)
def test_nonzero_or_empty_output_degrades(tmp_path, scenario, reason):
    _stub_agy(tmp_path / "bin")
    result = _run(
        tmp_path / "bin", SCENARIO=scenario,
        MODEL_DUMP=str(tmp_path / "models"),
    )
    assert result.returncode == 1 and result.stdout == ""
    assert reason in result.stderr and "本轮缺 gemini" in result.stderr


@pytest.mark.parametrize("scenario", ["auth", "nonquota"])
def test_auth_and_nonquota_failures_never_use_second_pool(tmp_path, scenario):
    _stub_agy(tmp_path / "bin")
    models = tmp_path / "models"
    result = _run(
        tmp_path / "bin", SCENARIO=scenario, MODEL_DUMP=str(models),
        AGY_MODEL="primary", AGY_FALLBACK_MODEL="fallback",
    )
    assert models.read_text().splitlines() == ["primary"]
    assert result.returncode == 1 and result.stdout == ""
    assert "本轮缺 gemini" in result.stderr


def test_unknown_log_only_fatal_is_preserved_before_degrade(tmp_path):
    _stub_agy(tmp_path / "bin")
    result = _run(
        tmp_path / "bin", SCENARIO="unknown_log",
        MODEL_DUMP=str(tmp_path / "models"),
    )
    assert result.returncode == 1 and result.stdout == ""
    assert result.stderr.index(
        "E UNKNOWN_NATIVE_FATAL: provider imploded"
    ) < result.stderr.index("gemini: degrade")


def test_confirmed_primary_quota_uses_second_pool_once_and_labels_family(tmp_path):
    _stub_agy(tmp_path / "bin")
    models = tmp_path / "models"
    result = _run(
        tmp_path / "bin", SCENARIO="quota_then_success",
        MODEL_DUMP=str(models),
    )
    assert models.read_text().splitlines() == [
        "Gemini 3.5 Flash (High)", "Claude Sonnet 4.6 (Thinking)",
    ]
    assert result.returncode == 0
    assert result.stdout == "review from Claude Sonnet 4.6 (Thinking)\n"
    assert "NO Google family this round" in result.stderr
    assert "RESOURCE_EXHAUSTED" not in result.stderr


def test_both_quota_pools_exhaust_after_exactly_two_calls(tmp_path):
    _stub_agy(tmp_path / "bin")
    models = tmp_path / "models"
    result = _run(
        tmp_path / "bin", SCENARIO="quota_all", MODEL_DUMP=str(models),
    )
    assert models.read_text().splitlines() == [
        "Gemini 3.5 Flash (High)", "Claude Sonnet 4.6 (Thinking)",
    ]
    assert result.returncode == 1 and result.stdout == ""
    assert "E RESOURCE_EXHAUSTED (code 429): Individual quota reached." in result.stderr
    assert "quota/429" not in result.stderr and "本轮缺 gemini" in result.stderr


def test_failed_fallback_preserves_primary_quota_and_fallback_error(tmp_path):
    _stub_agy(tmp_path / "bin")
    models = tmp_path / "models"
    result = _run(
        tmp_path / "bin", SCENARIO="quota_then_auth", MODEL_DUMP=str(models),
    )
    assert models.read_text().splitlines() == [
        "Gemini 3.5 Flash (High)", "Claude Sonnet 4.6 (Thinking)",
    ]
    assert result.returncode == 1 and result.stdout == ""
    assert result.stderr.index(
        "E RESOURCE_EXHAUSTED (code 429): Individual quota reached."
    ) < result.stderr.index("Authentication required for fallback")
    assert result.stderr.index(
        "Authentication required for fallback"
    ) < result.stderr.index("gemini: degrade")


def test_successful_non_google_override_reports_actual_family(tmp_path):
    _stub_agy(tmp_path / "bin")
    result = _run(
        tmp_path / "bin", AGY_MODEL="GPT-OSS 120B",
        MODEL_DUMP=str(tmp_path / "models"),
    )
    assert result.returncode == 0
    assert "GPT-OSS 120B" in result.stderr
    assert "NO Google family this round" in result.stderr


def test_non_git_cwd_stops_before_agy_and_preserves_git_error(tmp_path):
    _stub_agy(tmp_path / "bin")
    models = tmp_path / "models"
    result = _run(
        tmp_path / "bin", cwd=tmp_path, MODEL_DUMP=str(models),
    )
    assert result.returncode != 0 and result.stdout == "" and not models.exists()
    assert "fatal: not a git repository" in result.stderr
