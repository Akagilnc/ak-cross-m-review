# ak-cross-m-review

Local, pre-PR cross-model review skill (v3 vendor squad: N codex + 1
Claude opus Agent + 1 Gemini). `SKILL.md` is the entry; `lib/` holds the
deterministic core; `backends/` the corrected reviewer invocations;
`prompts/` the reviewer/fixer prompts. See `README.md` for architecture
and `~/WorkSpace/vault/ak-cc-wiki/wiki/concepts/cross-model-review.md`
for the source-of-truth spec.

## Testing

Run: `pytest` (or `.venv/bin/pytest`). Test directory: `tests/`.
Full conventions and the two-layer model are in
[TESTING.md](./TESTING.md).

Test expectations:

- 100% coverage is the goal — tests make vibe coding safe, not yolo.
- New function → write a corresponding test in `tests/test_<module>.py`.
- Bug fix → write a regression test that fails before, passes after.
- New error path → cover it; keep `bash backends/codex-review.sh
  --selftest` (the invocation-form regression guard) green.
- New conditional (if/else, branch) → test BOTH paths.
- Assert real computed values, never existence/smoke checks.
- Never commit code that makes existing tests or the selftest battery
  fail.
