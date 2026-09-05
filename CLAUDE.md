# ak-cross-m-review

Local, pre-PR, review-only CMR. `SKILL.md` plus each selected prompt under
`prompts/` is the complete active authority. `CONTEXT.md` defines vocabulary,
and ADR 0005 records the owner-approved v0.5 boundary. The named skills under
`skills/` are presets.

## Operation

Use `SKILL.md` Steps 1–5 for pinning, authority, lens selection, harness
dispatch, judgment, sealing, and termination. Do not duplicate that procedure
here. The harness must provide sub-agents and isolated copies; this repository
provides instructions and prompts only.

Install the engine and both presets with:

```bash
scripts/install-skills.sh
```

## Testing

This repository has no executable surface and no tests. ADR 0003 still forbids
tests that pin documentation wording; review prose changes against the active
authority and Git diff.
