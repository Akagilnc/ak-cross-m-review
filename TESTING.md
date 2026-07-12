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

1. **Unit tests (`tests/`)** — pytest. `test_codex_review.py` /
   `test_gemini.py` are subprocess regression tests for the backends'
   degrade-vs-passthrough gate: a successful reviewer run (exit 0) — even
   pure **prose** with no JSON — must pass through verbatim (exit 0), and
   only a true outage (empty output, a non-zero CLI exit, agy auth-race /
   quota) degrades with "本轮缺 X". They stub `codex` / `agy` on PATH —
   real assertions, no real CLI calls. (There is no `extract_json` parser
   to test — it was removed in 0.3.9.0; reviewers return prose the
   orchestrator reads, not sentinel-JSON.)
2. **codex-review.sh selftest** — `bash backends/codex-review.sh
   --selftest` validates the pinned invocation form (no `-C`, stdin
   pipe, `--model gpt-5.6-sol`, `model_reasoning_effort=medium`, `2>&1`);
   it is the regression guard for the
   codex footguns the wiki lists as hard rules. Never calls codex.

Merge / grade / drift / termination are **agent judgment** per the wiki
(`cross-model-review.md`), not deterministic code — there is no
`merge.py` / `drift.py` to unit-test (removed in 0.2.0.0). The full
N+1+1 reviewer loop is exercised by running the skill itself against a
real diff (it shells out to `claude` / `codex` / `agy` — the last is the
post-EOL replacement for the original `gemini` CLI; see SKILL.md Step 2
invocation forms).

## Conventions

- Test files: `tests/test_<module>.py`; functions `test_<behavior>`.
- Assert real computed values, never `assert x is not None` / existence
  smoke checks.
- Mock nothing in the core tests — stub the reviewer CLIs (`codex` /
  `agy`) on PATH and assert the backend's exact stdout / exit / flags.
- New function → add a `tests/test_*.py` case. Bug fix → regression test.
  New conditional branch → test both paths.
- Never import secrets/API keys in tests.
- Never commit code that makes the suite or the selftest battery red.
