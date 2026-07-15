# ak-cross-m-review

Local, pre-PR, **review-only** cross-model gate. Version 0.4 fixes one
base-to-HEAD diff, sends the same packet to independent model families, judges
their candidate findings against named authority, reports once, and stops.

`SKILL.md` is the engine authority. The two prompt files define its correctness
and completeness lenses. ADR 0004 records the owner-approved boundary.

## Five-step shape

1. **Pin target** — require a clean committed repository, resolve the
   user-supplied base and `HEAD`, and materialize one non-empty full diff.
2. **Pin authority** — freeze owner decisions, ADRs, spec/issue clauses, and
   repository contracts.
3. **Choose one lens** — completeness or correctness, never both in one call.
4. **Dispatch panel** — give every transport the same packet plus its own
   independent writable clone of the pinned HEAD, then run them in parallel.
5. **Judge and stop** — verify the union of candidates; report live findings
   and evidence-backed rejections; return one terminal verdict.

The skill never repairs the target, commits, pushes, launches another pass, or
invokes the other lens. Reviewers may write only inside isolated scratch clones
to run tests and probes; repair decisions belong to the outer workflow.

## Named entry points

- `ak-cmr-completeness` presets the completeness lens. Use it first on a
  finished change and on design documents.
- `ak-cmr-correctness` presets the correctness lens. Use it per-slice, or after
  completeness passes for the same finished target.

Both are thin wrappers: they invoke the root engine once, return its report,
and stop.

## Usage

Every call needs a fixed point, scenario, and authority. There is no implicit
base. Panel configuration is shell environment; skill invocation happens in
the agent chat. They are different surfaces.

```bash
export CMR_PANEL=codex,grok
```

Then, in agent chat:

```text
ak-cmr-completeness --base main --scenario ship-pre --authority docs/spec.md
ak-cmr-correctness --base HEAD~1 --scenario per-slice --authority docs/adr/0004-review-only-cmr.md
```

For ship-pre or a design document, the outer workflow calls completeness
first. A later correctness call names the successful completeness result and
the same resolved base/HEAD pair.

Direct engine use is available when the lens must be explicit:

```text
ak-cross-m-review --base HEAD~1 --scenario per-slice --lens correctness --authority docs/adr/0004-review-only-cmr.md
```

## Panel and quota switching

The default is deliberately small and does not require Claude:

```text
CMR_PANEL=codex,grok
```

Supported panel tokens are `codex`, `grok`, optional `claude`, formal optional
`gemini`/`agy`, and optional `opencode`. A panel needs at least two successful,
actually distinct model families. Unknown or repeated tokens fail before
dispatch. Models are explicit. A degraded member is not replaced by another
panel leg; the agy member has the declared quota-only second pool below.

Transport overrides:

| transport | model/effort controls |
|---|---|
| Codex | `gpt-5.6-sol`, `CMR_CODEX_EFFORT=medium` by default; `low` allowed |
| Grok | `grok-4.5`, effort `high` |
| Claude preset | explicitly requests Opus 4.8 via an independent host Agent |
| agy | `AGY_MODEL` primary; `AGY_FALLBACK_MODEL` quota-only second pool (empty disables) |
| OpenCode | `CMR_OPENCODE_MODEL` defaults to `opencode-go/glm-5.2`; optional `CMR_OPENCODE_VARIANT` |

Family is derived from the model/vendor actually used, not a configurable
`FAMILY` label. Default OpenCode GLM counts as Z.AI; an OpenCode model served by
OpenAI is the same family as Codex. The `claude` preset explicitly requests
Opus 4.8 through an independent host Agent and never inherits the host default
or Fable routing. If unavailable, the leg degrades; the caller may explicitly
select another panel transport/model.

agy calls `AGY_MODEL` once (default `Gemini 3.5 Flash (High)`). Only a confirmed
quota/429 may call `AGY_FALLBACK_MODEL` once (default `Claude Sonnet 4.6
(Thinking)`); set it to an empty value to disable the second pool. Auth and
other failures do not retry. The successful model's actual family counts.

For a lower-cost Codex leg, set:

```bash
export CMR_CODEX_EFFORT=low
```

If Grok is unavailable, switch explicitly to the tested agy transport:

```bash
export AGY_MODEL='Gemini 3.5 Flash (High)'
export AGY_FALLBACK_MODEL='Claude Sonnet 4.6 (Thinking)'
export CMR_PANEL=codex,gemini
```

Or use the OpenCode GLM leg:

```bash
export CMR_PANEL=codex,opencode
export CMR_OPENCODE_MODEL='opencode-go/glm-5.2'
```

Then start the new review in agent chat, not the shell:

```text
ak-cmr-correctness --base HEAD~1 --scenario per-slice --authority docs/adr/0004-review-only-cmr.md
```

## What ships

```text
SKILL.md                         five-step review engine and judge
prompts/cmr-reviewer.md          Trace–Break–Prove correctness lens
prompts/cmr-completeness.md      Clause–Wire–Exercise completeness lens
skills/ak-cmr-completeness/      completeness preset
skills/ak-cmr-correctness/       correctness preset
backends/codex-review.sh         incident-backed Codex transport
backends/grok-review.sh          thin Grok transport
backends/gemini.sh               agy / Gemini 3.5 Flash transport
backends/opencode-review.sh      thin OpenCode transport
scripts/install-skills.sh        installs the engine and both presets
docs/adr/0004-review-only-cmr.md owner supersession decision
```

The CLI invocation forms have executable behavior tests in their adapter
slices. Prompt prose is governed by review and git history, not phrase-pinning
tests (ADR 0003).

## Boundary

- CMR is a local gate; it does not replace online PR review or later ship
  checks.
- User-facing factual claims still need grounded source verification outside
  this repository.
- Review-only is an outcome boundary, not filesystem read-only. Every reviewer
  gets a separate writable clone at `LEG_ROOT`; it may install, test, and probe
  there, but may not repair, commit, push, or mutate remotes.
- A leg is not a linked worktree: its Git config, refs, and object store are
  independent, and its source remote is removed before dispatch.
- Backends resolve from the installed skill directory and run with cwd at their
  own `LEG_ROOT`; reviewers never receive the original target path.
- Before the verdict, the engine seals only the original target. Only clean,
  unmoved, remote-free scratch clones are discarded; dirty, moved, or
  remote-changed scratch is preserved and reported without reset or cleanup.
- The caller owns every edit, commit, retry, and subsequent gate.

## Installation

```bash
scripts/install-skills.sh
```

## License

MIT. See [LICENSE](./LICENSE).
