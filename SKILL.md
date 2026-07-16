---
name: ak-cross-m-review
description: One-pass cross-model review of a fixed base-to-HEAD diff. Use per-slice, before a PR, or for design-document review; prefer the named completeness or correctness preset.
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

**REVIEW ONLY.** One invocation pins one target, authority set, lens, and panel
pass, then reports once and stops: no repair, commit, push, another pass, or
other lens. This constrains the outcome, not writable reviewer scratch space.

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
  asked to review; pin and judge the target here.

The user-supplied fixed point and the current committed `HEAD` define the whole
review. There is no implicit `main`, range, worktree-diff, or small-change
exception.

1. Run `git -C "$REPO_ROOT" status --porcelain=v1 --untracked-files=all`; any
   output hard-stops before dispatch and is reported verbatim.
2. Record `PRE_HEAD` from `git -C "$REPO_ROOT" rev-parse --verify
   'HEAD^{commit}'`; resolve the supplied base similarly as `BASE_SHA`.
3. Pin one resolved command for each reviewer to run from its clone, with the
   literal full SHAs substituted for refs:

   ```text
   git log --oneline BASE_SHA..PRE_HEAD
   git diff --binary BASE_SHA...PRE_HEAD
   ```

4. Run the resolved log command at `REPO_ROOT`. Check the resolved range with
   `git -C "$REPO_ROOT" diff --quiet "$BASE_SHA...$PRE_HEAD"`: exit 0 means
   empty and hard-stops; exit 1 means non-empty; any other exit hard-stops.
5. Freeze those two commands. Every reviewer runs them itself in its own clone;
   never regenerate, narrow, segment, compress, or embed the diff in a prompt.

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

Follow references named by a higher authority. Freeze the exact ordered source
list. Repository authority is listed by repository-relative path and read by
each reviewer from its clone; do not paste repository file bodies or excerpts
into the task packet. Include exact user-supplied authority text only when it
has no repository path. A lower source cannot override a higher one.

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

Default panel: `CMR_PANEL=codex,grok`.

Supported tokens, adapters, and real transport families:

| token | adapter | family |
|---|---|---|
| `codex` | `backends/codex-review.sh` | OpenAI |
| `grok` | `backends/grok-review.sh` | xAI |
| `claude` | independent host Agent | Anthropic |
| `gemini` / `agy` | `backends/gemini.sh` | actual model vendor (Google primary; second pool may differ) |
| `opencode` | `backends/opencode-review.sh` | actual model vendor |

Transport configuration:

- Codex uses `CMR_CODEX_MODEL` / `CMR_CODEX_EFFORT` (defaults `gpt-5.6-sol` /
  `medium`; explicit `low` allowed).
- Grok model and effort are configurable with `CMR_GROK_MODEL` /
  `CMR_GROK_EFFORT`.
- The `claude` preset explicitly requests Opus 4.8 through an independent host
  Agent; never inherit the host default or Fable routing. If unavailable,
  degrade the leg; the caller may explicitly select another panel
  transport/model.
- `gemini` and `agy` alias one transport; selecting both is a duplicate. The
  agy adapter calls `AGY_MODEL` once (default `Gemini 3.5 Flash (High)`). Only a
  confirmed quota/429 may call `AGY_FALLBACK_MODEL` once (default `Claude
  Sonnet 4.6 (Thinking)`; empty disables it). Auth and other failures do not
  retry. Count the model that actually succeeds; a non-Google result reports
  `NO Google family this round`.
- OpenCode uses `CMR_OPENCODE_MODEL` (default `opencode-go/glm-5.2`) and optional
  `CMR_OPENCODE_VARIANT`.

Observe family from the actual vendor, never a `*_FAMILY` variable: OpenCode
GLM is Z.AI; OpenAI is not distinct from Codex.

Preflight `CMR_PANEL` before launch. Unknown tokens, repeated tokens, aliases
that resolve to the same transport twice, or fewer than two selected transports
hard-stop. Do not probe quota: make the real calls and report real failures.

Build one small task packet outside `REPO_ROOT` containing only:

- `BASE_SHA` and `PRE_HEAD`;
- the one resolved log command and one resolved diff command from Step 1;
- the selected lens prompt;
- the frozen ordered authority source list; and
- the candidate contract from Step 5.

Do not attach the diff, changed files, repository archive, compressed content,
or preloaded file bodies. Each reviewer owns repository reading, search, and
verification. "Same input" means the same target/range, authority, lens, and
candidate contract, not a serialized diff copy.

