# ak-cross-m-review domain language

This file is vocabulary only. `SKILL.md` plus each selected lens prompt is the
complete active authority; Steps 1–5 define the procedure.

- **fixed target** — the pinned base-to-HEAD snapshot under review.
- **authority set** — the sources that govern the review.
- **lens selection** — correctness, completeness, or explicit ordered `all`;
  each panel pass still receives exactly one prompt under `prompts/`.
- **preset** — a named wrapper that selects one lens.
- **degraded member** — a selected reviewer whose transport failed (non-zero
  exit or empty stdout). Content shape never degrades a leg (ADR 0141).
- **present member** — exit 0 + non-empty raw stdout; pure prose is legal paper.
- **candidate** — an evidence-backed claim awaiting judgment.
- **judge** — the main session that adjudicates candidates.
- **lawful rejection** — an evidence-backed rejection defined by Step 5.
- **terminal verdict** — the result defined by Step 5.
- **review only** — run only the selected review sequence, report, and stop;
  never repair the target.

Panel, transport, scratch, adjudication, and termination definitions live only
in `SKILL.md` Steps 4–5 and each selected lens prompt.
