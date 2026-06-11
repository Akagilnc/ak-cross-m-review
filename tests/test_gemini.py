"""Regression tests for backends/gemini.sh (the Gemini reviewer leg).

The script now calls `agy` (Antigravity CLI) — the in-kind
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

import json
import os
import shutil
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


def test_does_not_false_degrade_when_model_output_contains_auth_string(tmp_path):
    # If agy exits 0, even if the model output contains "Authentication required"
    # (because the reviewed diff touches auth logic), it should NOT be treated
    # as an auth race. It should parse and pass successfully.
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'echo "===CMR-FINDINGS-BEGIN==="\n'
        'echo \'{"reviewer":"gemini","mode":"code","findings":[]}\'\n'
        'echo "===CMR-FINDINGS-END==="\n'
        'echo "The reviewed diff added: echo Authentication required"\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+ echo \"Authentication required\"\n--- END DIFF ---\n",
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 0, (
        f"expected exit 0, got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    # extract_json pretty-prints (json.dump indent=2), so assert on the
    # parsed value, not a compact substring (the degrade path emits
    # compact JSON; the success path does not).
    assert json.loads(r.stdout)["findings"] == []
    assert "auth race" not in r.stderr


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


def test_injects_read_only_instruction_into_agy_prompt(tmp_path):
    # First-run finding: agy (agentic CLI) edited tracked files + ran
    # pytest during a review because nothing told it to stay read-only;
    # `--sandbox` alone does not block workspace writes. gemini.sh must
    # prepend an explicit "REVIEW ONLY / do not modify" instruction to
    # the prompt it sends agy. We can't force the real agy to obey, but
    # we CAN pin that the backend actually gives the instruction: the
    # stub echoes back, inside sentinels, whether the marker reached it.
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'prompt="$(cat)"\n'
        'echo "===CMR-FINDINGS-BEGIN==="\n'
        'if echo "$prompt" | grep -qi "REVIEW ONLY"; then\n'
        '  echo \'{"reviewer":"gemini","mode":"code","findings":['
        '{"id":"RO_MARKER_PRESENT"}]}\'\n'
        'else\n'
        '  echo \'{"reviewer":"gemini","mode":"code","findings":['
        '{"id":"RO_MARKER_ABSENT"}]}\'\n'
        'fi\n'
        'echo "===CMR-FINDINGS-END==="\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 0, (
        f"expected exit 0, got {r.returncode}\n"
        f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    )
    assert "RO_MARKER_PRESENT" in r.stdout, (
        "gemini.sh did not prepend the read-only instruction to the agy "
        f"prompt. stdout={r.stdout!r}"
    )
    assert "RO_MARKER_ABSENT" not in r.stdout


def test_invocation_passes_sandbox_flag_and_empty_print_value(tmp_path):
    # Regression for the agy 1.0.7 flag-parse change. `--print`/`-p`
    # became a string flag that takes its value from the NEXT token, so
    # the old `agy -p --sandbox` made `-p` swallow `--sandbox` as the
    # prompt value — `--sandbox` never engaged. Pin the corrected form:
    # `--sandbox` is a standalone flag and `--print`'s value is the
    # empty string (the diff rides in on stdin, no ARG_MAX limit).
    dump = tmp_path / "argv.txt"
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        ': > "$AGY_ARGV_DUMP"\n'
        'for a in "$@"; do printf \'%s\\0\' "$a" >> "$AGY_ARGV_DUMP"; done\n'
        'echo "===CMR-FINDINGS-BEGIN==="\n'
        'echo \'{"reviewer":"gemini","mode":"code","findings":[]}\'\n'
        'echo "===CMR-FINDINGS-END==="\n'
        'exit 0\n'
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_ARGV_DUMP"] = str(dump)
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 0, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    argv = dump.read_bytes().split(b"\0")
    if argv and argv[-1] == b"":
        argv = argv[:-1]  # drop the trailing-delimiter artifact only
    argv = [a.decode() for a in argv]
    assert "--sandbox" in argv, f"--sandbox missing from agy argv: {argv}"
    assert "--print" in argv, f"--print missing (regressed to -p?): {argv}"
    # cross-model review R1 (codex#1 R2): the weak form of this test
    # (--sandbox present + --print present + token-after-first-print
    # empty) is satisfied even by a regressed `['-p','--sandbox',
    # '--print','']` where -p still swallows --sandbox. Assert the real
    # invariant: the short `-p` is never used, and NO `--print`/`-p`
    # occurrence has `--sandbox` as its value token.
    assert "-p" not in argv, (
        f"short `-p` must not be used (agy 1.0.7 makes it swallow the "
        f"next token as the prompt value): {argv}"
    )
    for i, tok in enumerate(argv):
        if tok in ("--print", "-p"):
            assert i + 1 < len(argv) and argv[i + 1] != "--sandbox", (
                f"`{tok}` swallows --sandbox as its value — the 1.0.7 "
                f"flag-eat bug has regressed. argv={argv}"
            )
    pi = argv.index("--print")
    assert pi + 1 < len(argv), f"--print has no following token: {argv}"
    assert argv[pi + 1] == "", (
        "--print value must be the empty string (diff rides on stdin); "
        f"got {argv[pi + 1]!r}. argv={argv}"
    )


def test_surfaces_quota_reason_when_agy_swallows_429_to_logfile(tmp_path):
    # Real-world failure (8 empty rounds): agy hits RESOURCE_EXHAUSTED
    # (429) but routes it to its --log-file and exits 0 with EMPTY
    # stdout — so the round looked like a silent empty degrade with no
    # reason. gemini.sh now passes --log-file and greps it on degrade,
    # so the flag names the quota cause instead of just "empty output".
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in\n'
        '    --log-file) logf="$2"; shift 2 ;;\n'
        '    *) shift ;;\n'
        '  esac\n'
        'done\n'
        '[ -n "$logf" ] && printf \'%s\\n\' '
        '"E0611 agent executor error: RESOURCE_EXHAUSTED (code 429): '
        'Individual quota reached. Resets in 64h24m36s." > "$logf"\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert '"findings":[]' in r.stdout
    assert "本轮缺 gemini" in r.stderr
    assert "quota" in r.stderr
    assert "429" in r.stderr
    assert "Resets in 64h" in r.stderr


def test_no_false_quota_reason_when_model_output_mentions_quota(tmp_path):
    # Cross-model review R1 (Claude C1 + codex#2 R1, live-reproduced):
    # the degrade-reason scan must read agy's --log-file, NOT $RAW. On
    # the extract-fail path $RAW is the full model output, which routinely
    # quotes the reviewed diff — so a diff that mentions quota/429 code
    # (e.g. `check_user_quota()`) must NOT make the flag falsely claim
    # "quota/429 — agy individual quota exhausted". agy exits 0 with
    # sentinel-less output and an EMPTY log → extract-fail degrade with
    # NO quota attribution. (Mirrors the auth-string false-degrade guard.)
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'echo "Reviewed diff adds: def check_user_quota(): return 429"\n'
        'echo "no sentinel block here"\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+ def check_user_quota(): return 429\n--- END DIFF ---\n",
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "本轮缺 gemini" in r.stderr  # it DOES degrade (no sentinel)
    assert "quota" not in r.stderr, (
        "false quota attribution: the reason scan matched 'quota' in the "
        f"model output ($RAW) instead of agy's log. stderr={r.stderr!r}"
    )
    assert "429" not in r.stderr


def test_quota_log_without_resets_line_still_degrades_cleanly(tmp_path):
    # Cross-model review R2 (codex#2 raised an abort concern; refuted
    # empirically + by the Claude leg, locked here): when agy's log has a
    # 429/quota signature but NO "Resets in …" line, the optional
    # `resets="$(grep … | head -1)"` grep finds nothing. Under
    # `set -euo pipefail` this must NOT abort the script before it emits
    # the degrade JSON — it must degrade cleanly and still name quota
    # (just without the reset-time suffix).
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in --log-file) logf="$2"; shift 2 ;; *) shift ;; esac\n'
        'done\n'
        '[ -n "$logf" ] && printf \'%s\\n\' '
        '"E agent executor error: RESOURCE_EXHAUSTED (code 429): '
        'Individual quota reached." > "$logf"\n'  # note: no "Resets in" line
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    # the synthetic degrade JSON MUST be present (proves no mid-function
    # abort before the emit)
    assert json.loads(r.stdout)["findings"] == []
    assert "本轮缺 gemini" in r.stderr
    assert "quota" in r.stderr
    assert "Resets in" not in r.stderr  # no reset hint available


def test_nonempty_nonfatal_log_degrades_without_reason_suffix(tmp_path):
    # R2 companion: a non-empty agy log with neither a quota signature
    # NOR an "agent executor error:" line exercises the trailing
    # `execerr="$(grep … | head -1)"` no-match path. It too must not
    # abort under `set -euo pipefail`; degrade cleanly with no reason
    # suffix appended.
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in --log-file) logf="$2"; shift 2 ;; *) shift ;; esac\n'
        'done\n'
        '[ -n "$logf" ] && printf \'%s\\n\' '
        '"I0611 benign agy log line, nothing fatal here" > "$logf"\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert json.loads(r.stdout)["findings"] == []
    assert "本轮缺 gemini" in r.stderr
    assert "quota" not in r.stderr  # no false attribution from a benign log


def test_execerr_reason_is_not_truncated_at_colon(tmp_path):
    # Online R1 (sourcery): the executor-error grep used `[^:]*` and
    # truncated multi-colon messages at the first colon. It now matches
    # to end of line, so the full executor error reaches the flag.
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in --log-file) logf="$2"; shift 2 ;; *) shift ;; esac\n'
        'done\n'
        '[ -n "$logf" ] && printf \'%s\\n\' '
        '"E agent executor error: call failed: backend timeout" > "$logf"\n'
        'exit 0\n'
    ))
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True,
        env=_env_with_stub(tmp_path / "bin"),
        timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "agent executor error: call failed: backend timeout" in r.stderr, (
        "executor error was truncated at the first colon — should match to "
        f"end of line. stderr={r.stderr!r}"
    )


def test_log_truncated_per_attempt_no_stale_reason_leak(tmp_path):
    # Online R1 (sourcery): AGY_LOG is reused across retry attempts; the
    # script truncates it before each attempt so the degrade reason
    # reflects ONLY the final attempt. Here attempt 1 writes a 429 to the
    # log AND emits the auth-race signature (→ retry); attempt 2 is a
    # clean empty success. Without per-attempt truncation, attempt 1's
    # 429 would leak into attempt 2's empty-output degrade reason.
    counter = tmp_path / "attempt_n"
    _stub_agy(tmp_path / "bin", (
        '#!/bin/sh\n'
        'logf=""\n'
        'while [ $# -gt 0 ]; do\n'
        '  case "$1" in --log-file) logf="$2"; shift 2 ;; *) shift ;; esac\n'
        'done\n'
        'n=$(cat "$AGY_ATTEMPT_COUNTER" 2>/dev/null || echo 0); n=$((n + 1))\n'
        'echo "$n" > "$AGY_ATTEMPT_COUNTER"\n'
        'if [ "$n" = 1 ]; then\n'
        '  [ -n "$logf" ] && printf \'%s\\n\' '
        '"E RESOURCE_EXHAUSTED (code 429): Individual quota reached." > "$logf"\n'
        '  echo "Authentication required"\n'  # auth-race signature → retry
        '  exit 1\n'
        'fi\n'
        'exit 0\n'  # attempt 2: clean empty success, writes nothing to log
    ))
    env = _env_with_stub(tmp_path / "bin")
    env["AGY_ATTEMPT_COUNTER"] = str(counter)
    r = subprocess.run(
        ["bash", str(SCRIPT), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 1, f"stdout={r.stdout!r}\nstderr={r.stderr!r}"
    assert "agy auth-race on attempt 1" in r.stderr  # it did retry
    assert "本轮缺 gemini" in r.stderr
    assert "quota" not in r.stderr, (
        "attempt 1's 429 leaked into attempt 2's degrade reason — the "
        f"per-attempt log truncation is not working. stderr={r.stderr!r}"
    )


def _run_copied_gemini(script_root: Path, tmp_path):
    """Copy gemini.sh under script_root/backends and run it with agy
    MISSING (so it degrades right after the path check). Returns the
    CompletedProcess. PROTO_ROOT resolves to script_root, letting a test
    place it under a hidden vs visible parent to exercise both branches
    of the hidden-path warning."""
    backends = script_root / "backends"
    backends.mkdir(parents=True)
    shutil.copy2(SCRIPT, backends / "gemini.sh")
    bindir = tmp_path / "emptybin"
    bindir.mkdir()
    env = dict(os.environ)
    env["PATH"] = f"{bindir}{os.pathsep}/usr/bin{os.pathsep}/bin"
    env["GEMINI_RETRY_WARM_SLEEP"] = "0"
    return subprocess.run(
        ["bash", str(backends / "gemini.sh"), "code"],
        input="review prompt\n--- BEGIN DIFF ---\n+x\n--- END DIFF ---\n",
        capture_output=True, text=True, env=env, timeout=30,
    )


def test_warns_when_workspace_root_under_hidden_dir(tmp_path):
    # cmr run from e.g. a `.claude/worktrees/...` path: agy refuses to
    # add a hidden-component path as a workspace folder, so the reviewer
    # loses repo context. The backend must warn (not silently degrade).
    r = _run_copied_gemini(tmp_path / ".hidden" / "repo", tmp_path)
    assert r.returncode == 1
    assert "agy not installed" in r.stderr  # degraded AFTER the warning
    assert "hidden" in r.stderr
    assert "without repo context" in r.stderr.lower()


def test_no_hidden_warning_when_workspace_root_visible(tmp_path):
    # The other branch: a normal (non-hidden) workspace root must NOT
    # emit the hidden-path warning. Cross-model review R1 (Claude C3):
    # guard the env edge where the base temp dir is itself under a hidden
    # component (e.g. TMPDIR=~/.cache/...), which would make even a
    # "visible" subpath match the */.* glob and false-red this branch.
    if "/." in str(tmp_path):
        import pytest
        pytest.skip(f"base temp dir is itself under a hidden component: {tmp_path}")
    r = _run_copied_gemini(tmp_path / "visible" / "repo", tmp_path)
    assert r.returncode == 1
    assert "agy not installed" in r.stderr
    assert "hidden" not in r.stderr
