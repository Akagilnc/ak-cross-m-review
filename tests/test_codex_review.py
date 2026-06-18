"""Regression test for the codex-review.sh degrade gap (Codex [P2]).

A codex that exits non-zero but prints a JSON error body — which
extract_json.py salvages into findings:[] and exits 0 — must STILL be
treated as a degraded vendor (exit 1 + synthetic empty findings).
Otherwise an auth/quota-failed codex silently counts as a valid
zero-finding reviewer."""

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "codex-review.sh"


def test_degrades_when_codex_exits_nonzero_with_salvageable_body(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    codex = stub_dir / "codex"
    # Prints a JSON object with no `findings` (extract_json pass-5
    # salvages it → findings:[] → exit 0) but the process exits 1.
    codex.write_text('#!/bin/sh\necho \'{"error":"quota exceeded"}\'\nexit 1\n')
    codex.chmod(codex.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env["CMR_CODEX_TIMEOUT"] = "15"

    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True, env=env, timeout=60,
    )

    assert r.returncode == 1, (
        f"expected degrade exit 1, got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    # Synthetic degrade payload (compact, no spaces — see the printf).
    assert '"reviewer":"codex"' in r.stdout
    assert '"findings":[]' in r.stdout


def _selftest(effort=None):
    """Run `codex-review.sh --selftest`, optionally pinning CMR_CODEX_EFFORT."""
    env = dict(os.environ)
    if effort is not None:
        env["CMR_CODEX_EFFORT"] = effort
    else:
        env.pop("CMR_CODEX_EFFORT", None)
    return subprocess.run(
        ["bash", str(SCRIPT), "--selftest"],
        capture_output=True, text=True, env=env, timeout=30,
    )


def test_selftest_passes_with_default_xhigh_effort():
    # Default (no env) → ship-pre xhigh; selftest green + names the pin.
    r = _selftest()
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "model_reasoning_effort=xhigh" in r.stdout


def test_selftest_passes_with_per_slice_high_effort():
    # CMR_CODEX_EFFORT=high (per-slice) → selftest still green, matching
    # the LIVE effort (not hardcoded xhigh).
    r = _selftest("high")
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "model_reasoning_effort=high" in r.stdout
    assert "model_reasoning_effort=xhigh" not in r.stdout


def test_invalid_effort_is_rejected():
    # Only high|xhigh are valid reasoning tiers for review; anything else
    # (e.g. a typo, or `medium` which would make per-slice a rubber stamp)
    # must hard-fail, not silently run at the wrong depth.
    r = _selftest("medium")
    assert r.returncode == 64, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "CMR_CODEX_EFFORT must be high|xhigh" in r.stderr
