# ak-cross-m-review domain language

- **fixed target** — a clean committed `REPO_ROOT`, resolved `BASE_SHA`, recorded
  `PRE_HEAD`, and one materialized full diff reused by every reviewer, then
  resealed against HEAD and status before the terminal verdict.
- **skill root** — the physical directory containing the loaded `SKILL.md`.
  Prompts and adapters resolve from here; transports run with cwd at
  `REPO_ROOT`.
- **authority set** — the ordered owner decisions, ADR/spec/issue clauses, and
  repository contracts frozen before dispatch. Changed code is evidence, not
  authority for itself.
- **lens** — one question asked of the fixed target. Correctness uses
  `prompts/cmr-reviewer.md`; completeness uses
  `prompts/cmr-completeness.md`.
- **correctness** — Trace–Break–Prove a reachable counterexample in behavior
  that exists.
- **completeness** — Clause–Wire–Exercise each authoritative requirement and
  find delivery that is missing, contradicted, partial, or hollow.
- **preset** — a named wrapper that selects one lens and returns the root
  engine result unchanged. It has no review procedure of its own.
- **panel token** — one supported transport selected by `CMR_PANEL`: `codex`,
  `grok`, optional host-Agent `claude`, formal optional `gemini`/`agy`, or
  optional `opencode`. `claude` is exactly host-Agent Opus 4.8; no other Claude
  model substitutes.
- **actual family** — the vendor family of the model that really produced a
  review. It is transport evidence, never a caller-supplied label. OpenCode
  GLM is Z.AI; an OpenAI model through OpenCode is the same family as Codex.
- **degraded member** — a selected transport that failed or returned no review.
  It remains visible and never counts as approval.
- **candidate** — one reviewer's evidence-backed claim containing location,
  claim, failure scenario, authority, evidence, and severity hint; remedy is
  optional.
- **judge** — the main session that verifies the union of candidates against
  the fixed target and authority, separately adjudicating defect and remedy.
- **lawful rejection** — `unconstitutional`, `over_defense`,
  `not_established`, or `scope_creep`, always with evidence.
- **terminal verdict** — completeness returns `complete|gaps`; correctness
  returns `converged|findings`; either may return `escalate|hard-stop`.
- **review only** — CMR reports and stops. The caller owns edits, commits,
  retries, and later gates. Unexpected target mutation hard-stops without
  reset, checkout, removal, or cleanup; every output is preserved.
- **deletion outranks addition** — for equivalent behavior, remove or simplify
  before adding another mechanism.
