#!/usr/bin/env python3
"""Score a merged findings JSON against a ground-truth JSON.

Inputs:
  --merged <path>       merged.json from lib/merge.py
  --ground-truth <path> ground_truth.json (e.g. eval/ground_truth.json)

Behavior:
  - For each ground-truth finding (H1-HN), check whether any merged finding
    contains at least one of its keywords_any (case-insensitive substring
    search across claim_quote, location, verification, suggested_fix of every
    reviewer in the merged group). If yes, the ground-truth finding is "hit".
  - Recall = hits / total ground-truth findings
  - Precision = (merged findings that matched ≥1 ground-truth) / (total merged)
  - Print a table: H# → hit/miss + which merged finding matched
  - Exit 0 if recall >= target, else exit 1
  - Default target: 0.7 for doc mode

Usage:
  python3 score.py --merged outputs/round-1/merged.json --ground-truth eval/ground_truth.json
  python3 score.py --merged ... --ground-truth ... --target 0.5
  python3 score.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def finding_corpus(merged_finding: dict[str, Any]) -> str:
    """Concatenate all reviewer text fields into one lowercase haystack.

    by_reviewer is a dict of reviewer -> list of finding dicts (a single
    reviewer may have multiple findings merged into the same group).
    Back-compat: also accept the old shape where by_reviewer is a dict of
    reviewer -> single finding dict.
    """
    parts: list[str] = []
    for reviewer_data in merged_finding.get("by_reviewer", {}).values():
        # Normalize to a list of finding dicts.
        findings_list = (
            reviewer_data if isinstance(reviewer_data, list) else [reviewer_data]
        )
        for f in findings_list:
            if not isinstance(f, dict):
                continue
            for field in ("claim_quote", "location", "verification", "suggested_fix"):
                v = f.get(field) or ""
                parts.append(v)
    parts.append(merged_finding.get("category", "") or "")
    return " ".join(parts).lower()


def score(
    merged: dict[str, Any],
    ground_truth: dict[str, Any],
) -> dict[str, Any]:
    """Compute recall/precision of merged findings against ground truth."""
    gt_findings: list[dict[str, Any]] = ground_truth.get("findings", [])
    merged_findings: list[dict[str, Any]] = merged.get("merged_findings", [])

    # Pre-compute one corpus per merged finding for fast substring search.
    merged_corpora = [(m, finding_corpus(m)) for m in merged_findings]

    hits: list[dict[str, Any]] = []
    misses: list[dict[str, Any]] = []
    # Track which merged findings matched something.
    matched_merged_ids: set[str] = set()

    for gt in gt_findings:
        keywords = [k.lower() for k in gt.get("keywords_any", [])]
        if not keywords:
            continue
        hit_merged: list[str] = []
        for m, corpus in merged_corpora:
            if any(kw in corpus for kw in keywords):
                hit_merged.append(m["merged_id"])
                matched_merged_ids.add(m["merged_id"])
        if hit_merged:
            hits.append({
                "id": gt["id"],
                "severity": gt["severity"],
                "description": gt.get("description", "")[:120],
                "matched_merged": hit_merged,
            })
        else:
            misses.append({
                "id": gt["id"],
                "severity": gt["severity"],
                "description": gt.get("description", "")[:120],
                "keywords": keywords[:3],
            })

    total_gt = len(gt_findings)
    total_merged = len(merged_findings)
    recall = len(hits) / total_gt if total_gt else 0.0
    precision = (
        len(matched_merged_ids) / total_merged if total_merged else 0.0
    )

    return {
        "total_ground_truth": total_gt,
        "total_merged_findings": total_merged,
        "hits_count": len(hits),
        "misses_count": len(misses),
        "recall": round(recall, 3),
        "precision": round(precision, 3),
        "hits": hits,
        "misses": misses,
        "unmatched_merged_ids": sorted(
            set(m["merged_id"] for m in merged_findings) - matched_merged_ids
        ),
    }


def print_report(report: dict[str, Any], target: float) -> None:
    recall = report["recall"]
    precision = report["precision"]
    passed = recall >= target

    print("=" * 60)
    print(
        f"  Recall: {report['hits_count']}/{report['total_ground_truth']} "
        f"= {recall:.1%}  (target: {target:.0%})  "
        f"{'✓ PASS' if passed else '✗ FAIL'}"
    )
    print(
        f"  Precision: {report['total_merged_findings']} merged findings, "
        f"{report['total_merged_findings'] - len(report['unmatched_merged_ids'])} "
        f"attributed to ground truth = {precision:.1%}"
    )
    print("=" * 60)
    print()

    print("HITS (ground-truth findings caught by the pipeline):")
    for h in report["hits"]:
        matched = ", ".join(h["matched_merged"])
        print(f"  ✓ {h['id']:<4} [{h['severity']:<8}] {h['description']}")
        print(f"          matched by: {matched}")
    print()

    if report["misses"]:
        print("MISSES (ground-truth findings the pipeline failed to catch):")
        for m in report["misses"]:
            kws = ", ".join(m["keywords"])
            print(f"  ✗ {m['id']:<4} [{m['severity']:<8}] {m['description']}")
            print(f"          (expected keywords: {kws})")
        print()

    if report["unmatched_merged_ids"]:
        print(
            "UNMATCHED MERGED FINDINGS "
            "(false positives or H-labels we did not enumerate):"
        )
        for mid in report["unmatched_merged_ids"]:
            print(f"  ? {mid}")
        print()


# =========================================================================
# Self-test
# =========================================================================


def _mock_ground_truth() -> dict[str, Any]:
    """A 4-finding mini ground truth for eval harness self-test."""
    return {
        "fixture": "test.md",
        "findings_count": 4,
        "findings": [
            {
                "id": "H1",
                "severity": "critical",
                "category": "wrong-math",
                "keywords_any": ["Beta(1,21)", "0.1611"],
                "description": "fabricated Beta quantile",
            },
            {
                "id": "H2",
                "severity": "high",
                "category": "wrong-refactor",
                "keywords_any": ["run-tick.ts", "cli.ts"],
                "description": "wrong refactor target",
            },
            {
                "id": "H3",
                "severity": "medium",
                "category": "stale-naming",
                "keywords_any": ["x-editor-pass"],
                "description": "stale x-prefix filename",
            },
            {
                "id": "H4",
                "severity": "low",
                "category": "never-found",
                "keywords_any": ["totally-obscure-xyzzy-keyword"],
                "description": "a finding no reviewer catches",
            },
        ],
    }


def _mock_merged(
    catch_beta: bool = True,
    catch_run_tick: bool = True,
    catch_x_editor: bool = True,
    add_false_positive: bool = False,
) -> dict[str, Any]:
    """A merged.json synthetically composed to hit or miss specific items."""
    merged_findings: list[dict[str, Any]] = []

    if catch_beta:
        merged_findings.append({
            "merged_id": "M1",
            "severity": "critical",
            "reviewers": ["claude", "codex"],
            "reviewer_count": 2,
            "category": "wrong-math",
            "by_reviewer": {
                "claude": {
                    "claim_quote": "Beta(1,21) upper CI = 0.143 is fabricated",
                    "location": "L3 Algorithm L331",
                    "verification": "scipy.stats.beta.ppf(0.975, 1, 21) = 0.1611",
                    "suggested_fix": "replace with 0.1611 or Beta(1,23)",
                },
                "codex": {
                    "claim_quote": "Beta quantile fabricated",
                    "location": "L3 numbers section",
                    "verification": "scipy disagrees with claimed value",
                    "suggested_fix": "recompute all Beta numbers",
                },
            },
        })
    if catch_run_tick:
        merged_findings.append({
            "merged_id": "M2",
            "severity": "high",
            "reviewers": ["codex"],
            "reviewer_count": 1,
            "category": "wrong-refactor",
            "by_reviewer": {
                "codex": {
                    "claim_quote": "refactor target should be cli.ts not run-tick.ts",
                    "location": "Hour 0-8",
                    "verification": "grepped run-tick.ts, already DI'd",
                    "suggested_fix": "point refactor at cli.ts:runSingleTick",
                },
            },
        })
    if catch_x_editor:
        merged_findings.append({
            "merged_id": "M3",
            "severity": "low",
            "reviewers": ["claude"],
            "reviewer_count": 1,
            "category": "stale-naming",
            "by_reviewer": {
                "claude": {
                    "claim_quote": "x-editor-pass.ts name is stale",
                    "location": "Q4",
                    "verification": "session 5 dropped X platform",
                    "suggested_fix": "rename to editor-pass-en.ts",
                },
            },
        })
    if add_false_positive:
        merged_findings.append({
            "merged_id": "M99",
            "severity": "medium",
            "reviewers": ["gemini"],
            "reviewer_count": 1,
            "category": "false-positive",
            "by_reviewer": {
                "gemini": {
                    "claim_quote": "some random concern reviewer made up",
                    "location": "somewhere",
                    "verification": "none",
                    "suggested_fix": "ignore",
                },
            },
        })

    return {
        "mode": "doc",
        "reviewers": ["claude", "codex", "gemini"],
        "merged_findings": merged_findings,
        "stats": {},
    }


def selftest() -> int:
    """Verify the eval scoring math with synthetic mock data."""
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append(f"FAIL: {name}" + (f" ({detail})" if detail else ""))

    gt = _mock_ground_truth()

    # Case A: catch 3 of 4, no false positives → recall 0.75, precision 1.0
    merged_a = _mock_merged(
        catch_beta=True, catch_run_tick=True, catch_x_editor=True,
        add_false_positive=False,
    )
    report_a = score(merged_a, gt)
    check("case A recall is 3/4", report_a["recall"] == 0.75,
          f"got {report_a['recall']}")
    check("case A precision is 1.0 (no false positives)",
          report_a["precision"] == 1.0,
          f"got {report_a['precision']}")
    check("case A hit count is 3", report_a["hits_count"] == 3)
    check("case A miss count is 1", report_a["misses_count"] == 1)
    check("case A miss is H4 (the never-found one)",
          report_a["misses"][0]["id"] == "H4" if report_a["misses"] else False)

    # Case B: catch only the Beta one, with a false positive
    # → recall 0.25, precision 1/2 = 0.5
    merged_b = _mock_merged(
        catch_beta=True, catch_run_tick=False, catch_x_editor=False,
        add_false_positive=True,
    )
    report_b = score(merged_b, gt)
    check("case B recall is 1/4 = 0.25", report_b["recall"] == 0.25,
          f"got {report_b['recall']}")
    check("case B precision is 0.5 (1 real hit out of 2 merged)",
          report_b["precision"] == 0.5,
          f"got {report_b['precision']}")
    check("case B unmatched count is 1 (the false positive)",
          len(report_b["unmatched_merged_ids"]) == 1,
          f"got {report_b['unmatched_merged_ids']}")

    # Case C: catch nothing
    merged_c = _mock_merged(
        catch_beta=False, catch_run_tick=False, catch_x_editor=False,
    )
    report_c = score(merged_c, gt)
    check("case C recall is 0", report_c["recall"] == 0.0)
    check("case C precision is 0 (no merged findings)",
          report_c["precision"] == 0.0)

    # Case D: one merged finding catches TWO ground-truth findings
    # (e.g. "run-tick.ts should be cli.ts and also mentions x-editor-pass")
    merged_d = {
        "mode": "doc",
        "reviewers": ["claude"],
        "merged_findings": [
            {
                "merged_id": "M1",
                "severity": "high",
                "reviewers": ["claude"],
                "reviewer_count": 1,
                "category": "mixed",
                "by_reviewer": {
                    "claude": {
                        "claim_quote": "run-tick.ts is wrong target and x-editor-pass is stale",
                        "location": "multiple places",
                        "verification": "checked both",
                        "suggested_fix": "fix both at once",
                    },
                },
            },
        ],
    }
    report_d = score(merged_d, gt)
    check("case D recall counts 2 hits from 1 merged finding",
          report_d["hits_count"] == 2, f"got {report_d['hits_count']}")
    check("case D recall is 0.5 (2/4)", report_d["recall"] == 0.5,
          f"got {report_d['recall']}")
    check("case D precision is 1.0 (all merged findings matched)",
          report_d["precision"] == 1.0, f"got {report_d['precision']}")

    if failures:
        print(f"\n❌ {len(failures)} test(s) failed:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("✓ all eval scoring self-tests passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Score merged findings vs ground truth")
    parser.add_argument("--merged", help="Path to merged.json")
    parser.add_argument("--ground-truth", help="Path to ground_truth.json")
    parser.add_argument(
        "--target",
        type=float,
        default=0.7,
        help="Minimum recall for exit code 0 (default 0.7)",
    )
    parser.add_argument("--selftest", action="store_true", help="Run self-tests and exit")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    if not args.merged or not args.ground_truth:
        parser.error("--merged and --ground-truth are required (or use --selftest)")

    merged = load_json(args.merged)
    gt = load_json(args.ground_truth)
    report = score(merged, gt)
    print_report(report, args.target)
    return 0 if report["recall"] >= args.target else 1


if __name__ == "__main__":
    sys.exit(main())
