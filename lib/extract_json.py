#!/usr/bin/env python3
"""Extract the best-effort JSON object from a reviewer CLI's stdout.

CLIs like `codex exec` and `gemini -p` return free text that may include
status messages, thinking sections, code fences, and the actual findings
JSON somewhere inside. This helper tries, in order:

  1. Parse the whole input as JSON (clean case).
  2. Find a ```json ... ``` fenced block and parse that.
  3. Find any ``` ... ``` fenced block and try to parse it as JSON.
  4. Find the widest substring from the first `{` to the last `}` and
     try to parse that.
  5. Fall back to emitting a synthetic empty-findings object with the
     reviewer name so the merge step can still proceed.

Usage:
  cat raw_output.txt | python3 extract_json.py <reviewer_name> [<mode>]

The reviewer name is injected into the JSON if the parsed object does
not already have a `reviewer` field, and the mode similarly.

Exit codes:
  0  successfully extracted non-empty JSON (pass 1-4)
  1  fell back to empty synthetic JSON (pass 5); something upstream is wrong
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

FENCE_JSON_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
FENCE_ANY_RE = re.compile(r"```[a-zA-Z]*\s*(.*?)\s*```", re.DOTALL)
BRACES_RE = re.compile(r"\{.*\}", re.DOTALL)


def try_parse(text: str) -> Any:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def is_findings_shape(obj: Any) -> bool:
    """Return True if obj looks like a reviewer payload we can merge."""
    return (
        isinstance(obj, dict)
        and "findings" in obj
        and isinstance(obj["findings"], list)
    )


def extract(text: str) -> tuple[Any, int]:
    """Return (parsed_json, pass_number). pass_number indicates strategy."""
    # Pass 1: whole input
    obj = try_parse(text)
    if is_findings_shape(obj):
        return obj, 1

    # Pass 2: ```json ... ``` fenced block
    for match in FENCE_JSON_RE.finditer(text):
        obj = try_parse(match.group(1))
        if is_findings_shape(obj):
            return obj, 2

    # Pass 3: any ``` ... ``` fenced block
    for match in FENCE_ANY_RE.finditer(text):
        obj = try_parse(match.group(1))
        if is_findings_shape(obj):
            return obj, 3

    # Pass 4: widest {...} span
    match = BRACES_RE.search(text)
    if match:
        obj = try_parse(match.group(0))
        if is_findings_shape(obj):
            return obj, 4

    # Pass 5: bare naked parse of widest brace span even if shape is off
    # (lets us salvage anything JSON-ish for debugging)
    if match:
        obj = try_parse(match.group(0))
        if isinstance(obj, dict):
            # Patch up missing findings array so downstream doesn't crash.
            obj.setdefault("findings", [])
            return obj, 4

    return None, 5


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: extract_json.py <reviewer_name> [<mode>]", file=sys.stderr)
        return 1

    reviewer = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) >= 3 else "unknown"

    text = sys.stdin.read()
    obj, pass_num = extract(text)

    if obj is None:
        # Nothing salvageable. Emit empty findings payload.
        obj = {"reviewer": reviewer, "mode": mode, "findings": []}
        sys.stderr.write(
            f"extract_json: WARNING — no JSON found in {reviewer} output "
            f"({len(text)} bytes), emitting empty findings\n"
        )
        json.dump(obj, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1

    # Inject reviewer / mode fields if missing or blank.
    if not obj.get("reviewer"):
        obj["reviewer"] = reviewer
    if not obj.get("mode"):
        obj["mode"] = mode

    sys.stderr.write(
        f"extract_json: {reviewer} extracted via pass {pass_num}, "
        f"{len(obj.get('findings', []))} findings\n"
    )
    json.dump(obj, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
