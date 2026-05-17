"""Real behavior tests for lib/drift.py — location normalization and the
round_summary reducer that feeds drift/termination detection."""

import drift


def test_norm_location_lower_collapse_and_none():
    assert drift._norm_location("  Src/A.TS:10  ") == "src/a.ts:10"
    assert drift._norm_location(None) == ""
    assert drift._norm_location("") == ""
    assert drift._norm_location("A   B") == "a b"


def test_round_summary_counts_severity_categories_locations():
    merged = {"merged_findings": [
        {"category": "Bug", "severity": "HIGH", "location": "src/a.ts:10"},
        {"category": "bug", "severity": "low", "location": "src/a.ts:10"},
        {"severity": "Critical", "location": "src/b.ts:5"},
    ]}
    rs = drift.round_summary(merged, 2)
    assert rs["round"] == 2
    assert rs["count"] == 3
    # HIGH + Critical count as crit_high; "low" does not.
    assert rs["crit_high"] == 2
    # Missing category falls back to "unknown"; categories sorted+deduped.
    assert rs["categories"] == ["bug", "unknown"]
    # Duplicate location collapses to one entry in the primary-location set.
    assert rs["_loc_set"] == {"src/a.ts:10", "src/b.ts:5"}


def test_round_summary_empty_payload():
    rs = drift.round_summary({}, 0)
    assert rs["round"] == 0
    assert rs["count"] == 0
    assert rs["crit_high"] == 0
    assert rs["categories"] == []


def test_round_summary_normalizes_padded_severity():
    merged = {"merged_findings": [{"severity": " High ", "location": "x:1"}]}
    rs = drift.round_summary(merged, 1)
    assert rs["crit_high"] == 1
