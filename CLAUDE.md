# ak-cross-m-review

Local, pre-PR, review-only cross-model gate. `SKILL.md` is the five-step engine
authority; `prompts/cmr-reviewer.md` and `prompts/cmr-completeness.md` are the
two executable lenses. The named skills under `skills/` are preset entry points,
not separate engines. ADR 0004 records the owner-approved v0.4 boundary.

`backends/` contains transport adapters only. A transport does not judge,
repair, or choose another model. `backends/gemini.sh` is the formal optional
agy/Gemini transport; the default CMR panel remains Codex + Grok.

Review-only is not filesystem read-only. Each reviewer runs in its own writable
independent clone at `LEG_ROOT` for tests and probes; it never receives the
original target and may not repair, commit, push, or mutate remote state. Never
use a linked worktree: remove the clone's source remote before dispatch, and do
not share Git config, refs, or objects with the target.

## Testing

Run: `pytest` (or `.venv/bin/pytest`). Then run:

```bash
bash backends/codex-review.sh --selftest
```

Full conventions are in [TESTING.md](./TESTING.md).

- Tests cover executable backend behavior, not Markdown wording (ADR 0003).
- New executable behavior or error paths require behavioral coverage.
- Preserve the incident-backed Codex invocation guard and agy transport tests.
- Grok invocation behavior belongs to its thin adapter and adapter tests, not
  duplicated prose in `SKILL.md`.
- Never commit with a red test or selftest.
