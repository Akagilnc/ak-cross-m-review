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
    txt = SKILL.read_text(encoding="utf-8")
    assert txt.startswith("---\n"), "SKILL.md must open with a `---` frontmatter fence"
    body = txt[4:]
    end = body.find("\n---")
    assert end != -1, "SKILL.md frontmatter must be closed by a second `---`"
    return body[:end].splitlines()


def _top_level_key_lines():
    """Top-level `key: value` lines, ignoring full-line `#` comments and
    stripping inline ` #` comments (online R: gemini — a comment that
    contains a colon must not be mistaken for a key / a bare `: `)."""
    for ln in _frontmatter_lines():
        if not ln or ln[0].isspace() or ln.lstrip().startswith("#"):
            continue
        if " #" in ln:
            ln = ln.split(" #", 1)[0].rstrip()
        if ":" in ln:
            yield ln


def test_frontmatter_has_required_top_level_keys():
    keys = [ln.split(":", 1)[0].strip() for ln in _top_level_key_lines()]
    for required in ("name", "description", "allowed-tools"):
        assert required in keys, f"frontmatter missing top-level key '{required}'"


def test_top_level_plain_scalar_values_have_no_bare_colon_space():
    # The bug: a plain (unquoted) value containing `: ` is parsed by YAML
    # as a nested mapping → invalid frontmatter. Quoted/block scalars are
    # exempt (they can hold `: `), so only check unquoted single-line
    # values.
    for ln in _top_level_key_lines():
        key, _, value = ln.partition(":")
        value = value.lstrip()
        if not value or value[0] in "\"'|>[{":
            continue  # empty, quoted, or block/flow — YAML-safe for `: `
        assert ": " not in value, (
            f"top-level key '{key.strip()}' has a bare ': ' in its plain "
            f"scalar value — this breaks the YAML frontmatter (quote it or "
            f"use ' — ' instead). Value: {value!r}"
        )
