"""Real behavior tests for lib/drift.py — location normalization and the
round_summary reducer that feeds drift/termination detection."""

import json

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


def test_detect_from_files_missing_latest_round_is_input_error(tmp_path):
    # Regression for the Codex [P1]: round-1 valid but the LATEST round's
    # merged.json missing must surface input_error, not silently evaluate
    # the earlier round as "latest" and risk a false stop_converged
    # (a green review gate on a broken pipeline).
    r1 = tmp_path / "round-1" / "merged.json"
    r1.parent.mkdir(parents=True)
    r1.write_text(json.dumps(
        {"merged_findings": [{"severity": "high", "category": "bug",
                              "location": "a.py:1"}]}))
    r2_missing = str(tmp_path / "round-2" / "merged.json")
    result = drift.detect_from_files([str(r1), r2_missing])
    assert result["verdict"] == "input_error"
    assert result["action"] == "stop_reground"


def test_detect_from_files_all_valid_not_input_error(tmp_path):
    # Guard the other direction: when every requested artifact loads, the
    # new any-error gate must NOT spuriously fire input_error.
    paths = []
    for i in (1, 2):
        p = tmp_path / f"round-{i}" / "merged.json"
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({"merged_findings": []}))
        paths.append(str(p))
    result = drift.detect_from_files(paths)
    assert result["verdict"] != "input_error"
