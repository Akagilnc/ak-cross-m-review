---
name: ak-cross-m-review
description: Run one read-only cross-model review pass against a fixed base-to-HEAD diff. Use per-slice, before a PR, or for design-document review; the named completeness and correctness skills are the preferred entry points.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Agent
---

# /ak-cross-m-review — one-pass review engine

This repository's CMR authority is this file plus the selected lens prompt.
The wiki is lineage, not an override (ADR 0002); ADR 0004 supersedes the prior
procedure.

**REVIEW ONLY.** One invocation pins one target, one authority set, one lens,
and one independent panel pass. It returns a judged report and stops. It does
not edit, repair, commit, dispatch another pass, or invoke the other lens.

Prefer the named presets `ak-cmr-completeness` and `ak-cmr-correctness`.
Direct engine invocation must provide every required input explicitly:

`/ak-cross-m-review --base FIXED_POINT --scenario per-slice|ship-pre|design-doc
--lens completeness|correctness --authority SOURCE [--authority SOURCE ...]`

## Step 1 — Pin the target

The reviewed repository must be a clean committed snapshot. Resolve two roots
without conflating them:

- `SKILL_ROOT` — the absolute physical directory containing this loaded
  `SKILL.md`; prompts and backends resolve from here.
- `REPO_ROOT` — `git rev-parse --show-toplevel` from the repository the caller
  asked to review; all review commands and reviewer transports run here.

The user-supplied fixed point and the current committed `HEAD` define the whole
review. There is no implicit `main`, range, worktree-diff, or small-change
exception.

1. Run `git -C "$REPO_ROOT" status --porcelain=v1 --untracked-files=all`; any
   output hard-stops before dispatch and is reported verbatim.
2. Record `PRE_HEAD` from `git -C "$REPO_ROOT" rev-parse --verify
   'HEAD^{commit}'`; resolve the supplied base similarly as `BASE_SHA`.
3. Record `git -C "$REPO_ROOT" log --oneline "$BASE_SHA..$PRE_HEAD"`.
4. Outside the reviewed repository, materialize `git -C "$REPO_ROOT" diff
   --binary "$BASE_SHA...$PRE_HEAD"` once; record its checksum and file list.
5. Reuse those exact bytes for every panel member. Never regenerate or narrow
   the diff after seeing a review.

An unresolved root/ref, dirty or untracked path, identical endpoints, or empty
diff ends the invocation with `CMR-VERDICT: hard-stop`. Report the failed
command and its output; do not launch reviewers.

## Step 2 — Pin the authority

Build one ordered authority set before dispatch:

1. the user's explicit decisions and supplied sources;
2. ratified ADRs, acceptance text, PRD/spec, and originating issue;
3. repository contracts: AGENTS/CLAUDE/CONTRIBUTING, public APIs, behavior tests;
4. surrounding code only as evidence of an established contract — the changed
   implementation is not authority for itself.

Follow references named by a higher authority. Put the exact authority list
and the load-bearing excerpts in the packet so every panel member sees the
same constitution. A lower source cannot override a higher one.

The completeness lens requires line-addressable clause authority. Every clause
must cite an actual authority `path:line`; an unlocated summary cannot establish
an absence. If no source states what had to be delivered, return
`CMR-VERDICT: hard-stop` with `missing completeness authority`. Correctness may
proceed from repository contracts when no feature spec exists, but those
contracts must be named.

## Step 3 — Choose one lens

Load exactly one prompt:

- `prompts/cmr-reviewer.md` — **correctness**: Trace–Break–Prove real defects.
- `prompts/cmr-completeness.md` — **completeness**: Clause–Wire–Exercise gaps.

The scenario is a gate, not a panel-shape switch:

- `per-slice` accepts correctness only.
- `ship-pre` and `design-doc` are two separate outer calls: completeness
  first, then correctness after completeness passes for the same target.
- A ship-pre/design-doc correctness call without a prior completeness result
  naming the same `BASE_SHA` and `PRE_HEAD` hard-stops.

Use backend mode `doc` for `design-doc`; use `code` for the other scenarios.

The outer workflow owns sequencing and any later repair. This engine neither
persists cross-call state nor calls its sibling lens.

## Step 4 — Dispatch the panel

Default panel:

```text
CMR_PANEL=codex,grok
```

Supported tokens and their real transport families:

| token | transport | family |
|---|---|---|
| `codex` | `stdin packet \| "$SKILL_ROOT/backends/codex-review.sh" <mode> <label>`; `gpt-5.6-sol`, effort `medium` (or explicit `low`) | OpenAI |
| `grok` | `stdin packet \| "$SKILL_ROOT/backends/grok-review.sh" <mode> <label>`; `grok-4.5` | xAI |
| `claude` | independent host Claude Agent, Opus 4.8 only | Anthropic |
| `gemini` / `agy` | `stdin packet \| "$SKILL_ROOT/backends/gemini.sh" <mode>`; Gemini 3.5 Flash | Google |
| `opencode` | `stdin packet \| "$SKILL_ROOT/backends/opencode-review.sh" <mode> <label>`; default `opencode-go/glm-5.2` | actual model vendor |

