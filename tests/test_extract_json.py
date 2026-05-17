"""Real behavior tests for lib/extract_json.py — the reviewer-stdout JSON
salvage helper. Covers all five extraction passes plus the shape guards."""

import extract_json as ej


def test_try_parse_valid_invalid_and_nonstr():
    assert ej.try_parse('{"a": 1}') == {"a": 1}
    assert ej.try_parse("not json at all") is None
    # TypeError path (json.loads(None)) must be swallowed, not raised.
    assert ej.try_parse(None) is None


def test_is_findings_shape():
    assert ej.is_findings_shape({"findings": []}) is True
    assert ej.is_findings_shape({"findings": [{"x": 1}]}) is True
    assert ej.is_findings_shape({"no": "findings"}) is False
    assert ej.is_findings_shape([{"findings": []}]) is False
    assert ej.is_findings_shape("string") is False


def test_extract_pass1_clean_json():
    obj, p = ej.extract('{"findings": [{"id": 1}]}')
    assert p == 1
    assert obj["findings"] == [{"id": 1}]


def test_extract_pass2_json_fence():
    text = 'status line\n```json\n{"findings": [42]}\n```\ntrailing'
    obj, p = ej.extract(text)
    assert p == 2
    assert obj["findings"] == [42]


def test_extract_pass3_anonymous_fence():
    text = 'thinking...\n```\n{"findings": []}\n```'
    obj, p = ej.extract(text)
    assert p == 3
    assert obj["findings"] == []


def test_extract_pass4_braces_in_prose():
    text = 'preamble noise {"findings": [{"sev": "high"}]} trailing noise'
    obj, p = ej.extract(text)
    assert p == 4
    assert obj["findings"][0]["sev"] == "high"


def test_extract_pass5_salvage_patches_missing_findings():
    # Braces parse to a dict but lack a findings array → salvaged with an
    # injected empty findings list, still reported as pass 4.
    obj, p = ej.extract('junk {"foo": 1} junk')
    assert p == 4
    assert obj["foo"] == 1
    assert obj["findings"] == []


def test_extract_no_json_returns_none_pass5():
    obj, p = ej.extract("absolutely no json here, just words")
    assert obj is None
    assert p == 5
