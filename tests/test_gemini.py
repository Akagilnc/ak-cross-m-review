"""Regression for the gemini.sh degrade gap (dogfood round-2 HIGH).

A gemini that exits non-zero but prints a JSON-ish error body — which
extract_json's legacy salvage would patch into findings:[] with exit 0 —
must STILL degrade (exit 1 + synthetic empty findings + visible flag).
Round-1's gemini.sh fix ported only the EX_RC half of codex-review.sh's
gate, so a rate-limited gemini slipped through as a silent zero-finding
approve. This pins the restored G_RC half."""

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "backends" / "gemini.sh"


def test_degrades_when_gemini_exits_nonzero_with_salvageable_body(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    g = stub_dir / "gemini"
    # No sentinels; a JSON-ish error body (extract_json pass-5 would
    # patch it to findings:[] exit 0). Process exits 1 — the 429 shape.
    g.write_text(
        '#!/bin/sh\necho \'{"error":"RESOURCE_EXHAUSTED 429"}\'\nexit 1\n'
    )
    g.chmod(g.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
    env["GEMINI_RETRY_SLEEP"] = "0"  # don't wait the 30s retry backoff

    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True, env=env, timeout=60,
    )

    assert r.returncode == 1, (
        f"expected degrade exit 1, got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert '"reviewer":"gemini"' in r.stdout
    assert '"findings":[]' in r.stdout
    assert "本轮缺 gemini" in r.stderr