`gemini` and `agy` are aliases for one transport; selecting both is a duplicate.
For CMR, set `AGY_MODEL='Gemini 3.5 Flash'` so that transport runs its one formal
CMR model. A backend message such as
`NO Google voice this round` means the successful leg is not Google-family.

`claude` means exactly an independent host Claude Agent running Opus 4.8. If the
host cannot explicitly dispatch that model, record the leg unavailable or
degraded; Sonnet and other Claude models cannot substitute. There is no
one-shot CLI path.

Transport configuration: Codex uses `CMR_CODEX_MODEL` / `CMR_CODEX_EFFORT`
(defaults `gpt-5.6-sol` / `medium`; explicit `low` allowed); Grok uses
`CMR_GROK_MODEL` / `CMR_GROK_EFFORT` (defaults `grok-4.5` / `high`); OpenCode
uses `CMR_OPENCODE_MODEL` (default `opencode-go/glm-5.2`) and optional
`CMR_OPENCODE_VARIANT`. Observe family from the actual vendor, never a
`*_FAMILY` variable: OpenCode GLM is Z.AI; OpenAI is not distinct from Codex.

Preflight `CMR_PANEL` before launch. Unknown tokens, repeated tokens, aliases
that resolve to the same transport twice, or fewer than two selected transports
hard-stop. Do not probe quota: make the real calls and report real failures.

Build one packet outside `REPO_ROOT` containing the endpoint SHAs, diff
checksum, authority, selected lens prompt, candidate contract, and materialized
diff. Launch all selected members in one parallel batch, with no other member's
output in any prompt. Each member runs exactly one configured model; CMR does
not replace a failed member or choose a fallback panel. Resolve every prompt
and backend from `SKILL_ROOT`; invoke every transport with cwd fixed to
`REPO_ROOT`. The reviewed repository is never assumed to contain `backends/`.

A successful CLI member has exit code zero and non-empty review stdout; a host
Agent must return non-empty review text. Record every failed/empty member as
`degraded` with token, model, actual family if known, and error evidence. It is
not an approval. At least two successful members from distinct actual families
are required. Otherwise return `CMR-VERDICT: hard-stop` and print a fully
resolved retry in two correctly labelled parts: a copyable shell line beginning
with `export CMR_PANEL=...`, followed by a copyable **agent-chat skill
invocation** repeating the actual base, scenario, lens, and authority values.
Placeholders are forbidden; never present a skill invocation as a shell binary.

## Step 5 — Judge and stop

Panel output contains **candidate findings**, not verdicts. Take their union;
agreement is not a vote. Deduplicate only candidates with the same trigger,
execution path, wrong outcome, and impact.

An admissible candidate contains:

- `location` — an actual `path:line` in the reviewed repository;
- `claim` — the alleged defect or gap;
- `failure scenario` — `trigger → path → wrong observable outcome`;
- `authority` — the exact requirement or invariant violated;
- `evidence` — source, test, command, or probe result;
- `severity_hint` — impact if the claim is live;
- `remedy` — optional and never required for admission.

Correctness candidates use the actual affected `path:line`. A completeness
absence cites both its authority `path:line` and the nearest actual affected or
expected consumer `path:line`; without both locations it is not admissible.

Verify each candidate against the fixed target and authority. Judge the defect
claim separately from its remedy:

```text
defect: live | refuted
reason: <one of unconstitutional | over_defense | not_established | scope_creep when refuted>
evidence: <required for every refutation>
severity: <impact only; live findings only>
remedy: none | advisory | rejected | owner_decision
remedy_reason: <reason + evidence when rejected>
```

The four lawful rejection reasons are: conflict with ratified authority;
defense whose probability, consequence, and downstream backstop do not justify
its cost; claim not established by the current target; or behavior invented
outside the authority. Difficulty is not a rejection reason. A real defect
stays live when only its proposed remedy is rejected. Deletion/simplification
outranks adding an equivalent mechanism.

Reviewer agreement may raise confidence, never severity. Grounding decides
whether the claim is established, never its impact. A test finding is live only
with evidence such as wrong behavior remaining green, the system under test
being mocked out, a material assertion being removed/relaxed, or the relevant
failure path being unable to turn red.

Report every live finding and every refuted/rejected disposition with its
evidence. Before writing the terminal line, seal the snapshot:

1. compare `git -C "$REPO_ROOT" rev-parse 'HEAD^{commit}'` with `PRE_HEAD`;
2. rerun `git -C "$REPO_ROOT" status --porcelain=v1 --untracked-files=all`.

Any HEAD change or status output overrides the lens result with
`CMR-VERDICT: hard-stop`. Show the before/after HEAD and status evidence. Never
reset, checkout, remove, or clean anything; preserve every reviewer-produced
file and modification exactly for the caller to decide.

With the snapshot still sealed, end with exactly one terminal line:

- completeness: `CMR-VERDICT: complete` when no live gap remains, otherwise
  `CMR-VERDICT: gaps`;
- correctness: `CMR-VERDICT: converged` when no live defect remains, otherwise
  `CMR-VERDICT: findings`;
- either lens: `CMR-VERDICT: escalate` for a genuine owner decision, or
  `CMR-VERDICT: hard-stop` when a prerequisite or family floor failed.

Then stop unconditionally. The caller decides what happens next.
