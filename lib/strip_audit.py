#!/usr/bin/env python3
"""Strip the post-approval audit section from a design doc to produce an
"as-if-before-audit" fixture for recall evaluation.

A doc that has been audited looks like:

    # Design: Foo
    ...body content including original (possibly hallucinated) claims...
    ## Post-Approval Hallucination Audit
    ...findings H1, H2, ... that are the ground truth...

The audit section is pure append — the body is NOT in-place corrected. Removing
everything from the audit header onward produces a fixture that contains the
original hallucinations exactly as they shipped, which is what we want to feed
the reviewer during evaluation.

Usage:
    python3 strip_audit.py <input.md>                 # stdout
    python3 strip_audit.py <input.md> <output.md>     # write to file

Exit codes:
    0  success
    2  input file not found
    3  no audit section found (nothing to strip; caller should decide if
       that is an error — this script treats it as a soft warning on stderr
       and outputs the full input unchanged with exit code 3)
"""

import sys
from pathlib import Path

AUDIT_HEADER_PREFIX = "## Post-Approval Hallucination Audit"


def strip_audit(content: str) -> tuple[str, bool]:
    """Return (stripped_content, found_audit_header).

    If the audit header is not found, returns the original content unchanged
    and found_audit_header=False so the caller can decide.
    """
    lines = content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith(AUDIT_HEADER_PREFIX):
            return "".join(lines[:i]), True
    return content, False


def main() -> int:
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("usage: strip_audit.py <input.md> [<output.md>]", file=sys.stderr)
        return 1

    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2

    content = input_path.read_text(encoding="utf-8")
    stripped, found = strip_audit(content)

    if not found:
        print(
            f"warning: no '{AUDIT_HEADER_PREFIX}' section found in {input_path}; "
            "outputting full input unchanged",
            file=sys.stderr,
        )

    if len(sys.argv) == 3:
        output_path = Path(sys.argv[2])
        output_path.write_text(stripped, encoding="utf-8")
    else:
        sys.stdout.write(stripped)

    return 0 if found else 3


if __name__ == "__main__":
    sys.exit(main())
