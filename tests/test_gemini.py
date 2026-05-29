"""Regression tests for backends/gemini.sh (the Gemini reviewer leg).

The script now calls `agy` (Antigravity CLI 1.0.0) — the in-kind
replacement after the original `gemini` CLI's 2026-06-18 EOL — with
the wiki's keychain-warm + retry × 4 recipe.

Two pinned behaviors:

1. agy exits non-zero with a JSON-ish error body that extract_json's
   legacy salvage would patch into findings:[] exit 0 → the script
   must STILL degrade (the G_RC half of the codex-review.sh-style
   gate). Round-1 of the original gemini.sh fix lacked this half and
   a rate-limited gemini slipped through as a silent zero-finding
   approve.

2. agy keeps hitting the keychain auth-race signature → the script
   retries up to 4 attempts (initial 1 + 3 retries), then degrades
   with the auth-race-specific flag. Never silent."""

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "gemini.sh"


def _stub_agy(stub_dir: Path, body: str) -> None:
    """Drop an executable `agy` stub on PATH that runs `body`."""
    stub_dir.mkdir(parents=True, exist_ok=True)
    g = stub_dir / "agy"
    g.write_text(body)
    g.chmod(g.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _env_with_stub(stub_dir: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    # Tests should never wait between retries.
    env["GEMINI_RETRY_WARM_SLEEP"] = "0"
    return env


def test_degrades_when_agy_exits_nonzero_with_salvageable_body(tmp_path):
    # No auth-race signature (so the retry loop breaks on attempt 1).
    # A JSON-ish body extract_json pass-5 would patch into findings:[]
    # exit 0 — without the G_RC gate this would slip through as a
    # silent zero-finding approve.
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'echo \'{"error":"RESOURCE_EXHAUSTED 429"}\'\n'
        'exit 1\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1, (
        f"expected degrade exit 1, got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert '"reviewer":"gemini"' in r.stdout
    assert '"findings":[]' in r.stdout
    assert "本轮缺 gemini" in r.stderr


def test_retries_on_auth_race_then_degrades_after_4_attempts(tmp_path):
    # Every attempt prints the auth-race signature → script retries the
    # max 3 times (after the initial attempt), warns each retry, then
    # degrades with the auth-race-specific flag. Visible, never silent.
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'echo "Authentication required"\n'
        'exit 1\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1
    assert '"reviewer":"gemini"' in r.stdout
    assert '"findings":[]' in r.stdout
    assert "auth race after retry×3" in r.stderr
    # 3 retry-warn lines (after attempts 1, 2, 3) before the final
    # degrade on attempt 4 — confirms the loop actually iterated, did
    # not short-circuit.
    assert r.stderr.count("agy auth-race on attempt") == 3


def test_degrades_with_clear_flag_when_agy_not_installed(tmp_path):
    # Empty stub dir → no `agy` on PATH → degrade up-front with the
    # post-EOL explanation, never silent / never crash.
    (tmp_path / "bin").mkdir()
    env = dict(os.environ)
    # Override PATH to ONLY contain the (empty) stub dir + system minimal
    # bin paths so `agy` is missing but `security`/coreutils still work.
    env["PATH"] = f"{tmp_path / 'bin'}{os.pathsep}/usr/bin{os.pathsep}/bin"
    env["GEMINI_RETRY_WARM_SLEEP"] = "0"

    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True, env=env, timeout=30,
    )
    assert r.returncode == 1
    assert '"reviewer":"gemini"' in r.stdout
    assert '"findings":[]' in r.stdout
    assert "agy not installed" in r.stderr
    assert "本轮缺 gemini" in r.stderr
