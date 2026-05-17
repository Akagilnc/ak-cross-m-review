"""CLI-layer coverage for lib/drift.py main(): arg parsing, the
--active-vendors integer guard, the usage path, and the input_error
exit-code-3 contract. Real subprocess invocations, real exit codes."""

import subprocess
import sys
from pathlib import Path

DRIFT = Path(__file__).resolve().parents[1] / "lib" / "drift.py"


def _run(*args):
    return subprocess.run(
        [sys.executable, str(DRIFT), *args],
        capture_output=True, text=True,
    )


def test_selftest_exits_zero():
    r = _run("--selftest")
    assert r.returncode == 0
    assert "all drift self-tests passed" in r.stdout


def test_no_args_prints_usage_and_exits_1():
    r = _run()
    assert r.returncode == 1
    assert "usage:" in r.stderr


def test_active_vendors_non_integer_exits_1():
    r = _run("--active-vendors", "notanumber", "some.json")
    assert r.returncode == 1
    assert "needs an integer" in r.stderr


def test_active_vendors_without_paths_exits_1():
    r = _run("--active-vendors", "2")
    assert r.returncode == 1
    assert "no merged.json paths" in r.stderr


def test_missing_input_file_is_input_error_exit_3():
    r = _run("/nonexistent/definitely/not/here/merged.json")
    # Broken input pipeline must exit 3 so the orchestrator cannot mistake
    # it for a benign converged tick.
    assert r.returncode == 3
    assert '"verdict": "input_error"' in r.stdout
