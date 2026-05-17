# Testing

100% test coverage is the key to great vibe coding. Tests let you move
fast, trust your instincts, and ship with confidence — without them,
vibe coding is just yolo coding. With tests, it's a superpower.

## Framework

- **pytest** 9.x (+ `pytest-cov`), Python 3.12+.
- Config: `pyproject.toml` → `[tool.pytest.ini_options]`
  (`pythonpath = ["lib"]`, `testpaths = ["tests"]`).
- Local dev uses a project venv (`.venv/`, gitignored).

## How to run

```bash
python3 -m venv .venv && .venv/bin/pip install pytest pytest-cov
.venv/bin/pytest
```

Or, if pytest is on PATH: `pytest`.

## Test layers

Two complementary layers, both run in CI (`.github/workflows/test.yml`):

1. **Unit tests (`tests/`)** — pytest tests for the deterministic core in
   `lib/` (`merge.py`, `drift.py`, `extract_json.py`, `apply_diff.py`).
   Real input/output assertions, no external CLIs touched.
2. **Selftest battery** — each deterministic module ships an in-process
   `--selftest` mode that is the regression guard for its own logic:
   `python3 lib/merge.py --selftest`, `python3 lib/drift.py --selftest`,
   `bash backends/codex-review.sh --selftest` (dry-run, never calls codex).

E2E / integration of the full N+1+1 reviewer loop is exercised by running
the skill itself against a real diff — not unit-tested (it shells out to
`claude` / `codex` / `gemini`).

## Conventions

- Test files: `tests/test_<module>.py`; functions `test_<behavior>`.
- Assert real computed values, never `assert x is not None` / existence
  smoke checks.
- Mock nothing in the core tests — `lib/` functions are pure; feed real
  inputs and assert exact outputs.
- New function → add a `tests/test_*.py` case. Bug fix → regression test.
  New conditional branch → test both paths.
- Never import secrets/API keys in tests.
- Never commit code that makes the suite or the selftest battery red.
