# ak-cross-m-review domain language

This file is vocabulary only. `SKILL.md` plus each selected lens prompt is the
complete active authority; Steps 1–5 define the procedure.

- **fixed target** — the pinned base-to-HEAD snapshot under review.
- **authority set** — the sources that govern the review.
- **lens selection** — correctness, completeness, or explicit ordered `all`;
  each panel pass still receives exactly one prompt under `prompts/`.
- **preset** — a named wrapper that selects one lens.
- **degraded member** — a selected reviewer that produced no usable review.
- **candidate** — an evidence-backed claim awaiting judgment.
- **judge** — the main session that adjudicates candidates.
- **lawful rejection** — an evidence-backed rejection defined by Step 5.
- **terminal verdict** — the result defined by Step 5.
- **review only** — run only the selected review sequence, report, and stop;
  never repair the target.

Panel, transport, scratch, adjudication, and termination definitions live only
in `SKILL.md` Steps 4–5 and each selected lens prompt.
