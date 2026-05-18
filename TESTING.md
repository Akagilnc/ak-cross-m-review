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

1. **Unit tests (`tests/`)** — pytest. `test_extract_json.py` covers
   `lib/extract_json.py` (the only deterministic helper: salvage findings
   JSON from noisy CLI stdout). `test_codex_review.py` is a subprocess
   regression test for `backends/codex-review.sh`'s degrade path (a
   non-zero codex exit must degrade even when its error body is
   salvageable). Real assertions, no real CLI calls.
2. **codex-review.sh selftest** — `bash backends/codex-review.sh
   --selftest` validates the pinned invocation form (no `-C`, stdin
   pipe, `--model gpt-5.5`, `2>&1`); it is the regression guard for the
   codex footguns the wiki lists as hard rules. Never calls codex.

Merge / grade / drift / termination are **agent judgment** per the wiki
(`cross-model-review.md`), not deterministic code — there is no
`merge.py` / `drift.py` to unit-test (removed in 0.2.0.0). The full
N+1+1 reviewer loop is exercised by running the skill itself against a
real diff (it shells out to `claude` / `codex` / `gemini`).

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