For each member, choose a unique `LEG_ROOT` outside the target under a path with
no hidden component (no path segment beginning with `.`), then create an
independent writable clone at `PRE_HEAD`. This keeps every transport able to
discover the repository; agy refuses hidden workspace paths.

```bash
LEG_ROOT="$("$SKILL_ROOT/scripts/prepare-review-clone.sh" \
  "$REPO_ROOT" "$LEG_ROOT" "$PRE_HEAD" "$BASE_SHA")"
```

Do not use a linked worktree, shared object store, reference clone, or
alternates. The helper is the single clone/preflight implementation: it makes
the leg's Git config, refs, and objects independent; detaches at `PRE_HEAD`;
removes the source remote; and emits the canonical `LEG_ROOT` only after
rejecting a destination inside `REPO_ROOT` and verifying the common Git
directory stays inside the leg, the pinned HEAD/base are present, the path has
no hidden component, and status and remotes are empty. Any helper failure
hard-stops before that reviewer runs; preserve the failed clone for diagnosis.

Record token → absolute `LEG_ROOT`; resolve prompts and backends from
`SKILL_ROOT`, `cd` to that member's `LEG_ROOT`, and send the same task packet to
each transport from there. The reviewer starts at the clone root and must run
the pinned log/diff commands, inspect surrounding code and authority paths, and
run useful tests or probes itself. Launch one parallel batch with no peer
output; do not replace a degraded panel member. The declared
agy quota-only second pool above belongs to that one member; it is not a
replacement panel leg.

A reviewer may install dependencies, test, and create probes or local artifacts
in `LEG_ROOT`, but must not repair, commit, push, or mutate remote state.
Checkout mutations are evidence only; judge against the pinned target.

A successful CLI member has exit code zero and non-empty review stdout; a host
Agent must return non-empty review text. Record every failed/empty member as
`degraded` with token, model, actual family if known, and error evidence. It is
not an approval. At least two successful members from distinct actual families
are required. Otherwise return `CMR-VERDICT: hard-stop` and print a fully
resolved retry in two correctly labelled parts: a copyable shell line beginning
with `export CMR_PANEL=...`, followed by a copyable **agent-chat skill
invocation** repeating the actual base, scenario, lens, and authority values.
Placeholders are forbidden; never present a skill invocation as a shell binary.

After output, record each leg's HEAD, `status --porcelain=v1
--untracked-files=all`, and remotes. Discard the independent clone only when
HEAD still equals `PRE_HEAD`, status is empty, and no remote exists. Preserve
and report the path, HEAD, status, and remotes of every dirty, moved, or
remote-changed leg. Never reset, clean, or remove such a leg; scratch state does
not alter the target verdict.

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

`scope_creep` means the proposed fix invents behavior not authorized by the
authority/spec. A defect being pre-existing, in an adjacent file, or
incidentally discovered during review does not make it scope creep.

Before marking a claim live, prove its exact trigger, state taxonomy, and owner
are inside the cited clause. Similar states, adjacent retries, and other
components cannot widen authority: use `not_established` or `scope_creep`.

Reviewer agreement may raise confidence, never severity. Grounding decides
whether the claim is established, never its impact. A test finding is live only
with evidence such as wrong behavior remaining green, the system under test
being mocked out, a material assertion being removed/relaxed, or the relevant
failure path being unable to turn red.

Report every live and refuted/rejected disposition with evidence. Before the
terminal line, seal only the original target:

1. compare `git -C "$REPO_ROOT" rev-parse 'HEAD^{commit}'` with `PRE_HEAD`;
2. rerun `git -C "$REPO_ROOT" status --porcelain=v1 --untracked-files=all`.

Any HEAD change or status output overrides the lens result with
`CMR-VERDICT: hard-stop`. Show the before/after HEAD and status evidence. Never
reset, checkout, remove, or clean `REPO_ROOT`; preserve unexpected target
changes. Step 4 leg cleanup never substitutes for this seal.

With the snapshot still sealed, end with exactly one terminal line:

- completeness: `CMR-VERDICT: complete` when no live gap remains, otherwise
  `CMR-VERDICT: gaps`;
- correctness: `CMR-VERDICT: converged` when no live defect remains, otherwise
  `CMR-VERDICT: findings`;
- either lens: `CMR-VERDICT: escalate` for a genuine owner decision, or
  `CMR-VERDICT: hard-stop` when a prerequisite or family floor failed.

Then stop unconditionally. The caller decides what happens next.
