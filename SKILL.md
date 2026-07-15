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

```text
/ak-cross-m-review --base FIXED_POINT
                   --scenario per-slice|ship-pre|design-doc
                   --lens completeness|correctness
                   --authority SOURCE [--authority SOURCE ...]
```

## Step 1 — Pin the target

The user-supplied fixed point and the current `HEAD` define the whole review.
There is no implicit `main`, range, worktree-diff, or small-change exception.

1. Resolve both endpoints with `git rev-parse --verify
   "${BASE}^{commit}"` and `git rev-parse --verify 'HEAD^{commit}'`.
2. Record `BASE_SHA`, `HEAD_SHA`, and `git log --oneline
   "$BASE_SHA..$HEAD_SHA"`.
3. Materialize `git diff --binary "$BASE_SHA...$HEAD_SHA"` once into a
   temporary file. Record its checksum and changed-file list.
4. Reuse those exact bytes for every panel member. Never regenerate or narrow
   the diff after seeing a review.

An absent/unresolvable base, identical endpoints, or empty diff ends the
invocation with `CMR-VERDICT: hard-stop`. Report the failed command and its
output; do not launch reviewers.

Completion criterion: both endpoint SHAs and one non-empty immutable diff are
visible in the tool record.

## Step 2 — Pin the authority

Build one ordered authority set before dispatch:

1. the user's explicit decisions and supplied sources;
2. ratified ADRs, acceptance text, PRD/spec, and originating issue;
3. repository contracts such as AGENTS/CLAUDE/CONTRIBUTING, public APIs, and
   behavior tests;
4. surrounding code only as evidence of an established contract — the changed
   implementation is not authority for itself.

Follow references named by a higher authority. Put the exact authority list
and the load-bearing excerpts in the packet so every panel member sees the
same constitution. A lower source cannot override a higher one.

The completeness lens requires clause-level authority. If no source states
what had to be delivered, return `CMR-VERDICT: hard-stop` with
`missing completeness authority`. Correctness may proceed from repository
contracts when no feature spec exists, but those contracts must be named.

Completion criterion: the packet contains a frozen, ordered authority set;
completeness additionally has an enumerable clause list.

## Step 3 — Choose one lens

Load exactly one prompt:

- `prompts/cmr-reviewer.md` — **correctness**: Trace–Break–Prove real defects
  in what exists.
- `prompts/cmr-completeness.md` — **completeness**: Clause–Wire–Exercise what
  the authority required but the change omitted, contradicted, or left hollow.

The scenario is a gate, not a panel-shape switch:

- `per-slice` accepts correctness only.
- `ship-pre` and `design-doc` are two separate outer calls: completeness
  first, then correctness after completeness passes for the same target.
- A ship-pre/design-doc correctness call without a prior completeness result
  naming the same `BASE_SHA` and `HEAD_SHA` hard-stops.

Use backend mode `doc` for `design-doc`; use `code` for the other scenarios.

The outer workflow owns sequencing and any later repair. This engine neither
persists cross-call state nor calls its sibling lens.

Completion criterion: scenario, lens, prompt path, and any prerequisite gate
result agree before dispatch.

## Step 4 — Dispatch the panel

Default panel:

```text
CMR_PANEL=codex,grok
```

Supported tokens and their real transport families:

| token | transport | family |
|---|---|---|
| `codex` | `stdin packet \| backends/codex-review.sh <mode> <label>` | OpenAI |
| `grok` | `stdin packet \| backends/grok-review.sh <mode> <label>` | xAI |
| `claude` | independent host Agent or one-shot Claude CLI | Anthropic |
| `gemini` / `agy` | `stdin packet \| backends/gemini.sh <mode>` | the vendor of the model actually served |

`gemini` and `agy` are aliases for one legacy transport; selecting both is a
duplicate. For CMR, one explicit `AGY_MODEL` is required so that transport runs
one model. A backend message such as
`NO Google voice this round` means the successful leg is not Google-family.

Configuration belongs to each transport. Codex model/effort overrides are
`CMR_CODEX_MODEL` / `CMR_CODEX_EFFORT`; Grok overrides are
`CMR_GROK_MODEL` / `CMR_GROK_EFFORT` and are implemented by its adapter;
Claude uses `CMR_CLAUDE_MODEL` when explicitly selected. Family is observed
from the real transport/vendor and is never supplied by a `*_FAMILY` variable.

Preflight `CMR_PANEL` before launch. Unknown tokens, repeated tokens, aliases
that resolve to the same transport twice, or fewer than two selected transports
hard-stop. Do not probe quota: make the real calls and report real failures.

Build one packet containing the endpoint SHAs, diff checksum, authority set,
selected lens prompt, candidate contract below, and the entire materialized
diff. Launch all selected members in one parallel batch, with no other member's
output in any prompt. Each member runs exactly one configured model; CMR does
not replace a failed member or choose a fallback panel.

A successful CLI member has exit code zero and non-empty review stdout; a host
Agent must return non-empty review text. Record every failed/empty member as
`degraded` with token, model, actual family if known, and error evidence. It is
not an approval. At least two successful members from distinct actual families
are required. Otherwise return `CMR-VERDICT: hard-stop` and print a fully
resolved, copyable retry command using a supported distinct-family panel. It
must begin with `CMR_PANEL=...` and repeat the actual base, scenario, lens, and
authority values from this invocation; placeholders are forbidden.

Completion criterion: every selected member has one success/degraded record,
and at least two successes have distinct actual families.

## Step 5 — Judge and stop

Panel output contains **candidate findings**, not verdicts. Take their union;
agreement is not a vote. Deduplicate only candidates with the same trigger,
execution path, wrong outcome, and impact.

An admissible candidate contains:

- `location` — `path:line` or the nearest stable symbol;
- `claim` — the alleged defect or gap;
- `failure scenario` — `trigger → path → wrong observable outcome`;
- `authority` — the exact requirement or invariant violated;
- `evidence` — source, test, command, or probe result;
- `severity_hint` — impact if the claim is live;
- `remedy` — optional and never required for admission.

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
evidence. End with exactly one terminal line:

- completeness: `CMR-VERDICT: complete` when no live gap remains, otherwise
  `CMR-VERDICT: gaps`;
- correctness: `CMR-VERDICT: converged` when no live defect remains, otherwise
  `CMR-VERDICT: findings`;
- either lens: `CMR-VERDICT: escalate` for a genuine owner decision, or
  `CMR-VERDICT: hard-stop` when a prerequisite or family floor failed.

Then stop unconditionally. The caller decides what happens next.
