# ak-cross-m-review

Local, pre-PR, **review-only** cross-model gate. Version 0.4 fixes one
base-to-HEAD range, gives each model family an independent clone plus the same
small task packet, judges their candidate findings against named authority,
reports once, and stops. Reviewers read the diff and repository themselves;
explicit `--lens all` runs completeness and, after `complete`, correctness with
fresh panels.

`SKILL.md` plus each selected prompt under `prompts/` is the complete active
authority. ADR 0004 records the owner-approved boundary.

## Five-step shape

1. **Pin target** — fix the reviewed base-to-HEAD snapshot.
2. **Pin authority** — fix the sources that govern the review.
3. **Choose lens sequence** — independent completeness or correctness, or
   explicit ordered `all` inside this invocation.
4. **Dispatch panel** — run every reviewer from its own clone with the same
   pinned commands, lens, authority list, and candidate contract.
5. **Judge and stop** — adjudicate candidates and return one terminal verdict.

## Named entry points

- `ak-cmr-completeness` presets the completeness lens.
- `ak-cmr-correctness` presets the correctness lens.

Both are thin wrappers: they invoke the root engine once, return its report,
and stop.

The generic `ak-cross-m-review` entry also accepts explicit `--lens all`. Lens
omission is an error, not an `all` default. `all` stops on completeness gaps;
after `complete`, it launches a fresh correctness panel against the same pinned
target and authority. This internal order does not make either named lens a
prerequisite for the other.

## Minimal usage

```bash
export CMR_PANEL=codex,grok
```

Then, in agent chat:

Correctness review of code:

```text
/ak-cmr-correctness --base HEAD~1 --mode code --authority docs/specs/feature.md
```

Independent completeness review of code:

```text
/ak-cmr-completeness --base main --mode code --authority docs/specs/feature.md
```

Explicit ordered review:

```text
/ak-cross-m-review --base main --mode code --lens all --authority docs/specs/feature.md
```

Explicit ordered document review:

```text
/ak-cross-m-review --base main --mode doc --lens all --authority docs/adr/0042-feature-design.md
```

## Panel and quota switching

See `SKILL.md` Step 4. Adapter CLI contracts live in `backends/` and their
behavior tests.

## What ships

```text
SKILL.md                         five-step review engine and judge
prompts/cmr-reviewer.md          Trace–Break–Prove correctness lens
prompts/cmr-completeness.md      Clause–Wire–Exercise completeness lens
skills/ak-cmr-completeness/      completeness preset
skills/ak-cmr-correctness/       correctness preset
backends/codex-review.sh         incident-backed Codex transport
backends/grok-review.sh          thin Grok transport
backends/claude-review.sh        thin Claude CLI transport
backends/gemini.sh               agy transport
backends/opencode-review.sh      thin OpenCode transport
scripts/install-skills.sh        installs the engine and both presets
docs/adr/0004-review-only-cmr.md owner supersession decision
```

CLI invocation and failure reporting have executable behavior tests in their
adapter slices. Prompt prose is governed by review and git history, not
phrase-pinning tests (ADR 0003).

## Boundary

See `SKILL.md` Steps 4–5 and each selected lens prompt. They supersede summaries
in non-authoritative project documentation.

## Installation

```bash
scripts/install-skills.sh
```

## License

MIT. See [LICENSE](./LICENSE).
