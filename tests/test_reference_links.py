"""Test reference-style link rendering.

Regression tests for https://github.com/jlevy/flowmark/issues/45

marko's stock inline.Link element does not preserve the original reference style
(inline, full, collapsed, or shortcut); it only stores ``dest`` and ``title``.
flowmark's ``CustomLink`` records the authored style and label at parse time, so an
inline link and a reference link to the same destination stay distinguishable.
Reconstructing the reference form by searching the definitions for a matching
destination -- the earlier approach -- rewrote inline links that happened to point at
an already-defined URL.

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


def test_inline_link_sharing_a_definition_url_stays_inline():
    """An inline link is not rewritten just because some definition shares its URL."""
    md = flowmark_markdown()
    src = (
        "Per the [memory docs][cc-mem], see this.\n\n"
        "[cc-mem]: https://example.com/memory\n\n"
        "Later, an inline link: [memory docs](https://example.com/memory) here.\n"
    )
    out = md.convert(src)

    assert "[memory docs](https://example.com/memory)" in out, out
    assert "[memory docs][cc-mem]" in out, out
    assert _html(src) == _html(out)


def test_inline_link_with_a_defined_url_is_stable_across_passes():
    """The rewrite was also non-idempotent: the inline form has to survive a second pass."""
    md = flowmark_markdown()
    src = "[docs]: https://example.com/x\n\nAn inline link to [docs](https://example.com/x) here.\n"
    once = md.convert(src)
    assert md.convert(once) == once, once


def test_reference_link_to_an_also_inlined_url_keeps_its_label():
    """A real reference link keeps reference form even when the URL is also used inline."""
    md = flowmark_markdown()
    src = (
        "[ref]: https://example.com/z\n\n"
        "A reference [text][ref] and an inline [text](https://example.com/z).\n"
    )
    out = md.convert(src)

    assert "[text][ref]" in out, out
    assert "[text](https://example.com/z)" in out, out
    assert _html(src) == _html(out)


def test_inline_link_with_an_empty_destination_stays_inline():
    """`[text]()` resolves to an empty destination, like a reference can — but is inline."""
    md = flowmark_markdown()
    src = "An empty inline link: [text]() here.\n"
    out = md.convert(src)

    assert "[text]()" in out, out
    assert _html(src) == _html(out)


def test_collapsed_reference_to_an_empty_destination_stays_a_reference():
    """A `[foo]: <>` definition resolves `[foo][]` to an empty destination."""
    md = flowmark_markdown()
    src = "[foo]: <>\n\n[foo][]\n"
    out = md.convert(src)

    assert "[foo][]" in out, out
    assert _html(src) == _html(out)


def test_shortcut_reference_keeps_the_normalized_label_when_case_differs():
    """`[Foo]` against a `[Foo]:` definition renders full, not collapsed.

    Definitions are keyed by normalized label, so the label is `foo` while the text is
    `Foo`. Collapsing to `[Foo][]` would still resolve, but it is a different source form
    than this formatter has always emitted, and the shared conformance corpus pins it.
    """
    md = flowmark_markdown()
    src = "[Foo]: /url\n\n[Foo]\n"
    out = md.convert(src)

    assert "[Foo][foo]" in out, out
    assert _html(src) == _html(out)
