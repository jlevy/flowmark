"""Test reference-style link rendering.

Regression tests for https://github.com/jlevy/flowmark/issues/45

marko's inline.Link element does not preserve the original reference style
(inline, full, collapsed, or shortcut); it only stores ``dest`` and ``title``.
flowmark reconstructs a reference link by matching the destination/title back
to a link reference definition.

When the link text equals the matched label, the link must NOT be collapsed to
the shortcut form ``[label]``: a shortcut reference is fragile because it merges
with a following ``(...)`` (becoming an inline link) or a following ``[...]``
(becoming a full/collapsed reference), silently changing or dropping links.
The collapsed reference form ``[label][]`` is used instead, which is unambiguous.
"""

import marko

from flowmark.formats.flowmark_markdown import flowmark_markdown


def _html(src: str) -> str:
    """Render markdown to HTML with stock marko, for semantic equivalence checks."""
    parser = marko.Markdown()
    return parser.render(parser.parse(src)).strip()


def test_full_reference_with_distinct_label_preserved():
    """[text][label] with text != label stays a full reference (the 'fm' case)."""
    md = flowmark_markdown()
    src = "Use [flowmark][fm]\n\n[fm]: https://github.com/jlevy/flowmark\n"
    assert md(src) == "Use [flowmark][fm]\n\n[fm]: https://github.com/jlevy/flowmark\n"


def test_label_equals_text_not_collapsed_to_shortcut():
    """[flowmark][flowmark] must not become a bare [flowmark] shortcut.

    This is the exact case from issue #45.
    """
    md = flowmark_markdown()
    src = "Use [flowmark][flowmark]\n\n[flowmark]: https://github.com/jlevy/flowmark\n"
    result = md(src)
    assert result == "Use [flowmark][]\n\n[flowmark]: https://github.com/jlevy/flowmark\n"


def test_issue_45_link_survives_round_trip():
    """The reformatted output must still parse to the same link as the input."""
    md = flowmark_markdown()
    src = "Use [flowmark][flowmark]\n\n[flowmark]: https://github.com/jlevy/flowmark\n"
    result = md(src)
    assert _html(result) == _html(src)
    # The link is preserved, not dropped.
    assert '<a href="https://github.com/jlevy/flowmark">flowmark</a>' in _html(result)


def test_idempotent_on_collapsed_reference():
    """Formatting is stable: collapsed reference output is a fixed point."""
    md = flowmark_markdown()
    src = "Use [flowmark][]\n\n[flowmark]: https://github.com/jlevy/flowmark\n"
    once = md(src)
    assert md(once) == once


def test_shortcut_input_normalized_to_collapsed_reference():
    """A shortcut reference [flowmark] is normalized to the explicit [flowmark][]."""
    md = flowmark_markdown()
    src = "Use [flowmark]\n\n[flowmark]: https://github.com/jlevy/flowmark\n"
    assert md(src) == "Use [flowmark][]\n\n[flowmark]: https://github.com/jlevy/flowmark\n"


def test_label_equals_text_followed_by_parens_keeps_link():
    """[flowmark][flowmark](/path): collapsing to shortcut would steal the parens.

    Shortcut [flowmark](/path) reparses as an inline link to '/path', changing the
    destination. The collapsed form keeps the original destination.
    """
    md = flowmark_markdown()
    src = "See [flowmark][flowmark](/path) end.\n\n[flowmark]: https://example.com\n"
    result = md(src)
    assert _html(result) == _html(src)
    assert '<a href="https://example.com">flowmark</a>' in _html(result)


def test_label_equals_text_followed_by_reference_keeps_both_links():
    """[flowmark][flowmark][ref2]: collapsing to shortcut would drop the first link.

    Shortcut [flowmark][ref2] reparses as one full reference (flowmark -> ref2),
    losing the flowmark link entirely.
    """
    md = flowmark_markdown()
    src = (
        "See [flowmark][flowmark][ref2] end.\n\n"
        "[flowmark]: https://example.com\n"
        "[ref2]: https://example.org\n"
    )
    result = md(src)
    assert _html(result) == _html(src)
    assert '<a href="https://example.com">flowmark</a>' in _html(result)
    assert '<a href="https://example.org">ref2</a>' in _html(result)
