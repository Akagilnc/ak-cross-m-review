#!/usr/bin/env python3
"""Deterministic drift detector for the cross-model-review loop.

Transcribes the "Drift 三联检测" from
`wiki/concepts/cross-model-review.md` + `iterative-adversarial-review.md`
into a deterministic verdict so the loop stops (or doesn't) for the same
reason every time, instead of each session re-deciding by feel.

Three architectural-drift triggers (any one → STOP + reground):

  - quantity drift : this round's finding count did not decrease
  - class drift    : a finding category appears that the previous round
                     did not have (new problem surface, not convergence)
  - target drift   : round produced only low/clarity findings while the
                     count did not decrease (reviewers polishing
                     secondary output instead of fixing core issues)

One override (NOT a stop — continue with a refactor instead):

  - coverage drift : finding count is FLAT across rounds, the dominant
                     category is stable, but each round's locations are a
                     fresh surface (the rule is right, it just wasn't
                     propagated everywhere). Response is "centralize the
                     reference", not an architectural stop.
                     Evidence: 2026-04-30 v3.3 capture R1=10 → R2=1 →
                     R3=1 → R4=1 → R5=0, R3/R4 same rule different surface.

Positive termination (handled here so the loop has one source of truth):

  - converged : latest round has zero findings (N/N concur)

Input: one or more merged.json paths (the per-round output of merge.py),
in round order. Or `--selftest`.

Usage:
  python3 drift.py round-1/merged.json round-2/merged.json ...
  python3 drift.py --selftest

Output: a JSON verdict to stdout:
  {
    "verdict": "converged | converging | coverage_drift |
                architectural_drift | insufficient_history",
    "action":  "stop_converged | continue | centralize_then_continue |
                stop_reground | need_more_rounds",
    "triggers": ["quantity_drift", ...],   # only for architectural_drift
    "rounds": [ {round, count, crit_high, categories:[...]}, ... ],
    "explain": "one-line human summary"
  }

Exit codes:
  0  verdict computed (any verdict)
  1  usage / no valid input
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

CRIT_HIGH = {"critical", "high"}


def _norm_location(s: str) -> str:
    """Normalize a location string for cross-round surface comparison.

    Lowercased, whitespace-collapsed. Two findings on the same file:line
    should produce the same key so we can tell "same surface re-flagged"
    (coverage exception fails) from "fresh surface each round" (coverage
    exception holds).
    """
    return " ".join((s or "").lower().split())


def round_summary(merged: dict[str, Any], idx: int) -> dict[str, Any]:
    """Reduce a merged.json payload to the signals drift detection needs."""
    findings = merged.get("merged_findings", []) or []
    categories: set[str] = set()
    locations: set[str] = set()
    crit_high = 0
    for f in findings:
        cat = (f.get("category") or "unknown").lower().strip()
        categories.add(cat)
        if f.get("severity") in CRIT_HIGH:
            crit_high += 1
        # Pull locations from every reviewer entry in the group.
        by_rev = f.get("by_reviewer", {}) or {}
        for entries in by_rev.values():
            lst = entries if isinstance(entries, list) else [entries]
            for e in lst:
                loc = _norm_location(e.get("location", ""))
                if loc:
                    locations.add(loc)
        top_loc = _norm_location(f.get("location", ""))
        if top_loc:
            locations.add(top_loc)
    return {
        "round": idx,
        "count": len(findings),
        "crit_high": crit_high,
        "categories": sorted(categories),
        "_cat_set": categories,
        "_loc_set": locations,
    }


def _dominant_category(rs: dict[str, Any]) -> str | None:
    cats = rs["_cat_set"]
    return next(iter(sorted(cats))) if len(cats) == 1 else None


def detect(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute the drift verdict from an ordered list of round summaries."""
    public_rounds = [
        {k: v for k, v in s.items() if not k.startswith("_")}
        for s in summaries
    ]

    if not summaries:
        return {
            "verdict": "insufficient_history",
            "action": "need_more_rounds",
            "triggers": [],
            "rounds": public_rounds,
            "explain": "no rounds provided",
        }

    latest = summaries[-1]

    # Positive termination: zero findings in the latest round.
    if latest["count"] == 0:
        return {
            "verdict": "converged",
            "action": "stop_converged",
            "triggers": [],
            "rounds": public_rounds,
            "explain": f"round {latest['round']} has 0 findings — N/N concur",
        }

    if len(summaries) < 2:
        return {
            "verdict": "insufficient_history",
            "action": "need_more_rounds",
            "triggers": [],
            "rounds": public_rounds,
            "explain": "need >=2 rounds to judge drift; run another round",
        }

    prev = summaries[-2]
    count_now, count_prev = latest["count"], prev["count"]
    not_decreasing = count_now >= count_prev

    # --- Coverage-drift exception (checked FIRST: it overrides quantity
    #     drift). Flat count + single stable dominant category + this
    #     round's locations are a fresh surface vs the previous round.
    flat = count_now == count_prev and count_now > 0
    dom_now = _dominant_category(latest)
    dom_prev = _dominant_category(prev)
    same_rule = dom_now is not None and dom_now == dom_prev
    locs_now, locs_prev = latest["_loc_set"], prev["_loc_set"]
    fresh_surface = bool(locs_now) and locs_now.isdisjoint(locs_prev)
    if flat and same_rule and fresh_surface:
        return {
            "verdict": "coverage_drift",
            "action": "centralize_then_continue",
            "triggers": ["coverage_drift"],
            "rounds": public_rounds,
            "explain": (
                f"same rule '{dom_now}' re-surfacing on fresh locations each "
                f"round — centralize the reference, do NOT architectural-stop"
            ),
        }

    triggers: list[str] = []

    # Quantity drift: count did not decrease.
    if not_decreasing:
        triggers.append("quantity_drift")

    # Class drift: a category present now that was absent last round.
    new_cats = latest["_cat_set"] - prev["_cat_set"]
    if new_cats:
        triggers.append("class_drift")

    # Target drift: only low/clarity findings remain (no crit/high) yet
    # the count did not shrink — reviewers polishing secondary output.
    if latest["crit_high"] == 0 and not_decreasing:
        triggers.append("target_drift")

    if triggers:
        return {
            "verdict": "architectural_drift",
            "action": "stop_reground",
            "triggers": triggers,
            "rounds": public_rounds,
            "explain": (
                "architectural drift ("
                + ", ".join(triggers)
                + ") — stop patching, reground from implementation/architecture"
            ),
        }

    return {
        "verdict": "converging",
        "action": "continue",
        "triggers": [],
        "rounds": public_rounds,
        "explain": (
            f"count {count_prev}->{count_now}, no new category — "
            f"converging, run next round"
        ),
    }


