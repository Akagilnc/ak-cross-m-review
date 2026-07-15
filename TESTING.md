# Testing

Tests cover executable transport behavior. Skill and prompt prose are reviewed
as documents and tracked in git history; they are never pinned by pytest (ADR
0003).

## Run

```bash
pytest
bash backends/codex-review.sh --selftest
```

Local development may use `.venv/bin/pytest`. CI uses Python 3.12 and the
configuration in `pyproject.toml`.

## Executable surfaces

- `tests/test_codex_review.py` drives `backends/codex-review.sh` with a stub
  Codex CLI and covers success, real outage, final-message extraction, idle
  handling, and invocation overrides.
- `tests/test_grok_review.py` drives `backends/grok-review.sh` and pins its
  one-shot stdin/model/effort invocation plus failure semantics.
- `tests/test_gemini.py` drives the formal optional agy/Gemini transport in
  `backends/gemini.sh`, which also has external consumers.
- `tests/test_opencode_review.py` drives the optional OpenCode transport in
  `backends/opencode-review.sh`.
- `backends/codex-review.sh --selftest` validates the real command-array form
  without calling Codex.

The target pin, authority choice, candidate adjudication, and final verdict are
agent judgment defined by `SKILL.md`, not deterministic code.

## Conventions

- Test files are `tests/test_<surface>.py`; test names describe behavior.
- Stub the reviewer CLI on `PATH` and assert stdout, stderr, exit status, and
  the actual argv/environment contract.
- New executable behavior gets a failing test first; new branches cover both
  sides. Bug fixes get a regression test that fails on the old behavior.
- Assert computed behavior, not existence or wording.
- Never import secrets or real subscription credentials.
- Keep pytest and the Codex selftest green before commit.
