---
name: grounded-review
description: Multi-reviewer grounded fact-check of a design doc or code file with iterative fixer loop. Dispatches 3 independent reviewers (Claude Opus headless, Codex, Gemini) in parallel, merges findings with consensus-based severity upgrade, and proposes a unified diff per round for user approval. Use when you need to catch hallucinations, wrong file paths, fake CLI flags, or fabricated math in a markdown doc or TypeScript / Python / JS file.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
  - TodoWrite
---

# /grounded-review — Multi-Reviewer Grounded Fact-Check

You are running the `/grounded-review` skill. It dispatches three
independent reviewer backends in parallel against a target file, merges
their findings with deterministic severity upgrade on consensus, proposes
a unified diff via a fixer pass, asks the user to approve the diff, and
loops until findings converge or a round budget is hit.

This skill lives at `~/WorkSpace/gstack-grounded-review-proto/` (symlinked
into `~/.claude/skills/grounded-review/`). Cross-reference the README.md
in the repo for architecture and limitations.

---

## Step 0: Parse arguments and check binaries

The user invokes:

```
/grounded-review <target_path> [--mode doc|code|auto] [--rounds N] [--source-repo PATH]
```

- `target_path` — required. Path to a markdown, TypeScript, Python, or
  other source file to review.
- `--mode` — default `auto`. If `auto`, detect from file extension
  (`.md`/`.markdown` → `doc`, everything else → `code`).
- `--rounds` — default `3`. Max number of reviewer-fixer iterations.
- `--source-repo` — optional. Absolute path to a git repo whose source
  code the target references. This is prepended to the reviewer prompts
  as a hint so backends know where to grep. If omitted, backends use
  their own working directory and rely on `Read`/`Grep` with absolute
  paths embedded in the doc.

Parse the arguments and derive:

- `TARGET` — absolute path to the target file
- `MODE` — `doc` or `code`
- `ROUNDS` — integer, max rounds
- `SOURCE_REPO` — absolute path or empty

Run this bash to check binaries and compute paths:

```bash
PROTO_ROOT="$HOME/WorkSpace/gstack-grounded-review-proto"
cd "$PROTO_ROOT"

for bin in claude codex gemini python3 jq; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "error: required binary '$bin' not found in PATH" >&2
    exit 2
  fi
done
echo "env check: all binaries present"
```

If any binary is missing, stop and tell the user: "The
grounded-review skill requires `claude`, `codex`, `gemini`, `python3`, and
`jq`. Install the missing tool(s) and try again."

---

## Step 1: Resolve mode and source-repo hint

```bash
TARGET="<from user>"
MODE="<from user or auto>"

# Auto-detect mode from extension if needed
if [ "$MODE" = "auto" ] || [ -z "$MODE" ]; then
  case "$TARGET" in
    *.md|*.markdown) MODE=doc ;;
    *)               MODE=code ;;
  esac
fi
echo "mode: $MODE"
echo "target: $TARGET"
```

If `SOURCE_REPO` was provided, prepare a hint paragraph:

```
> Source-repo hint for verification: the target document references code
> in `<SOURCE_REPO>`. When verifying file paths, function names, module
> claims, or API signatures, grep / read that directory. Use `python3`
> or first-party docs for math and external packages as usual.
```

Compose the full dispatch prompt for this mode:

```bash
PROMPT_FILE="$PROTO_ROOT/prompts/reviewer-$MODE.md"
DISPATCH_PROMPT="$(
  cat "$PROMPT_FILE"
  echo
  if [ -n "$SOURCE_REPO" ]; then
    echo "> Source-repo hint: grep ${SOURCE_REPO} for path/function/module verification."
    echo
  fi
  echo "--- BEGIN TARGET FILE: $TARGET ---"
  echo
  cat "$TARGET"
  echo
  echo "--- END TARGET FILE ---"
  echo
  echo "Return JSON only. No markdown wrapper."
)"
```

Create the run directory:

```bash
RUN_ID="run-$(date +%Y%m%d-%H%M%S)"
RUN_DIR="$PROTO_ROOT/outputs/$RUN_ID"
mkdir -p "$RUN_DIR"
echo "run dir: $RUN_DIR"
```

---

## Step 2: Round loop

Use TodoWrite to track rounds as todos so the user can see progress.
Initialize the todo list with N round entries.

For each round from 1 to ROUNDS:

### Step 2a: Dispatch 3 reviewers in parallel

Create the round directory and dispatch. **Use three parallel tool calls
in a single message** (1 Agent + 2 Bash) so the reviewers run
concurrently.

```bash
ROUND_DIR="$RUN_DIR/round-$N"
mkdir -p "$ROUND_DIR"
```

Parallel dispatch (three independent tool calls, no dependencies
between them):

