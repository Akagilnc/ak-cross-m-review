"""Regression tests for backends/codex-review.sh.

Two pinned behaviors around the degrade gate:

1. A codex that exits NON-ZERO is a real outage (auth/quota/crash) and
   must degrade (exit 1 + synthetic empty findings), even if it printed a
   salvageable-looking body. Otherwise a failed codex silently counts as
   a valid zero-finding reviewer.

2. A codex that exits ZERO with a PROSE review (no JSON, no sentinel)
   must be PASSED THROUGH verbatim (exit 0), NOT degraded. Codex's
   strongest review is prose; the old sentinel-JSON gate dropped it as if
   codex were down — the divergence from the wiki (§「.result 是 review
   文本」: reviewers return prose, the orchestrator reads it) that lost the
   strongest reviewer to a format technicality across many rounds."""

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "codex-review.sh"


def test_degrades_when_codex_exits_nonzero_with_salvageable_body(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    codex = stub_dir / "codex"
    # Prints a JSON-ish error body but the process exits 1 — a real
    # outage (auth/quota/crash). Must degrade, never count as a review.
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


def test_prose_review_passes_through_not_degraded(tmp_path):
    # THE fix: codex's natural, strongest output is a PROSE review (no
    # JSON, no sentinel). It exits 0. The script must pass that prose
    # through verbatim and exit 0 — NOT degrade it to "本轮缺 codex" as if
    # codex were down. (The old extract_json sentinel gate did exactly
    # that, dropping the strongest reviewer over format.)
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    codex = stub_dir / "codex"
    prose = (
        "I reviewed the diff. One real issue:\\n"
        "P1: route.ts:96 route() treats a non-reviewer output as 0 findings, "
        "letting a malformed step bypass the P0/P1 gate.\\n"
        "Otherwise converged."
    )
    # %b (not %s) so the prose's \n become real newlines — a faithful
    # multi-line review stub (gemini online R, medium).
    codex.write_text(f"#!/bin/sh\nprintf '%b\\n' \"{prose}\"\nexit 0\n")
    codex.chmod(codex.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env["CMR_CODEX_TIMEOUT"] = "15"

    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 0, (
        f"prose review must pass through (exit 0), not degrade; got "
        f"{r.returncode}\nstdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert "route() treats a non-reviewer output" in r.stdout, (
        f"codex's prose review was not passed through. stdout={r.stdout!r}"
    )
    assert "本轮缺 codex" not in r.stderr, (
        f"a real prose review was wrongly flagged as a missing vendor. "
        f"stderr={r.stderr!r}"
    )


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
