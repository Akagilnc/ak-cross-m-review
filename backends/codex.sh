#!/usr/bin/env bash
# OpenAI Codex reviewer backend.
#
# Invocation:
#   <stdin: full dispatch prompt including task prompt + target content + any
#           source-repo hint> | backends/codex.sh <mode> [<workdir>]
#
# Outputs JSON (reviewer payload) to stdout. Diagnostics to stderr.
#
# Uses `codex exec -s read-only` for a sandboxed, read-only run. Optional
# workdir arg sets the codex working directory, which controls where
# codex's built-in Read / Bash tools resolve relative paths. Default is
# the proto repo root.

set -euo pipefail

PROTO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-doc}"
WORKDIR="${2:-$PROTO_ROOT}"

FULL_PROMPT="$(cat)"

if [ -z "$FULL_PROMPT" ]; then
  echo "codex: error: empty prompt on stdin" >&2
  exit 1
fi

if [ ! -d "$WORKDIR" ]; then
  echo "codex: warn: workdir '$WORKDIR' not a directory, falling back to PROTO_ROOT" >&2
  WORKDIR="$PROTO_ROOT"
fi

# Codex exec with read-only sandbox. Pipe prompt via stdin argument.
RAW="$(
  codex exec "$FULL_PROMPT" -C "$WORKDIR" -s read-only 2>/dev/null || true
)"

if [ -z "$RAW" ]; then
  echo "codex: error: codex CLI returned empty output" >&2
  printf '{"reviewer":"codex","mode":"%s","findings":[]}\n' "$MODE"
  exit 1
fi

printf '%s' "$RAW" | python3 "$PROTO_ROOT/lib/extract_json.py" codex "$MODE"
