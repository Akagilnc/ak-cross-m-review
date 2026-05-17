"""Real behavior tests for lib/merge.py — fuzzy finding-match + grounding
score, the consensus core. Assertions check actual computed values."""

import merge


def test_tokenize_empty_lowercase_and_basename():
    assert merge.tokenize("") == set()
    # Path-shaped token also emits its basename for cross-reviewer match.
    toks = merge.tokenize("src/workflow/run-tick.ts")
    assert "run-tick.ts" in toks
    # Lowercased.
    assert "foobar" in merge.tokenize("FOOBAR")
    # Tokens shorter than 3 chars are dropped entirely.
    assert merge.tokenize("ab cd") == set()


def test_findings_match_same_category_one_shared_token():
    a = {"category": "bug", "claim_quote": "null deref parsePayment",
         "location": "src/pay.ts:42"}
    b = {"category": "BUG", "claim_quote": "parsePayment returns null",
         "location": "src/pay.ts:42"}
    # Same category (case-insensitive) + shared identifier tokens → match.
    assert merge.findings_match(a, b) is True


def test_findings_match_different_category_low_overlap_no_match():
    a = {"category": "security", "claim_quote": "unique_alpha_token zeta",
         "location": "fileA.py:1"}
    b = {"category": "performance", "claim_quote": "unique_alpha_token",
         "location": "fileB.py:9"}
    # Different categories need >= min_shared+2 shared tokens; only 1 here.
    assert merge.findings_match(a, b) is False


def test_compute_grounding_score_counts_real_tool_invocations():
    f = {"verification": "ran rg then python3 then Read the file"}
    # rg + python3 + Read = 3 grounding hits.
    assert merge.compute_grounding_score(f) == 3
    assert merge.compute_grounding_score({}) == 0
    assert merge.compute_grounding_score({"verification": None}) == 0
