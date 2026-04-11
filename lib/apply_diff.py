#!/usr/bin/env python3
"""Safely apply a unified diff produced by the fixer to a target file.

Safety rails (in order):

  1. Parse the fixer JSON output from stdin; pull out the `diff` field.
  2. If `diff` is empty, print a notice and exit 0 (nothing to do).
  3. Write the diff to a temporary file.
  4. Run `git apply --check` to validate the diff applies cleanly. If it
     does not, print the error + the diff, and exit 2 without touching
     the target.
  5. Back up the target file to <target>.bak-<timestamp>.
  6. Run `git apply` to apply the diff.
  7. Print success summary + the list of `fixes_applied` from the fixer
     JSON so the user knows what changed.

Usage:
  python3 apply_diff.py <target_file> <fixer_output.json>
  python3 apply_diff.py --check-only <target_file> <fixer_output.json>

Exit codes:
  0  diff applied successfully OR diff was empty
  1  usage / parse error
  2  diff failed `git apply --check`
  3  `git apply` succeeded in check but failed in apply (rare)
  4  target file doesn't exist

This script intentionally does NOT commit the change, ask for confirmation,
or run tests. The orchestrator (SKILL.md or a human) is responsible for
those steps. This is a pure "apply if it applies cleanly" helper.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


HUNK_HEADER_RE = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$"
)


def normalize_diff_hunks(diff_text: str) -> str:
    """Recount each hunk's old/new line totals and rewrite its header.

    LLM-generated diffs frequently get hunk sizes wrong when a single hunk
    contains multiple edits close together — the model correctly merges
    the edits into one hunk but forgets that the declared `-X,N +Y,M`
    counts must include every line (context + additions + deletions).

    This is a pure re-counting pass: it does NOT change any content, just
    updates the four numbers in each `@@` header to match what the hunk
    body actually contains. If the diff has no hunks or the headers are
    unparseable, the input is returned unchanged.
    """
    lines = diff_text.splitlines(keepends=False)
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = HUNK_HEADER_RE.match(line)
        if not m:
            out.append(line)
            i += 1
            continue

        old_start = int(m.group(1))
        new_start = int(m.group(3))
        trailing = m.group(5) or ""

        # Collect hunk body until the next @@ header, ---, or end of input.
        body_start = i + 1
        body_end = body_start
        minus_count = 0
        plus_count = 0
        context_count = 0
        while body_end < len(lines):
            bl = lines[body_end]
            if HUNK_HEADER_RE.match(bl):
                break
            if bl.startswith("---") or bl.startswith("+++"):
                break
            if bl.startswith("-"):
                minus_count += 1
            elif bl.startswith("+"):
                plus_count += 1
            else:
                context_count += 1
            body_end += 1

        old_total = minus_count + context_count
        new_total = plus_count + context_count
        new_header = f"@@ -{old_start},{old_total} +{new_start},{new_total} @@{trailing}"
        out.append(new_header)
        out.extend(lines[body_start:body_end])
        i = body_end

    # Preserve trailing newline if the input had one.
    result = "\n".join(out)
    if diff_text.endswith("\n"):
        result += "\n"
    return result


def load_fixer_json(path: str) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: could not read fixer JSON at {path}: {e}", file=sys.stderr)
        sys.exit(1)


def write_diff_to_temp(diff: str) -> Path:
    fd, path = tempfile.mkstemp(prefix="grounded-review-diff-", suffix=".patch")
    with open(fd, "w", encoding="utf-8") as f:
        f.write(diff)
        if not diff.endswith("\n"):
            f.write("\n")
    return Path(path)


def run_git_apply(diff_path: Path, target_file: Path, check_only: bool) -> tuple[int, str, str]:
    """Run `git apply [--check] <diff>` in the target's parent directory.

    Returns (returncode, stdout, stderr).
    """
    cmd = ["git", "apply"]
    if check_only:
        cmd.append("--check")
    cmd.append(str(diff_path))

    result = subprocess.run(
        cmd,
        cwd=target_file.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def backup_target(target: Path) -> Path:
    """Create a timestamped backup next to the target file."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = target.with_suffix(target.suffix + f".bak-{ts}")
    shutil.copy2(target, backup)
    return backup


