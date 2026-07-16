"""Behavioral tests for isolated reviewer clone preparation."""

import os
import shutil
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare-review-clone.sh"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _source_repo(path: Path) -> tuple[str, str]:
    path.mkdir()
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    _git(path, "config", "user.name", "CMR Test")
    _git(path, "config", "user.email", "cmr-test@example.invalid")
    (path / "reviewed.txt").write_text("base\n")
    _git(path, "add", "reviewed.txt")
    _git(path, "commit", "-m", "base")
    base = _git(path, "rev-parse", "HEAD").stdout.strip()
    (path / "reviewed.txt").write_text("base\nhead\n")
    _git(path, "add", "reviewed.txt")
    _git(path, "commit", "-m", "head")
    head = _git(path, "rev-parse", "HEAD").stdout.strip()
    return base, head


def _git_override_env(stub_dir: Path, body: str) -> dict[str, str]:
    stub_dir.mkdir()
    git_stub = stub_dir / "git"
    git_stub.write_text("#!/bin/sh\n" + body + '\nexec "$REAL_GIT" "$@"\n')
    git_stub.chmod(
        git_stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    )
    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env["REAL_GIT"] = shutil.which("git") or "git"
    return env


def test_prepared_review_clone_does_not_expose_source_path(tmp_path):
    source = tmp_path / "SOURCE_REPO_PATH_MUST_NOT_REACH_REVIEWER"
    leg = tmp_path / "review-leg"
    base, head = _source_repo(source)

    result = subprocess.run(
        ["bash", str(SCRIPT), str(source), str(leg), head, base],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout.strip() == str(leg.resolve())
    assert _git(leg, "rev-parse", "HEAD").stdout.strip() == head
    assert _git(leg, "remote").stdout == ""
    assert _git(leg, "status", "--porcelain=v1", "--untracked-files=all").stdout == ""

    source_bytes = str(source.resolve()).encode()
    assert source_bytes not in (leg / ".git" / "config").read_bytes()
    logs = leg / ".git" / "logs"
    for log in logs.rglob("*") if logs.exists() else ():
        if log.is_file():
            assert source_bytes not in log.read_bytes(), f"source leaked through {log}"
    assert str(source.resolve()) not in _git(leg, "reflog", "show", "--all").stdout


def test_preflight_rejects_source_path_left_in_raw_reflog(tmp_path):
    source = tmp_path / "SOURCE_REPO_PATH_MUST_NOT_REACH_REVIEWER"
    leg = tmp_path / "review-leg"
    base, head = _source_repo(source)

    env = _git_override_env(
        tmp_path / "bin",
        'if [ "$1" = "-C" ] && [ "$3" = "reflog" ] && '
        '[ "$4" = "expire" ]; then\n'
        "  exit 0\n"
        "fi",
    )

    result = subprocess.run(
        ["bash", str(SCRIPT), str(source), str(leg), head, base],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )

    source_bytes = str(source.resolve()).encode()
    leaked_logs = [
        path
        for path in (leg / ".git" / "logs").rglob("*")
        if path.is_file() and source_bytes in path.read_bytes()
    ]
    assert leaked_logs, "fixture must preserve the clone provenance leak"
    assert result.returncode != 0, (
        "preflight accepted a clone whose raw reflog exposed REPO_ROOT\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert "reflog" in result.stderr.lower()


def test_preflight_rejects_source_path_left_in_local_config(tmp_path):
    source = tmp_path / "SOURCE_REPO_PATH_MUST_NOT_REACH_REVIEWER"
    leg = tmp_path / "review-leg"
    base, head = _source_repo(source)
    env = _git_override_env(
        tmp_path / "bin",
        'if [ "$1" = "-C" ] && [ "$3" = "remote" ] && '
        '[ "$4" = "remove" ] && [ "$5" = "origin" ]; then\n'
        '  "$REAL_GIT" "$@" || exit $?\n'
        '  "$REAL_GIT" -C "$2" config cmr.injectedSource "$CMR_SOURCE_PATH"\n'
        "  exit $?\n"
        "fi",
    )
    env["CMR_SOURCE_PATH"] = str(source.resolve())

    result = subprocess.run(
        ["bash", str(SCRIPT), str(source), str(leg), head, base],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )

    assert str(source.resolve()) in _git(leg, "config", "--local", "--list").stdout
    assert result.returncode != 0, (
        "preflight accepted a clone whose local config exposed REPO_ROOT\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert "config" in result.stderr.lower()
