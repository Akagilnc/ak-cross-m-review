# Testing

The surviving suite has two layers. Both cover executable behavior; prose
rules are tracked in prose and git history, not pinned by pytest.

## Framework

- **pytest** 9.x (+ `pytest-cov`), Python 3.12+.
- Config: `pyproject.toml` → `[tool.pytest.ini_options]`
  (`testpaths = ["tests"]`).
- Local dev uses a project venv (`.venv/`, gitignored).

## How to run

```bash
python3 -m venv .venv && .venv/bin/pip install pytest pytest-cov
.venv/bin/pytest
```

Or, if pytest is on PATH: `pytest`.

## Test layers

1. **pytest subprocess behavioral tests** — `tests/test_codex_review.py` and
   `tests/test_gemini.py` execute `backends/codex-review.sh` and
   `backends/gemini.sh`. They stub `codex` / `agy` on PATH, so they exercise
   backend behavior without real reviewer CLI calls.
2. **codex-review.sh invocation-form guard** —
   `bash backends/codex-review.sh --selftest` validates the invocation form
   without calling codex. Pytest also drives this selftest with supported
   environment-variable combinations.

Doc-consistency tests were removed by adjudication on 2026-07-13 (issue #38).
Rule provenance lives in prose `RECORDED` markers and git history, not pytest.

Merge / grade / drift / termination are **agent judgment** per `SKILL.md`,
not deterministic code. The full N+1+1 reviewer
loop is exercised by running the skill itself against a real diff.

## Conventions

- Test files: `tests/test_<module>.py`; functions `test_<behavior>`.
- Assert real computed values, never `assert x is not None` / existence
  smoke checks.
- Mock nothing in the core tests — stub the reviewer CLIs (`codex` / `agy`)
  on PATH and assert the backend's exact stdout / exit / flags.
- New executable function → add a `tests/test_*.py` case. Executable bug fix
  → regression test. New executable conditional branch → test both paths.
- Never import secrets/API keys in tests.
- Never commit code that makes the suite or the selftest battery red.
