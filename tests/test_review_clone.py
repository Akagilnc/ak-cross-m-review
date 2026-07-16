"""Behavioral tests for isolated reviewer clone preparation."""

import os
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


def _prepare(
    source: Path,
    leg: Path,
    head: str,
    base: str,
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), str(source), str(leg), head, base],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def test_prepares_clean_detached_remote_free_clone(tmp_path):
    source = tmp_path / "source"
    leg = tmp_path / "review-leg"
    base, head = _source_repo(source)

    result = _prepare(source, leg, head, base)

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout.strip() == str(leg.resolve())
    assert _git(leg, "rev-parse", "HEAD").stdout.strip() == head
    assert _git(leg, "remote").stdout == ""
    assert _git(leg, "status", "--porcelain=v1", "--untracked-files=all").stdout == ""


def test_rejects_canonical_leg_root_inside_source_before_clone(tmp_path):
    source = tmp_path / "source"
    base, head = _source_repo(source)
    source_alias = tmp_path / "source-alias"
    source_alias.symlink_to(source, target_is_directory=True)
    leg = source_alias / "review-leg"

    result = _prepare(source, leg, head, base)

    assert result.returncode != 0
    assert "outside source repository" in result.stderr
    assert not leg.exists(), "rejection must happen before git clone"


def test_removes_origin_when_default_remote_name_is_overridden(tmp_path):
    source = tmp_path / "source"
    leg = tmp_path / "review-leg"
    base, head = _source_repo(source)
    env = dict(os.environ)
    env.update(
        {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "clone.defaultRemoteName",
            "GIT_CONFIG_VALUE_0": "upstream",
        }
    )

    result = _prepare(source, leg, head, base, env=env)

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert _git(leg, "remote").stdout == ""