def detect_from_files(paths: list[str]) -> dict[str, Any]:
    summaries: list[dict[str, Any]] = []
    for i, p in enumerate(paths, start=1):
        path = Path(p)
        if not path.is_file():
            print(f"warning: merged file not found: {p}", file=sys.stderr)
            continue
        try:
            with path.open() as fh:
                merged = json.load(fh)
        except json.JSONDecodeError as e:
            print(f"warning: invalid JSON in {p}: {e}", file=sys.stderr)
            continue
        summaries.append(round_summary(merged, i))
    return detect(summaries)


def _mk(round_no: int, findings: list[tuple[str, str, str]]) -> dict[str, Any]:
    """Test helper: build a merged.json-shaped payload.

    findings = list of (severity, category, location).
    """
    return {
        "merged_findings": [
            {
                "severity": sev,
                "category": cat,
                "location": loc,
                "by_reviewer": {"claude": [{"location": loc}]},
            }
            for sev, cat, loc in findings
        ]
    }


def selftest() -> int:
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append(f"FAIL: {name}" + (f" ({detail})" if detail else ""))

    def verdict(rounds: list[dict[str, Any]]) -> dict[str, Any]:
        return detect([round_summary(r, i) for i, r in enumerate(rounds, 1)])

    # 1. Converged: latest round empty.
    v = verdict([_mk(1, [("high", "logic", "a.ts:1")]), _mk(2, [])])
    check("converged on 0 findings", v["verdict"] == "converged", str(v))
    check("converged action", v["action"] == "stop_converged")

    # 2. Insufficient history: single non-empty round.
    v = verdict([_mk(1, [("high", "logic", "a.ts:1")])])
    check("single round → insufficient_history",
          v["verdict"] == "insufficient_history", str(v))

    # 3. Converging: count strictly decreasing, no new category.
    v = verdict([
        _mk(1, [("high", "logic", "a.ts:1"), ("high", "logic", "b.ts:2"),
                ("medium", "logic", "c.ts:3")]),
        _mk(2, [("high", "logic", "a.ts:1")]),
    ])
    check("decreasing count → converging",
          v["verdict"] == "converging", str(v))

    # 4. Quantity drift: count increased.
    v = verdict([
        _mk(1, [("high", "logic", "a.ts:1")]),
        _mk(2, [("high", "logic", "a.ts:1"), ("high", "logic", "d.ts:9")]),
    ])
    check("count increased → architectural_drift",
          v["verdict"] == "architectural_drift", str(v))
    check("quantity_drift trigger present",
          "quantity_drift" in v["triggers"], str(v["triggers"]))

    # 5. Class drift: new category vs previous round (count decreased so
    #    quantity drift does NOT fire — isolate class drift).
    v = verdict([
        _mk(1, [("high", "logic", "a.ts:1"), ("high", "logic", "b.ts:2")]),
        _mk(2, [("high", "security", "a.ts:1")]),
    ])
    check("new category → architectural_drift",
          v["verdict"] == "architectural_drift", str(v))
    check("class_drift trigger present",
          "class_drift" in v["triggers"], str(v["triggers"]))
    check("class drift without quantity drift",
          "quantity_drift" not in v["triggers"], str(v["triggers"]))

    # 6. Target drift: only low/clarity remain, count not decreasing.
    v = verdict([
        _mk(1, [("low", "style", "a.ts:1")]),
        _mk(2, [("low", "style", "a.ts:1"), ("clarity", "style", "b.ts:2")]),
    ])
    check("nitpick-only + not shrinking → architectural_drift",
          v["verdict"] == "architectural_drift", str(v))
    check("target_drift trigger present",
          "target_drift" in v["triggers"], str(v["triggers"]))

    # 7. Coverage-drift exception: flat count, same single rule, fresh
    #    surface each round → continue with centralization, NOT a stop.
    v = verdict([
        _mk(1, [("medium", "stale-link", "page-a.md:10")]),
        _mk(2, [("medium", "stale-link", "page-b.md:20")]),
    ])
    check("same rule fresh surface → coverage_drift",
          v["verdict"] == "coverage_drift", str(v))
    check("coverage_drift continues (no stop)",
          v["action"] == "centralize_then_continue", str(v))

    # 8. Coverage exception must NOT fire when the SAME location repeats
    #    (that is real non-convergence, not propagation lag).
    v = verdict([
        _mk(1, [("medium", "stale-link", "page-a.md:10")]),
        _mk(2, [("medium", "stale-link", "page-a.md:10")]),
    ])
    check("same rule SAME surface → architectural_drift, not coverage",
          v["verdict"] == "architectural_drift", str(v))

    # 9. The 2026-04-30 v3.3 capture trace: R1=10 → R2=1 → R3=1 → R4=1
    #    → R5=0. R3/R4 same rule, different surface. End state: converged.
    cap = [
        _mk(1, [("high", "logic", f"f{i}.md:{i}") for i in range(10)]),
        _mk(2, [("medium", "stale-rule", "s1.md:1")]),
        _mk(3, [("medium", "stale-rule", "s2.md:2")]),
        _mk(4, [("medium", "stale-rule", "s3.md:3")]),
        _mk(5, []),
    ]
    v = verdict(cap)
    check("v3.3 capture ends converged", v["verdict"] == "converged", str(v))
    # And mid-trace R3 vs R4 (flat, same rule, fresh surface) = coverage.
    v_mid = verdict(cap[2:4])
    check("v3.3 R3->R4 reads as coverage_drift not architectural",
          v_mid["verdict"] == "coverage_drift", str(v_mid))

    if failures:
        print(f"\n❌ {len(failures)} drift self-test(s) failed:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("✓ all drift self-tests passed")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("usage: drift.py <round-1/merged.json> [<round-2/merged.json> ...]",
              file=sys.stderr)
        print("       drift.py --selftest", file=sys.stderr)
        return 1
    if args[0] == "--selftest":
        return selftest()
    result = detect_from_files(args)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