def print_fix_summary(fixer: dict[str, Any]) -> None:
    applied = fixer.get("fixes_applied", [])
    skipped = fixer.get("fixes_skipped", [])
    confidence = fixer.get("confidence", "unknown")
    notes = fixer.get("notes", "")

    print(f"\n{'=' * 60}")
    print(f"  Fixer confidence: {confidence}")
    print(f"  Applied fixes: {len(applied)}")
    print(f"  Skipped fixes: {len(skipped)}")
    print(f"{'=' * 60}\n")

    if applied:
        print("APPLIED:")
        for fix in applied:
            mid = fix.get("merged_id", "?")
            cat = fix.get("finding_category", "?")
            summary = fix.get("edit_summary", "")
            print(f"  ✓ {mid:<6} [{cat}] {summary}")
        print()

    if skipped:
        print("SKIPPED:")
        for fix in skipped:
            mid = fix.get("merged_id", "?")
            reason = fix.get("reason", "(no reason given)")
            details = fix.get("details", "")
            print(f"  ⊘ {mid:<6} {reason}")
            if details:
                print(f"          details: {details}")
        print()

    if notes:
        print(f"NOTES: {notes}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely apply a unified diff from fixer output"
    )
    parser.add_argument("target", help="Path to target file")
    parser.add_argument("fixer_json", help="Path to fixer output JSON")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate diff applies cleanly but do not actually apply it",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a .bak-<timestamp> backup of the target",
    )
    args = parser.parse_args()

    target = Path(args.target)
    if not target.is_file():
        print(f"error: target file not found: {target}", file=sys.stderr)
        return 4

    fixer = load_fixer_json(args.fixer_json)
    diff = fixer.get("diff", "")

    if not diff.strip():
        print("apply_diff: fixer produced empty diff, nothing to apply")
        print_fix_summary(fixer)
        return 0

    # Pre-flight: normalize hunk headers so LLM-produced count errors do
    # not trip git apply --check. This is a pure re-counting pass, not a
    # content change.
    normalized_diff = normalize_diff_hunks(diff)
    if normalized_diff != diff:
        print("apply_diff: normalized diff hunk headers (LLM miscounted line totals)")

    diff_file = write_diff_to_temp(normalized_diff)
    print(f"apply_diff: wrote diff to {diff_file} ({len(normalized_diff)} bytes)")

    try:
        # --- Stage 1: check ---
        rc, out, err = run_git_apply(diff_file, target, check_only=True)
        if rc != 0:
            print(
                f"apply_diff: ✗ `git apply --check` FAILED (exit {rc})",
                file=sys.stderr,
            )
            if out:
                print(f"  stdout: {out}", file=sys.stderr)
            if err:
                print(f"  stderr: {err}", file=sys.stderr)
            print("\n--- diff content (for manual inspection) ---", file=sys.stderr)
            print(diff, file=sys.stderr)
            print("--- end diff ---", file=sys.stderr)
            return 2

        print("apply_diff: ✓ `git apply --check` OK")

        if args.check_only:
            print("apply_diff: --check-only mode, not applying")
            print_fix_summary(fixer)
            return 0

        # --- Stage 2: backup ---
        if not args.no_backup:
            backup = backup_target(target)
            print(f"apply_diff: backed up target to {backup}")

        # --- Stage 3: apply ---
        rc, out, err = run_git_apply(diff_file, target, check_only=False)
        if rc != 0:
            print(
                f"apply_diff: ✗ `git apply` FAILED after check passed "
                f"(exit {rc}) — this is unusual",
                file=sys.stderr,
            )
            if out:
                print(f"  stdout: {out}", file=sys.stderr)
            if err:
                print(f"  stderr: {err}", file=sys.stderr)
            return 3

        print("apply_diff: ✓ applied successfully")
        print_fix_summary(fixer)
        return 0

    finally:
        # Clean up temp diff file
        try:
            diff_file.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
