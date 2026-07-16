# ak-cross-m-review

Local, pre-PR, review-only cross-model gate. `SKILL.md` plus the selected prompt
under `prompts/` is the complete active authority; named skills under `skills/`
are preset entry points. ADR 0004 records the owner-approved v0.4 boundary.

`backends/` only transport the small review task and return output; they do not
judge or repair. Reviewers run from independent clone roots and read the pinned
diff, authority, surrounding repository, and tests themselves. Runtime dispatch
and scratch lifecycle live in `SKILL.md` Step 4; judgment, sealing, and
termination live in Step 5.

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
