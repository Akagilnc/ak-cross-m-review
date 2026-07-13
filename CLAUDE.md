# ak-cross-m-review

Local, pre-PR cross-model review skill (v3 vendor squad by trigger point:
ship-pre = N codex + 1 Claude Agent + 1 Gemini via `agy`; per-slice =
N codex + agy, no Claude). `SKILL.md` is the entry — with `DOC-MODE.md`,
together a faithful transcription of the wiki (转写 = 两文件并集, see §Wiki
sync mapping below); merge / grade / drift / termination are agent
**judgment**, NOT a deterministic engine. Reviewers return a **prose**
review (no sentinel-JSON; the `lib/extract_json.py` parser was removed in
0.3.9.0 — it dropped the strongest reviewer's prose as a phantom outage).
`backends/` holds the corrected reviewer invocations (pass a successful
review through verbatim, degrade only on a true outage); `prompts/` the
two review lenses — `cmr-reviewer.md` (correctness, P0–P4) and
`cmr-completeness.md` (was the spec fully delivered? — added 0.3.14.0; it
was prose-only before, so ship-pre's Step-5 gate never actually ran) —
plus `cmr-fixer.md`. See `README.md` for architecture
and `~/WorkSpace/vault/ak-cc-wiki/wiki/concepts/cross-model-review.md`
for the source-of-truth spec.

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

## Wiki sync mapping

转写 = `SKILL.md` + `DOC-MODE.md` 的并集；wiki sync 对照面必须同时覆盖两文件。
边界与去重基准见 [ADR 0001](docs/adr/0001-progressive-disclosure.md)。