Tool call 1 — Claude Opus via **Agent tool** (subagent):

```
Agent tool call:
  description: "claude reviewer round N"
  model: opus
  prompt: |
    {DISPATCH_PROMPT}

    Return JSON only. No markdown wrapper.
```

After the subagent returns, extract its JSON response:

```bash
# Write subagent response to a temp file for extraction.
# Replace {SUBAGENT_RESPONSE} with the actual text returned by the
# Agent tool call above.
cat > "$ROUND_DIR/claude.raw" << 'REVIEWER_EOF'
{SUBAGENT_RESPONSE}
REVIEWER_EOF

python3 "$PROTO_ROOT/lib/extract_json.py" claude "$MODE" \
  < "$ROUND_DIR/claude.raw" \
  > "$ROUND_DIR/claude.json"
```

Tool call 2 — Codex (Bash, unchanged):
```bash
printf '%s' "$DISPATCH_PROMPT" \
  | "$PROTO_ROOT/backends/codex.sh" "$MODE" "${SOURCE_REPO:-$(dirname "$TARGET")}" \
  > "$ROUND_DIR/codex.json" \
  2> "$ROUND_DIR/codex.err"
```

Tool call 3 — Gemini (Bash, unchanged):
```bash
printf '%s' "$DISPATCH_PROMPT" \
  | "$PROTO_ROOT/backends/gemini.sh" "$MODE" \
  > "$ROUND_DIR/gemini.json" \
  2> "$ROUND_DIR/gemini.err"
```

Wait for all three to complete (tool results return). Report which
succeeded and which failed.

### Step 2b: Merge findings

```bash
python3 "$PROTO_ROOT/lib/merge.py" \
  "$ROUND_DIR/claude.json" \
  "$ROUND_DIR/codex.json" \
  "$ROUND_DIR/gemini.json" \
  > "$ROUND_DIR/merged.json"

jq -r '"merged: \(.merged_findings | length) findings (\(.stats.by_severity))"' \
  "$ROUND_DIR/merged.json"
```

### Step 2c: Present merged findings to the user

Read `$ROUND_DIR/merged.json` and format a concise summary. Show:

- Total findings count
- Breakdown by severity (critical / high / medium / low / clarity)
- For each critical/high finding: show `merged_id`, `category`,
  reviewer consensus count, and the first `claim_quote` from the
  `by_reviewer` field
- For medium/low: just show count, don't enumerate

Keep it under 30 lines of display per round. Full details live in
`$ROUND_DIR/merged.json` for the user to inspect.

### Step 2d: Termination check

```bash
CRIT_HIGH_COUNT=$(
  jq '[.merged_findings[] | select(.severity == "critical" or .severity == "high")] | length' \
    "$ROUND_DIR/merged.json"
)
echo "critical+high count: $CRIT_HIGH_COUNT"
```

If `CRIT_HIGH_COUNT == 0`:
  - Report "round $N: no critical/high findings remaining — CONVERGED"
  - Break out of the round loop

If this is the final round (`N == ROUNDS`):
  - Report "round $N: round budget reached, not looping further"
  - Break out of the round loop

Otherwise proceed to fixer.

### Step 2e: Fixer pass (proposes unified diff)

Compose the fixer prompt parts via Bash, then dispatch via Agent tool
(subagent). The subagent runs in-process so tool calls (Read, Grep for
concept sweep) are fast — no per-call API round-trip overhead.

```bash
MERGED_JSON="$(cat "$ROUND_DIR/merged.json")"
TARGET_CONTENT="$(cat "$TARGET")"
FIXER_PROMPT_TEMPLATE="$(cat "$PROTO_ROOT/prompts/fixer.md")"

# Determine fixer model (default sonnet, override with env var)
FIXER_MODEL="${GROUNDED_REVIEW_FIXER_MODEL:-sonnet}"
echo "fixer: model=$FIXER_MODEL round=$N"
echo "FIXER_PROMPT_TEMPLATE length: ${#FIXER_PROMPT_TEMPLATE}"
echo "MERGED_JSON length: ${#MERGED_JSON}"
echo "TARGET_CONTENT length: ${#TARGET_CONTENT}"
```

Now dispatch the fixer as a **subagent** using the Agent tool. Use the
Bash outputs above to compose the prompt parameter inline:

```
Agent tool call:
  description: "fixer round N"
  model: $FIXER_MODEL (from the bash output above — "sonnet" or "opus")
  prompt: |
    {FIXER_PROMPT_TEMPLATE}

    --- BEGIN MERGED FINDINGS ---
    {MERGED_JSON}
    --- END MERGED FINDINGS ---

    --- BEGIN TARGET FILE: {TARGET} ---
    {TARGET_CONTENT}
    --- END TARGET FILE ---

    Return JSON only. No markdown wrapper.
```

