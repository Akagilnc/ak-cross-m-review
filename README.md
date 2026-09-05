# ak-cross-m-review

Local, pre-PR, review-only CMR. Version 0.5 runs completeness and correctness
as independent lens legs; an `all` invocation dispatches both in parallel. The
harness owns sub-agent execution; each leg runs in an independent copy of the
target that the harness provides when it can and the caller creates otherwise.
The invoking session judges each result against one fixed target and authority
set. ADR 0005 records the owner decision.

`SKILL.md` plus each selected prompt under `prompts/` is the complete active
authority. For the executable review procedure, see `SKILL.md` Steps 1–5; this
README does not duplicate those rules. Vocabulary is defined in `CONTEXT.md`.

## Presets

- `ak-cmr-completeness` invokes the engine once for completeness.
- `ak-cmr-correctness` invokes the engine once for correctness.

Both return the engine report unchanged. Direct engine invocation also supports
both lenses together; see `SKILL.md` Invocation.

## Dependencies

- a harness that can dispatch sub-agents in isolated copies;
- Git for pinning and sealing the fixed target.

The review engine has no executable surface or tests; `scripts/install-skills.sh`
is an installation helper only. The harness supplies the execution environment.

## Repository map

```text
SKILL.md                         review engine and judge
CONTEXT.md                       vocabulary
prompts/cmr-reviewer.md          Trace–Break–Prove correctness lens
prompts/cmr-completeness.md      Clause–Wire–Exercise completeness lens
skills/ak-cmr-completeness/      completeness preset
skills/ak-cmr-correctness/       correctness preset
scripts/install-skills.sh        installs the engine and both presets
docs/adr/0005-two-parallel-lens-legs.md  v0.5 owner decision
```

## Installation

```bash
scripts/install-skills.sh
```

## License

MIT. See [LICENSE](./LICENSE).
