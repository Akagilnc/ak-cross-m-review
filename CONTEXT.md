# ak-cross-m-review domain language

- **fixed target** — the resolved user-supplied base SHA, resolved HEAD SHA,
  and one materialized full diff reused by every reviewer.
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
  `grok`, optional `claude`, or legacy `gemini`/`agy`.
- **actual family** — the vendor family of the model that really produced a
  review. It is transport evidence, never a caller-supplied label.
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
  retries, and later gates.
- **deletion outranks addition** — for equivalent behavior, remove or simplify
  before adding another mechanism.
