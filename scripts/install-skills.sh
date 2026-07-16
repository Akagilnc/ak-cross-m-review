#!/usr/bin/env bash
# Install the cross-model-review skills into ~/.claude/skills/.
#
# Three skills ship from this one repo:
#   - ak-cross-m-review  (one-pass engine; repo root) — already symlinked in
#                         most setups; this script (re)links it too.
#   - ak-cmr-completeness    (the completeness gate; skills/ak-cmr-completeness/)
#   - ak-cmr-correctness     (the correctness  gate; skills/ak-cmr-correctness/)
#
# Claude Code discovers a skill as `~/.claude/skills/<name>/SKILL.md`, one
# level deep — so each skill needs its OWN entry there. The two gate skills
# are preset wrappers that invoke the engine once with `--lens`; keeping them
# as named entry points is what makes the completeness vs correctness choice
# explicit (the agent picks the skill that names what it means, instead of
# trusting a `--lens` flag it might forget or mis-set).
#
# Idempotent: re-running just refreshes the symlinks. Safe to run after a
# `git pull`.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$SKILLS_DIR"

link() {
  local name="$1" target="$2"
  if [ ! -d "$target" ] || [ ! -f "$target/SKILL.md" ]; then
    echo "install-skills: skip $name — no SKILL.md at $target" >&2
    return 1
  fi
  ln -sfn "$target" "$SKILLS_DIR/$name"
  echo "  ✓ $SKILLS_DIR/$name -> $target"
}

echo "Installing cross-model-review skills into $SKILLS_DIR:"
link "ak-cross-m-review" "$REPO_ROOT"
link "ak-cmr-completeness"  "$REPO_ROOT/skills/ak-cmr-completeness"
link "ak-cmr-correctness"   "$REPO_ROOT/skills/ak-cmr-correctness"
echo "Done. Restart / re-scan skills if your client caches the list."
