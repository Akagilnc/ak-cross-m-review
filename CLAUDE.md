# ak-cross-m-review

Local, pre-PR cross-model review skill (v3 vendor squad by trigger point:
ship-pre = N codex + 1 Claude Agent + 1 Gemini via `agy`; per-slice =
N codex + agy under main=Claude — every squad must meet the host
minimum-leg guarantee (SKILL.md Step 1, RECORDED 2026-07-14: main=Claude
→ ≥1 codex leg; main=Codex → ≥1 Claude opus leg; other hosts → ≥1 of
codex/Claude); agy down → grok-4.5 high substitutes, Step 3). `SKILL.md`
is the entry — with `DOC-MODE.md`,
its disclosed file, the two form the standalone authority for cmr in this
environment; merge / grade / drift / termination are agent
**judgment**, NOT a deterministic engine. Reviewers return a **prose**
review (no sentinel-JSON; the `lib/extract_json.py` parser was removed in
0.3.9.0 — it dropped the strongest reviewer's prose as a phantom outage).
`backends/` holds the corrected reviewer invocations (pass a successful
review through verbatim, degrade only on a true outage); `prompts/` the
two review lenses — `cmr-reviewer.md` (correctness, P0–P4) and
`cmr-completeness.md` (was the spec fully delivered? — added 0.3.14.0; it
was prose-only before, so ship-pre's Step-5 gate never actually ran) —
plus `cmr-fixer.md`. See `README.md` for architecture. The historical
origin is
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
