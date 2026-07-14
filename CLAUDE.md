# ak-cross-m-review

Local, pre-PR cross-model review skill. `SKILL.md` is the entry — with
`DOC-MODE.md`, its disclosed file, the two form the standalone authority
for cmr in this environment: squad / dispatch / degradation / termination
rules ALL live there, never here (the user-adjudication ledger = RECORDED
markers + git history). Working principles for this repo: merge / grade /
drift / termination are agent **judgment**, NOT a deterministic engine;
reviewers return **prose** reviews — do not reintroduce sentinel-JSON or
parsers. `backends/` holds the reviewer invocations; `prompts/` the two
review lenses (`cmr-reviewer.md`, `cmr-completeness.md`) plus
`cmr-fixer.md`. See `README.md` for architecture. The historical origin is
`~/WorkSpace/vault/ak-cc-wiki/wiki/concepts/cross-model-review.md`.

## Testing

Run: `pytest` (or `.venv/bin/pytest`). Test directory: `tests/`.
Full conventions and the two-layer model are in
[TESTING.md](./TESTING.md).

Test expectations:

- 100% coverage of executable code is the goal — tests make vibe coding
  safe, not yolo. Docs/prose are never pytest targets (#38; ADR 0003):
  rule provenance = RECORDED markers + git history.
- New executable function → write a corresponding test in
  `tests/test_<module>.py`.
- Executable bug fix → write a regression test that fails before, passes
  after.
- New error path → cover it; keep `bash backends/codex-review.sh
  --selftest` (the invocation-form regression guard) green.
- New executable conditional (if/else, branch) → test BOTH paths.
- Assert real computed values, never existence/smoke checks.
- Never commit code that makes existing tests or the selftest battery
  fail.
