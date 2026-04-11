#!/usr/bin/env python3
"""Merge findings from multiple reviewer backends with deterministic severity
upgrade on consensus.

Input: one or more JSON files, each shaped like:
  {
    "reviewer": "claude|codex|gemini",
    "mode": "doc|code",
    "findings": [
      {
        "id": "R1",
        "severity": "critical|high|medium|low|clarity",
        "category": "...",
        "claim_quote": "...",
        "location": "...",
        "verification": "...",
        "suggested_fix": "..."
      },
      ...
    ]
  }

Output: one merged JSON to stdout shaped like:
  {
    "mode": "doc|code",
    "reviewers": ["claude", "codex", "gemini"],
    "merged_findings": [
      {
        "merged_id": "M1",
        "severity": "<post-upgrade>",
        "original_severities": {"claude": "high", "codex": "high"},
        "reviewers": ["claude", "codex"],
        "category": "...",
        "by_reviewer": {
          "claude": {"claim_quote": "...", "location": "...", ...},
          "codex":  {"claim_quote": "...", "location": "...", ...}
        }
      },
      ...
    ],
    "stats": {...}
  }

Severity upgrade rule (upgrade only, never downgrade):
  - 3 reviewers agree on a finding → severity = critical
  - 2 reviewers agree → severity = max(high, original_max)
  - 1 reviewer only → severity = original

"Agreement" = fuzzy match: same category AND ≥2 shared meaningful keywords
between any combination of {claim_quote, location, verification}.

Usage:
  python3 merge.py outputs/round-1/claude.json outputs/round-1/codex.json outputs/round-1/gemini.json
  python3 merge.py --selftest    # run built-in unit tests and exit
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SEVERITY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "clarity": 0,
}

STOPWORDS = {
    "the", "is", "a", "an", "of", "to", "and", "or", "in", "on", "for", "with",
    "that", "this", "it", "its", "be", "are", "was", "were", "has", "have",
    "not", "no", "but", "as", "at", "by", "from", "if", "so", "than", "then",
    "also", "only", "very", "just", "can", "will", "should", "would", "could",
    "which", "what", "when", "where", "who", "how", "all", "any", "some",
    "both", "each", "here", "there", "now", "been", "does", "did", "do", "done",
    "doc", "docs", "claim", "claims", "claimed", "reality", "actual", "section",
    "line", "lines", "file", "files", "code", "says", "said",
}

WORD_RE = re.compile(r"[a-zA-Z0-9_\-./]+")


def tokenize(s: str) -> set[str]:
    """Extract meaningful tokens from a string for fuzzy matching.

    Keeps alphanumeric tokens (including dots, slashes, dashes, underscores
    which matter for file paths and function names), lowercases them, drops
    stopwords, and drops tokens shorter than 3 characters.

    For path-shaped tokens (containing "/"), also emits the basename as a
    separate token so "src/workflow/run-tick.ts" matches "run-tick.ts".
    """
    if not s:
        return set()
    raw = {t.lower() for t in WORD_RE.findall(s)}
    expanded: set[str] = set()
    for t in raw:
        expanded.add(t)
        if "/" in t:
            basename = t.rsplit("/", 1)[-1]
            if basename:
                expanded.add(basename)
    return {t for t in expanded if len(t) >= 3 and t not in STOPWORDS}


def finding_tokens(f: dict[str, Any]) -> set[str]:
    """Collect fuzzy-match tokens from a single finding.

    Intentionally excludes the `verification` field. In code mode, every
    finding's verification starts with "Read <file>:<range>" which leaks
    file-path and procedure tokens into every pairwise comparison, letting
    unrelated findings jump the cross-category match threshold purely on
    review-log boilerplate. claim_quote + location is enough identity.
    """
    return (
        tokenize(f.get("claim_quote", ""))
        | tokenize(f.get("location", ""))
    )


def findings_match(a: dict[str, Any], b: dict[str, Any], min_shared: int = 2) -> bool:
    """Return True if two findings describe the same issue.

    Rule structure:
      - Same category → ≥1 shared meaningful token suffices. Rationale: the
        category does most of the work; a single shared identifier (file
        path, function name, specific value) confirms it is the same issue.
      - Different categories → need ≥(min_shared + 2) shared tokens. Strong
        token overlap can cross category disagreements because reviewers
        sometimes classify the same issue differently.
      - Missing category on either side → need ≥(min_shared + 1) shared
        tokens (middle ground).
    """
    a_cat = (a.get("category") or "").lower().strip()
    b_cat = (b.get("category") or "").lower().strip()
    shared = finding_tokens(a) & finding_tokens(b)

    if a_cat and b_cat:
        if a_cat == b_cat:
            return len(shared) >= 1
        return len(shared) >= min_shared + 2
    return len(shared) >= min_shared + 1


def upgrade_severity(original_severities: list[str], num_reviewers: int) -> str:
    """Apply the consensus upgrade rule.

    3+ reviewers → critical
    2 reviewers → at least high (but if original max was already critical, keep it)
    1 reviewer → original
    """
    if num_reviewers >= 3:
        return "critical"
    if num_reviewers == 2:
        max_original = max(
            (SEVERITY_RANK.get(s, 0) for s in original_severities),
            default=0,
        )
        if max_original >= SEVERITY_RANK["critical"]:
            return "critical"
        return "high"
    # Single reviewer — keep their original severity.
    if original_severities:
        return original_severities[0]
    return "clarity"


def merge_finding_groups(
    reviewer_payloads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collapse reviewer findings into merged groups.

    Greedy: take each finding in order, compare to existing groups, merge into
    the first matching group or create a new one. This is O(N*M) where N is
    total findings and M is number of groups. For prototype sizes (≤ 30
    findings) this is fine.
    """
    groups: list[dict[str, Any]] = []

    for payload in reviewer_payloads:
        reviewer = payload.get("reviewer", "unknown")
        for f in payload.get("findings", []):
            placed = False
            for g in groups:
                # Match against the canonical (first) finding of the group
                # ONLY. Matching against any finding would create transitive
                # chains that collapse unrelated issues into one group —
                # e.g., R1 ↔ R2 and R2 ↔ R3 does not mean R1 ↔ R3.
                canonical = g["_raw"][0]
                if findings_match(f, canonical):
                    g["_raw"].append(f)
                    g["_reviewers"].append(reviewer)
                    placed = True
                    break
            if not placed:
                groups.append({"_raw": [f], "_reviewers": [reviewer]})

    # Materialize final merged structure.
    merged = []
    for i, g in enumerate(groups, start=1):
        raws: list[dict[str, Any]] = g["_raw"]
        reviewers: list[str] = g["_reviewers"]

        # Deduplicate reviewer list while preserving order.
        seen: set[str] = set()
        unique_reviewers: list[str] = []
        for r in reviewers:
            if r not in seen:
                seen.add(r)
                unique_reviewers.append(r)

        original_severities = [r.get("severity", "low") for r in raws]
        final_severity = upgrade_severity(original_severities, len(unique_reviewers))

        # Use the first finding's category as the canonical one.
        category = raws[0].get("category", "unknown")

        # Preserve ALL findings from each reviewer in the group, not just
        # the first. Dropping later findings lost information needed by
        # downstream display and recall scoring (session 5 eval round 1:
        # 34→1 collapse hid post-decider finding that was reported but
        # never surfaced in by_reviewer).
        by_reviewer: dict[str, list[dict[str, Any]]] = {}
        for reviewer, raw in zip(reviewers, raws):
            by_reviewer.setdefault(reviewer, []).append({
                "severity": raw.get("severity"),
                "category": raw.get("category"),
                "claim_quote": raw.get("claim_quote"),
                "location": raw.get("location"),
                "verification": raw.get("verification"),
                "suggested_fix": raw.get("suggested_fix"),
            })

        merged.append({
            "merged_id": f"M{i}",
            "severity": final_severity,
            "original_severities": {
                r: raw.get("severity") for r, raw in zip(reviewers, raws)
            },
            "reviewers": unique_reviewers,
            "reviewer_count": len(unique_reviewers),
            "category": category,
            "by_reviewer": by_reviewer,
        })

    return merged


