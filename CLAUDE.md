# ak-cross-m-review

Local, pre-PR cross-model review skill (v3 vendor squad by trigger point:
ship-pre = N codex + 1 Claude Agent + 1 Gemini via `agy`; per-slice =
N codex + agy, no Claude). `SKILL.md` is the entry — a faithful
transcription of the wiki; merge / grade / drift / termination are agent
**judgment**, NOT a deterministic engine. Reviewers return a **prose**
review (no sentinel-JSON; the `lib/extract_json.py` parser was removed in
0.3.9.0 — it dropped the strongest reviewer's prose as a phantom outage).
`backends/` holds the corrected reviewer invocations (pass a successful
review through verbatim, degrade only on a true outage); `prompts/` the
reviewer/fixer prompts. See `README.md` for architecture
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