The subagent will use Read and Grep tools to verify claim_quote
locations and sweep for related occurrences (concept sweep). It returns
its response as text.

After the subagent returns, extract the JSON and write it to the round
directory:

```bash
# Write subagent response to a temp file for extraction.
# Replace {SUBAGENT_RESPONSE} with the actual text returned by the
# Agent tool call above.
cat > "$ROUND_DIR/fixer.raw" << 'FIXER_EOF'
{SUBAGENT_RESPONSE}
FIXER_EOF

# Extract JSON using the same pipeline as headless backend
python3 "$PROTO_ROOT/lib/extract_json.py" claude "$MODE" \
  < "$ROUND_DIR/fixer.raw" \
  > "$ROUND_DIR/fixer.json"

echo "fixer output: $(jq -r '"fixes_applied=\(.fixes_applied | length) fixes_skipped=\(.fixes_skipped | length) confidence=\(.confidence)"' "$ROUND_DIR/fixer.json")"
```

If the subagent fails or returns empty, treat it the same as a headless
failure: write an empty fixer payload and report the error to the user.

### Step 2f: Check proposed diff

```bash
python3 "$PROTO_ROOT/lib/apply_diff.py" --check-only "$TARGET" "$ROUND_DIR/fixer.json"
CHECK_EXIT=$?
```

If `CHECK_EXIT != 0`:
  - The fixer's diff doesn't apply cleanly. Show the raw diff to the
    user, explain the check failed, ask whether to continue (skip
    fixer this round, rerun reviewers next round) or stop.

### Step 2g: Ask user to approve the diff

Use AskUserQuestion. Show the user:
- Number of fixes_applied and fixes_skipped from `$ROUND_DIR/fixer.json`
- The diff content (read from `$ROUND_DIR/fixer.json` `.diff` field)

Options:
- A) Apply the diff and continue to round N+1
- B) Skip applying (keep findings, continue to round N+1 anyway — will
  re-review the same content)
- C) Stop the loop here, leave target unchanged

### Step 2h: Apply if approved

If the user chose A:

```bash
python3 "$PROTO_ROOT/lib/apply_diff.py" "$TARGET" "$ROUND_DIR/fixer.json"
echo "applied; backup at $TARGET.bak-*"
```

If the user chose B: do nothing, continue.

If the user chose C: break the round loop.

---

## Step 3: Final report

After the loop exits (convergence, budget, or user stop), print a
compact report:

- Total rounds run
- Total fixes applied across rounds (sum of fixes_applied counts)
- Remaining critical+high count from the final merged.json
- Path to the run directory so the user can inspect round-by-round
  artifacts

Example:

```
GROUNDED REVIEW COMPLETE
========================
run:            run-20260411-231500
rounds:         2 / 3
outcome:        converged (no critical/high remaining)
fixes applied:  7 across 2 rounds
artifacts:      ~/WorkSpace/gstack-grounded-review-proto/outputs/run-20260411-231500/
```

If the loop ended with unresolved critical/high findings (budget
reached or user stopped), clearly flag that the target file still has
known issues.

---

## Error / edge case handling

- **Target file not found**: stop immediately, clear error message.
- **All three backends fail on the same round**: stop with "all
  reviewers failed", show the contents of `*.err` files.
- **One or two backends fail**: continue with reduced reviewer count,
  merge will produce a 2-way or 1-way merge. Severity upgrade still
  works (just caps earlier). Log the failure in the final report.
- **Fixer produces invalid JSON**: stop with a clear error and show
  the raw output. User can decide whether to retry or abandon.
- **Fixer produces a diff that fails `git apply --check`**: present the
  raw diff to the user and ask them to fix manually, then offer to
  continue the loop or stop.
- **User interrupts mid-round**: safe — no partial state is
  committed. Backup files in the target's directory can be cleaned up
  manually.

---

## Non-goals

This skill does NOT:
- Run tests after applying a diff (user does that or adds it to their
  own workflow)
- Commit anything to git (by design — the prototype does not touch
  git state of the target repo)
- Write the findings back into the target doc as a `## Grounded Review`
  section (that is a v1 feature; for now findings live in the outputs/
  directory only)
- Re-run failed reviewers automatically (they return empty findings on
  failure and the round proceeds with reduced count)
- Handle multiple target files at once (one invocation per target)

---

## Invocation examples

```
/grounded-review ~/.gstack/projects/foo/design-20260411.md
/grounded-review ~/.gstack/projects/foo/design-20260411.md --mode doc --rounds 2
/grounded-review src/billing.ts --mode code --rounds 1
/grounded-review eval/session5_fixture.md --mode doc --source-repo ~/WorkSpace/ai-blogger-lab
```
