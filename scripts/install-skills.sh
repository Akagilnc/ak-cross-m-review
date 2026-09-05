#!/usr/bin/env bash
# Install the cross-model-review skills into ~/.claude/skills/.
#
# Three skills ship from this one repo:
#   - ak-cross-m-review      (engine; repo root) — already symlinked in most
#                             setups; this script (re)links it too.
#   - ak-cmr-completeness    (completeness preset; skills/ak-cmr-completeness/)
#   - ak-cmr-correctness     (correctness preset; skills/ak-cmr-correctness/)
#
# Claude Code discovers a skill as `~/.claude/skills/<name>/SKILL.md`, one
# level deep — so each skill needs its OWN entry there. The two presets invoke
# the engine once with `--lens`; their names make the completeness versus
# correctness choice explicit.
#
# Idempotent: re-running just refreshes the symlinks. Safe to run after a
# `git pull`.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$SKILLS_DIR"
failures=0

link() {
  local name="$1" target="$2" destination="$SKILLS_DIR/$1"
  if [ ! -d "$target" ] || [ ! -f "$target/SKILL.md" ]; then
    echo "install-skills: skip $name — no SKILL.md at $target" >&2
    failures=$((failures + 1))
    return 0
  fi
  if [ -e "$destination" ] && [ ! -L "$destination" ]; then
    echo "install-skills: refuse $destination — destination exists and is not a symlink" >&2
    failures=$((failures + 1))
    return 0
  fi
  ln -sfn "$target" "$destination"
  echo "  ✓ $destination -> $target"
}

echo "Installing cross-model-review skills into $SKILLS_DIR:"
link "ak-cross-m-review" "$REPO_ROOT"
link "ak-cmr-completeness"  "$REPO_ROOT/skills/ak-cmr-completeness"
link "ak-cmr-correctness"   "$REPO_ROOT/skills/ak-cmr-correctness"
if [ "$failures" -ne 0 ]; then
  echo "install-skills: failed — $failures skill(s) not installed" >&2
  exit 1
fi
echo "Done. Restart / re-scan skills if your client caches the list."
