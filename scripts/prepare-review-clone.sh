#!/usr/bin/env bash
# Prepare one independent writable clone for a reviewer.
#
# Usage: prepare-review-clone.sh REPO_ROOT LEG_ROOT PRE_HEAD BASE_SHA
# Prints the canonical LEG_ROOT only after every isolation check passes.
# Failed clones are deliberately preserved for diagnosis.

set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "prepare-review-clone: usage: $0 REPO_ROOT LEG_ROOT PRE_HEAD BASE_SHA" >&2
  exit 2
fi

REPO_ARG="$1"
LEG_ARG="$2"
PRE_HEAD="$3"
BASE_SHA="$4"

fail() {
  echo "prepare-review-clone: $*" >&2
  exit 1
}

has_hidden_component() {
  local path="${1#/}"
  local component
  local components=()
  IFS=/ read -r -a components <<< "$path"
  for component in "${components[@]}"; do
    case "$component" in
      .*) return 0 ;;
    esac
  done
  return 1
}

REPO_ROOT="$(cd "$REPO_ARG" && pwd -P)" || fail "cannot resolve source repository"
LEG_PARENT="$(cd "$(dirname "$LEG_ARG")" && pwd -P)" \
  || fail "cannot resolve reviewer clone parent"
LEG_CANDIDATE="$LEG_PARENT/$(basename "$LEG_ARG")"
if [ -e "$LEG_ARG" ]; then
  LEG_CANDIDATE="$(cd "$LEG_ARG" && pwd -P)" \
    || fail "cannot resolve reviewer clone path"
fi
case "$LEG_CANDIDATE" in
  "$REPO_ROOT"|"$REPO_ROOT"/*)
    fail "reviewer clone path must be outside source repository"
    ;;
esac

git clone --origin origin --no-local --no-checkout "$REPO_ROOT" "$LEG_ARG"
git -C "$LEG_ARG" checkout --detach "$PRE_HEAD"
git -C "$LEG_ARG" remote remove origin

LEG_ROOT="$(cd "$LEG_ARG" && pwd -P)" || fail "cannot resolve reviewer clone"
COMMON_DIR="$(git -C "$LEG_ROOT" rev-parse --path-format=absolute --git-common-dir)"
COMMON_DIR="$(cd "$COMMON_DIR" && pwd -P)" || fail "cannot resolve reviewer git directory"

case "$COMMON_DIR" in
  "$LEG_ROOT"/*) ;;
  *) fail "git common directory escapes reviewer clone" ;;
esac

ACTUAL_HEAD="$(git -C "$LEG_ROOT" rev-parse HEAD)"
[ "$ACTUAL_HEAD" = "$PRE_HEAD" ] || fail "reviewer clone HEAD does not match pinned HEAD"
git -C "$LEG_ROOT" cat-file -e "${BASE_SHA}^{commit}" || fail "base commit is not reachable in reviewer clone"
has_hidden_component "$LEG_ROOT" && fail "reviewer clone path contains a hidden component"

STATUS="$(git -C "$LEG_ROOT" status --porcelain=v1 --untracked-files=all)"
[ -z "$STATUS" ] || fail "reviewer clone is not clean"
REMOTES="$(git -C "$LEG_ROOT" remote)"
[ -z "$REMOTES" ] || fail "reviewer clone still has a remote"

printf '%s\n' "$LEG_ROOT"
