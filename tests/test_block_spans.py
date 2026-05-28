"""
Spans are attached to every block element by the `CustomParser` so consumers can map
parsed elements back to exact source offsets without re-parsing or regex guessing.
"""

from __future__ import annotations

from textwrap import dedent

from marko import block
from marko.block import (
    BlankLine,
    FencedCode,
    Heading,
    List,
    ListItem,
    Paragraph,
    Quote,
    SetextHeading,
    ThematicBreak,
)

from flowmark.formats.flowmark_markdown import flowmark_markdown


def _parse(text: str) -> block.Document:
    return flowmark_markdown().parse(text)


def test_top_level_block_spans_are_exact_and_authoritative():
    text = dedent(
        """
        # Title

        First paragraph.
        Continued.

        ## Subhead

        Second paragraph.

        ---

        ```python
        x = 1
        ```
        """
    ).strip()

    doc = _parse(text)
    blocks = [c for c in doc.children if not isinstance(c, BlankLine)]
    # CustomFencedCode is a flowmark subclass of FencedCode; check via isinstance, not name.
    assert [isinstance(b, Heading) for b in blocks] == [True, False, True, False, False, False]
    assert [isinstance(b, Paragraph) for b in blocks] == [False, True, False, True, False, False]
    assert isinstance(blocks[4], ThematicBreak)
    assert isinstance(blocks[5], FencedCode)

    for b in blocks:
        start, end = b.span  # type: ignore[attr-defined]
        assert 0 <= start < end <= len(text)
        # The slice must contain the verbatim source for the block's leading marker.
        slice_ = text[start:end]
        if isinstance(b, Heading):
            assert slice_.startswith("#")
        elif isinstance(b, ThematicBreak):
            assert slice_.strip() == "---"
        elif isinstance(b, FencedCode):
            assert slice_.startswith("```")


def test_paragraph_immediately_after_heading_has_correct_span():
    # No blank line between blocks — the historical failure mode for regex-based
    # scanners. Spans must come straight from marko and split correctly.
    text = "# Title\nParagraph immediately after.\n\n## Next\nBody."
    doc = _parse(text)
    blocks = [c for c in doc.children if not isinstance(c, BlankLine)]
    assert [type(b).__name__ for b in blocks] == ["Heading", "Paragraph", "Heading", "Paragraph"]
    for b in blocks:
        s, e = b.span  # type: ignore[attr-defined]
        assert 0 <= s < e <= len(text)
    assert text[blocks[0].span[0] : blocks[0].span[1]].lstrip().startswith("# ")  # type: ignore[attr-defined]
    assert "Paragraph immediately after." in text[blocks[1].span[0] : blocks[1].span[1]]  # type: ignore[attr-defined]


def test_setext_heading_span_covers_text_and_underline():
    text = "Title\n=====\n\nBody.\n"
    doc = _parse(text)
    blocks = [c for c in doc.children if not isinstance(c, BlankLine)]
    assert isinstance(blocks[0], (Heading, SetextHeading))
    s, e = blocks[0].span  # type: ignore[attr-defined]
    slice_ = text[s:e]
    assert "Title" in slice_ and "=====" in slice_


def test_fenced_code_span_includes_internal_blank_lines():
    text = dedent(
        """
        ```python
        x = 1

        y = 2
        ```
        """
    ).strip()
    doc = _parse(text)
    code = next(c for c in doc.children if isinstance(c, FencedCode))
    s, e = code.span  # type: ignore[attr-defined]
    slice_ = text[s:e]
    assert slice_.count("```") == 2
    assert "x = 1" in slice_ and "y = 2" in slice_


def test_nested_list_item_and_sublist_have_spans():
    # marko's container blocks (List → ListItem → nested List) recurse through
    # parse_source, so spans must propagate at every level.
    text = dedent(
        """
        - parent one
          - child a
          - child b
        - parent two
        """
    ).strip()
    doc = _parse(text)
    lst = next(c for c in doc.children if isinstance(c, List))
    s, e = lst.span  # type: ignore[attr-defined]
    assert 0 <= s < e <= len(text)
    items = [c for c in lst.children if isinstance(c, ListItem)]
    assert len(items) == 2
    for item in items:
        item_start, item_end = item.span  # type: ignore[attr-defined]
        assert s <= item_start < item_end <= e
    # The first item should contain a nested List.
    nested = [c for c in items[0].children if isinstance(c, List)]
    assert len(nested) == 1
    ns, ne = nested[0].span  # type: ignore[attr-defined]
    assert items[0].span[0] <= ns < ne <= items[0].span[1]  # type: ignore[attr-defined]
    nested_items = [c for c in nested[0].children if isinstance(c, ListItem)]
    assert len(nested_items) == 2


def test_blockquote_children_have_spans():
    text = "> First quoted line.\n> Still in quote.\n\nAfter.\n"
    doc = _parse(text)
    quote = next(c for c in doc.children if isinstance(c, Quote))
    s, e = quote.span  # type: ignore[attr-defined]
    assert text[s:e].lstrip().startswith(">")
    # Inner Paragraph should also carry a span recorded by the recursive parse_source.
    inner_paras = [c for c in quote.children if isinstance(c, Paragraph)]
    assert inner_paras
    for p in inner_paras:
        ps, pe = p.span  # type: ignore[attr-defined]
        assert s <= ps < pe <= e


def test_document_has_full_span():
    text = "# Just a heading\n"
    doc = _parse(text)
    assert doc.span == (0, len(text))  # type: ignore[attr-defined]


def test_block_span_helper_reads_the_span_attribute():
    from flowmark.markdown_ast import block_span

    text = "# Heading\n\nParagraph.\n"
    doc = _parse(text)
    for child in doc.children:
        if isinstance(child, BlankLine):
            continue
        start, end = block_span(child)
        assert 0 <= start < end <= len(text)


def test_spans_round_trip_for_a_realistic_document():
    text = dedent(
        """
        # Project Notes

        Introduction paragraph here.

        ## Goals

        - Be fast.
        - Be accurate.
        - Stay dependency-light.

        > A cautionary quote.

        | a | b |
        | - | - |
        | 1 | 2 |

        ```python
        x = 1
        ```

        ---

        Final paragraph.
        """
    ).strip()
    doc = _parse(text)
    blocks = [c for c in doc.children if not isinstance(c, BlankLine)]
    # Each top-level block's span maps back to a non-empty source slice and the slices
    # appear in strict document order with no overlap.
    last_end = 0
    for b in blocks:
        s, e = b.span  # type: ignore[attr-defined]
        assert s >= last_end
        assert e > s
        assert text[s:e].strip(), "every block should map to non-empty source"
        last_end = e
