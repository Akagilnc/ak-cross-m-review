"""Regression: SKILL.md's YAML frontmatter must not be broken by a stray
`: ` (colon-space).

A description edit once introduced an unquoted `: ` inside the plain
scalar (`trigger point: ship-pre …`), which YAML reads as a mapping
separator → the whole frontmatter became invalid
(`mapping values are not allowed in this context`) → the skill loader
could not discover/load `/ak-cross-m-review` (online review caught it as
a P1). Stdlib-only (the repo's tests avoid third-party deps), so instead
of a full YAML parse we pin the exact failure class: a top-level plain
(unquoted) scalar value must not contain a bare `: `."""

from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def _frontmatter_lines():
    txt = SKILL.read_text()
    assert txt.startswith("---\n"), "SKILL.md must open with a `---` frontmatter fence"
    body = txt[4:]
    end = body.find("\n---")
    assert end != -1, "SKILL.md frontmatter must be closed by a second `---`"
    return body[:end].splitlines()


def test_frontmatter_has_required_top_level_keys():
    keys = [ln.split(":", 1)[0] for ln in _frontmatter_lines()
            if ln and not ln[0].isspace() and ":" in ln]
    for required in ("name", "description", "allowed-tools"):
        assert required in keys, f"frontmatter missing top-level key '{required}'"


def test_top_level_plain_scalar_values_have_no_bare_colon_space():
    # The bug: a plain (unquoted) value containing `: ` is parsed by YAML
    # as a nested mapping → invalid frontmatter. Quoted/block scalars are
    # exempt (they can hold `: `), so only check unquoted single-line
    # values.
    for ln in _frontmatter_lines():
        if not ln or ln[0].isspace() or ":" not in ln:
            continue  # not a top-level key line
        key, _, value = ln.partition(":")
        value = value.lstrip()
        if not value or value[0] in "\"'|>[{":
            continue  # empty, quoted, or block/flow — YAML-safe for `: `
        assert ": " not in value, (
            f"top-level key '{key.strip()}' has a bare ': ' in its plain "
            f"scalar value — this breaks the YAML frontmatter (quote it or "
            f"use ' — ' instead). Value: {value!r}"
        )