def compute_stats(
    reviewer_payloads: list[dict[str, Any]],
    merged: list[dict[str, Any]],
) -> dict[str, Any]:
    total_before = sum(len(p.get("findings", [])) for p in reviewer_payloads)
    by_severity: dict[str, int] = {}
    for m in merged:
        by_severity[m["severity"]] = by_severity.get(m["severity"], 0) + 1
    by_reviewer_count: dict[int, int] = {}
    for m in merged:
        c = m["reviewer_count"]
        by_reviewer_count[c] = by_reviewer_count.get(c, 0) + 1
    return {
        "total_findings_before_merge": total_before,
        "total_findings_after_merge": len(merged),
        "merge_compression_ratio": (
            round(total_before / len(merged), 2) if merged else 0
        ),
        "by_severity": by_severity,
        "by_reviewer_count": by_reviewer_count,
    }


def merge(reviewer_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    """Top-level merge entry point."""
    modes = {p.get("mode", "unknown") for p in reviewer_payloads}
    mode = modes.pop() if len(modes) == 1 else "mixed"
    reviewers = [p.get("reviewer", "unknown") for p in reviewer_payloads]

    merged = merge_finding_groups(reviewer_payloads)
    stats = compute_stats(reviewer_payloads, merged)

    return {
        "mode": mode,
        "reviewers": reviewers,
        "merged_findings": merged,
        "stats": stats,
    }


def load_reviewer_files(paths: list[str]) -> list[dict[str, Any]]:
    out = []
    for p in paths:
        path = Path(p)
        if not path.is_file():
            print(f"warning: reviewer file not found: {p}", file=sys.stderr)
            continue
        try:
            with path.open() as f:
                out.append(json.load(f))
        except json.JSONDecodeError as e:
            print(f"warning: invalid JSON in {p}: {e}", file=sys.stderr)
    return out


def selftest() -> int:
    """Built-in self-tests. Exit 0 on success, 1 on failure."""
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append(f"FAIL: {name}" + (f" ({detail})" if detail else ""))

    # Test 1a: tokenize basics — stopwords and short tokens dropped
    toks = tokenize("The function runSingleTick in src/cli.ts line 425")
    check("tokenize keeps runSingleTick lowercased",
          "runsingletick" in toks, f"got {sorted(toks)}")
    check("tokenize keeps full path", "src/cli.ts" in toks, f"got {sorted(toks)}")
    check("tokenize drops stopword 'the'", "the" not in toks, f"got {sorted(toks)}")
    check("tokenize drops 2-char 'in'", "in" not in toks, f"got {sorted(toks)}")
    check("tokenize keeps 3+ char number 425", "425" in toks, f"got {sorted(toks)}")

    # Test 1b: basename expansion for path-shaped tokens
    toks_path = tokenize("src/workflow/run-tick.ts")
    check("tokenize emits basename from path",
          "run-tick.ts" in toks_path, f"got {sorted(toks_path)}")
    check("tokenize also keeps full path",
          "src/workflow/run-tick.ts" in toks_path, f"got {sorted(toks_path)}")

    # Test 2: findings_match — same category + shared tokens
    f1 = {
        "category": "wrong-refactor-target",
        "claim_quote": "refactor run-tick.ts to accept personaId",
        "location": "Hour 0-8",
    }
    f2 = {
        "category": "wrong-refactor-target",
        "claim_quote": "run-tick.ts is already dependency-injected",
        "location": "src/workflow/run-tick.ts",
    }
    check("findings_match: same category + shared token matches", findings_match(f1, f2))

    # Test 3: findings_match — different category, weak overlap
    f3 = {
        "category": "math-error",
        "claim_quote": "Beta(1,21) = 0.143",
        "location": "L3 Algorithm",
    }
    f4 = {
        "category": "wrong-refactor-target",
        "claim_quote": "run-tick.ts refactor",
        "location": "Hour 0-8",
    }
    check("findings_match: no overlap means no match", not findings_match(f3, f4))

    # Test 4: severity upgrade
    check("upgrade: 3 reviewers → critical",
          upgrade_severity(["low", "medium", "high"], 3) == "critical")
    check("upgrade: 2 reviewers non-critical → high",
          upgrade_severity(["medium", "low"], 2) == "high")
    check("upgrade: 2 reviewers with critical stays critical",
          upgrade_severity(["critical", "medium"], 2) == "critical")
    check("upgrade: 1 reviewer keeps original",
          upgrade_severity(["medium"], 1) == "medium")

    # Test 5: end-to-end merge with synthetic data
    claude_payload = {
        "reviewer": "claude",
        "mode": "doc",
        "findings": [
            {
                "id": "R1",
                "severity": "high",
                "category": "wrong-refactor-target",
                "claim_quote": "run-tick.ts refactor target is wrong",
                "location": "Hour 0-8",
                "verification": "grep src/workflow/run-tick.ts shows DI already",
                "suggested_fix": "target cli.ts:runSingleTick instead",
            },
            {
                "id": "R2",
                "severity": "critical",
                "category": "wrong-math",
                "claim_quote": "Beta(1,21) upper CI = 0.143",
                "location": "L3 Algorithm L331",
                "verification": "scipy.stats.beta.ppf(0.975, 1, 21) = 0.1611",
                "suggested_fix": "use Beta(1,23) = 0.1482 as first pivot",
            },
        ],
    }
    codex_payload = {
        "reviewer": "codex",
        "mode": "doc",
        "findings": [
            {
                "id": "C1",
                "severity": "medium",
                "category": "wrong-refactor-target",
                "claim_quote": "refactor run-tick.ts is the wrong target",
                "location": "src/workflow/run-tick.ts",
                "verification": "run-tick.ts is DI; cli.ts has the wiring",
                "suggested_fix": "point refactor at cli.ts",
            },
            {
                "id": "C2",
                "severity": "low",
                "category": "stale-naming",
                "claim_quote": "x-editor-pass.ts uses session 4 prefix",
                "location": "Q4 L371",
                "verification": "session 5 dropped X platform",
                "suggested_fix": "rename to editor-pass-en.ts",
            },
        ],
    }
    gemini_payload = {
        "reviewer": "gemini",
        "mode": "doc",
        "findings": [
            {
                "id": "G1",
                "severity": "high",
                "category": "wrong-math",
                "claim_quote": "Beta quantile 0.143 is fabricated",
                "location": "L3 Algorithm",
                "verification": "recomputed with scipy, real value ~0.161",
                "suggested_fix": "correct all Beta numbers",
            },
        ],
    }

    result = merge([claude_payload, codex_payload, gemini_payload])
    merged = result["merged_findings"]

    check("merge: finding count after merge", len(merged) == 3,
          f"got {len(merged)} expected 3 (run-tick shared, Beta shared, x-editor alone)")

    def group_quote_contains(m: dict[str, Any], needle: str) -> bool:
        """Check any claim_quote across all reviewers (lists) for substring."""
        needle = needle.lower()
        for reviewer_list in m.get("by_reviewer", {}).values():
            entries = reviewer_list if isinstance(reviewer_list, list) else [reviewer_list]
            for entry in entries:
                if needle in (entry.get("claim_quote") or "").lower():
                    return True
        return False

    # Find the run-tick merged finding
    run_tick_group = next(
        (m for m in merged if group_quote_contains(m, "run-tick")),
        None,
    )
    check("merge: run-tick finding matched between claude+codex", run_tick_group is not None)
    if run_tick_group:
        check("merge: run-tick has 2 reviewers",
              run_tick_group["reviewer_count"] == 2,
              f"got {run_tick_group['reviewer_count']}")
        check("merge: run-tick upgraded to high",
              run_tick_group["severity"] == "high",
              f"got {run_tick_group['severity']}")

    # Find the Beta math merged finding
    beta_group = next(
        (m for m in merged if "beta" in m["category"].lower()
         or group_quote_contains(m, "beta")),
        None,
    )
    check("merge: Beta finding matched between claude+gemini", beta_group is not None)
    if beta_group:
        check("merge: Beta stays critical (had critical original)",
              beta_group["severity"] == "critical",
              f"got {beta_group['severity']}")

    # x-editor should be solo
    x_editor_group = next(
        (m for m in merged if group_quote_contains(m, "editor-pass")),
        None,
    )
    check("merge: x-editor solo finding preserved", x_editor_group is not None)
    if x_editor_group:
        check("merge: x-editor keeps original low severity",
              x_editor_group["severity"] == "low",
              f"got {x_editor_group['severity']}")

    # Report
    if failures:
        print(f"\n❌ {len(failures)} test(s) failed:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("✓ all self-tests passed")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("usage: merge.py <reviewer1.json> [<reviewer2.json> ...]", file=sys.stderr)
        print("       merge.py --selftest", file=sys.stderr)
        return 1
    if args[0] == "--selftest":
        return selftest()

    payloads = load_reviewer_files(args)
    if not payloads:
        print("error: no valid reviewer payloads loaded", file=sys.stderr)
        return 2

    result = merge(payloads)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
