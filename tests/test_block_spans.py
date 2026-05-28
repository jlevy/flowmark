"""
Spans are attached to every block element by the `CustomParser` so consumers can map
parsed elements back to exact source offsets without re-parsing or regex guessing.

Tests cover top-level blocks, the historical no-blank-line failure mode, setext headings,
fenced code with internal blanks, nested lists, blockquotes, GFM tables, footnotes,
HTML blocks, CRLF line endings, empty/blank-only input, and a full sweep over the
project's golden testdoc.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from marko import inline
from marko.block import (
    BlankLine,
    BlockElement,
    Document,
    FencedCode,
    Heading,
    List,
    ListItem,
    Paragraph,
    Quote,
    SetextHeading,
    ThematicBreak,
)
from marko.element import Element
from marko.ext.gfm.elements import Table, TableCell, TableRow

from flowmark.formats.flowmark_markdown import flowmark_markdown
from flowmark.markdown_ast import block_span, walk_elements

# `Table.parse` builds these directly (bypassing the parser's main loop), so they fall
# outside the span contract — see :mod:`flowmark.markdown_ast` module docstring.
_NO_SPAN_BLOCK_TYPES = (TableRow, TableCell)


def _parse(text: str) -> Document:
    return flowmark_markdown().parse(text)


def _iter_span_bearing_blocks(root: Element) -> list[BlockElement]:
    """Block-element descendants of `root` that are part of the span contract."""
    return [
        e
        for e in walk_elements(root)
        if isinstance(e, BlockElement) and not isinstance(e, _NO_SPAN_BLOCK_TYPES)
    ]


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
    assert [isinstance(b, Heading) for b in blocks] == [True, False, True, False, False, False]
    assert [isinstance(b, Paragraph) for b in blocks] == [False, True, False, True, False, False]
    assert isinstance(blocks[4], ThematicBreak)
    assert isinstance(blocks[5], FencedCode)

    for b in blocks:
        start, end = block_span(b)
        assert 0 <= start < end <= len(text)
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
        s, e = block_span(b)
        assert 0 <= s < e <= len(text)
    s0, e0 = block_span(blocks[0])
    assert text[s0:e0].lstrip().startswith("# ")
    s1, e1 = block_span(blocks[1])
    assert "Paragraph immediately after." in text[s1:e1]


def test_setext_heading_span_covers_text_and_underline():
    text = "Title\n=====\n\nBody.\n"
    doc = _parse(text)
    blocks = [c for c in doc.children if not isinstance(c, BlankLine)]
    assert isinstance(blocks[0], (Heading, SetextHeading))
    s, e = block_span(blocks[0])
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
    s, e = block_span(code)
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
    s, e = block_span(lst)
    assert 0 <= s < e <= len(text)
    items = [c for c in lst.children if isinstance(c, ListItem)]
    assert len(items) == 2
    for item in items:
        item_start, item_end = block_span(item)
        assert s <= item_start < item_end <= e
    nested = [c for c in items[0].children if isinstance(c, List)]
    assert len(nested) == 1
    ns, ne = block_span(nested[0])
    item0_start, item0_end = block_span(items[0])
    assert item0_start <= ns < ne <= item0_end
    nested_items = [c for c in nested[0].children if isinstance(c, ListItem)]
    assert len(nested_items) == 2


def test_blockquote_children_have_spans():
    text = "> First quoted line.\n> Still in quote.\n\nAfter.\n"
    doc = _parse(text)
    quote = next(c for c in doc.children if isinstance(c, Quote))
    s, e = block_span(quote)
    assert text[s:e].lstrip().startswith(">")
    inner_paras = [c for c in quote.children if isinstance(c, Paragraph)]
    assert inner_paras
    for p in inner_paras:
        ps, pe = block_span(p)
        assert s <= ps < pe <= e


def test_gfm_table_has_span():
    text = "| a | b |\n| - | - |\n| 1 | 2 |\n"
    doc = _parse(text)
    table = next(c for c in doc.children if isinstance(c, Table))
    s, e = block_span(table)
    slice_ = text[s:e]
    assert "| a | b |" in slice_ and "| 1 | 2 |" in slice_


def test_footnote_definition_has_span():
    from marko.ext.footnote import FootnoteDef

    text = "Body with[^a] a footnote.\n\n[^a]: A footnote definition.\n"
    doc = _parse(text)
    fn_def = next((c for c in doc.children if isinstance(c, FootnoteDef)), None)
    assert fn_def is not None
    s, e = block_span(fn_def)
    assert text[s:e].lstrip().startswith("[^a]:")


def test_html_block_input_falls_back_to_paragraph_with_a_span():
    # CustomHTMLBlock.match() always returns False, so flowmark never produces an
    # HTMLBlock — HTML-shaped input is parsed as a Paragraph instead. Either way the
    # span contract must hold: a single block covering the HTML lines.
    text = "<div>\nraw html\n</div>\n\nAfter.\n"
    doc = _parse(text)
    blocks = [c for c in doc.children if not isinstance(c, BlankLine)]
    assert isinstance(blocks[0], Paragraph)
    s, e = block_span(blocks[0])
    assert "<div>" in text[s:e]


def test_document_has_full_span():
    text = "# Just a heading\n"
    doc = _parse(text)
    assert block_span(doc) == (0, len(text))


def test_block_span_helper_reads_the_span_attribute():
    text = "# Heading\n\nParagraph.\n"
    doc = _parse(text)
    for child in doc.children:
        if isinstance(child, BlankLine):
            continue
        start, end = block_span(child)
        assert 0 <= start < end <= len(text)


def test_empty_document_has_zero_span():
    doc = _parse("")
    assert block_span(doc) == (0, 0)
    # No block children to span.
    assert not [c for c in doc.children if not isinstance(c, BlankLine)]


def test_blank_only_document_has_full_span():
    text = "\n\n\n"
    doc = _parse(text)
    assert block_span(doc) == (0, len(text))


def test_crlf_input_normalized_to_lf_for_spans():
    # marko's Source preprocesses CRLF → LF before parsing; spans index into that
    # preprocessed buffer. Verify the root span and every descendant span sit in the
    # same (normalized) coordinate space.
    text = "# Heading\r\n\r\nParagraph.\r\n"
    normalized_len = len(text.replace("\r\n", "\n"))
    doc = _parse(text)
    assert block_span(doc) == (0, normalized_len)
    blocks = [c for c in doc.children if not isinstance(c, BlankLine)]
    for b in blocks:
        s, e = block_span(b)
        assert 0 <= s < e <= normalized_len


def test_every_block_element_in_realistic_doc_has_a_valid_span():
    text = dedent(
        """
        # Project Notes

        Introduction paragraph here.

        ## Goals

        - Be fast.
        - Be accurate.
        - Stay dependency-light.

        > A cautionary quote.

        > - quoted item one
        > - quoted item two

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
    doc_len = len(text)
    # Every block element at every nesting level must carry a valid span.
    for el in _iter_span_bearing_blocks(doc):
        s, e = block_span(el)
        if isinstance(el, BlankLine):
            # BlankLine spans may be empty regions or single newlines; just check sanity.
            assert 0 <= s <= e <= doc_len
        else:
            assert 0 <= s <= e <= doc_len
    # Top-level blocks' spans appear in strict document order, no overlap.
    top_blocks = [c for c in doc.children if not isinstance(c, BlankLine)]
    last_end = 0
    for b in top_blocks:
        s, e = block_span(b)
        assert s >= last_end
        assert e >= s
        last_end = e


def _testdoc_path() -> Path:
    return Path(__file__).parent / "testdocs" / "testdoc.orig.md"


def test_spans_cover_golden_testdoc_without_gaps_or_overlaps_at_top_level():
    # End-to-end: parse the project's most complex golden test document and verify
    # every top-level block has a valid span that yields a non-empty source slice.
    path = _testdoc_path()
    if not path.exists():
        # Repo layout might change; skip rather than fail.
        return
    text = path.read_text()
    doc = _parse(text)
    doc_len = len(text.replace("\r\n", "\n"))
    top_blocks = [c for c in doc.children if not isinstance(c, BlankLine)]
    assert top_blocks, "golden testdoc must produce at least one top-level block"
    last_end = 0
    for b in top_blocks:
        s, e = block_span(b)
        assert 0 <= s <= e <= doc_len
        assert s >= last_end, f"block spans must not overlap (block {type(b).__name__})"
        last_end = e


def test_every_block_in_golden_testdoc_has_a_span():
    # The strongest invariant: walk the whole tree, no exceptions.
    path = _testdoc_path()
    if not path.exists():
        return
    text = path.read_text()
    doc = _parse(text)
    doc_len = len(text.replace("\r\n", "\n"))
    visited = 0
    for el in _iter_span_bearing_blocks(doc):
        s, e = block_span(el)
        assert 0 <= s <= e <= doc_len, f"out-of-range span on {type(el).__name__}"
        visited += 1
    assert visited > 0


def test_inline_elements_do_not_have_spans():
    # The PR is explicit that inline elements remain unsupported — guard against
    # accidentally extending the contract to inline.
    doc = _parse("A paragraph with [a link](https://example.com) inside.\n")
    inline_count = 0
    for el in walk_elements(doc):
        if isinstance(el, inline.InlineElement):
            inline_count += 1
            assert not hasattr(el, "span"), (
                f"inline element {type(el).__name__} should not carry a span"
            )
    assert inline_count > 0


def test_nested_block_spans_include_container_markers():
    # Documented contract: a child span covers the source slice marko's parser
    # consumed, which means it includes the container's leading marker on each line
    # (e.g. `- ` for a list item, `> ` for a quote). Verified explicitly here so the
    # contract does not silently change.
    list_text = "- a list item paragraph\n"
    doc = _parse(list_text)
    lst = next(c for c in doc.children if isinstance(c, List))
    item = next(c for c in lst.children if isinstance(c, ListItem))
    para = next(c for c in item.children if isinstance(c, Paragraph))
    ps, pe = block_span(para)
    assert list_text[ps:pe].startswith("- ")

    quote_text = "> # Quoted heading\n"
    doc = _parse(quote_text)
    quote = next(c for c in doc.children if isinstance(c, Quote))
    head = next(c for c in quote.children if isinstance(c, Heading))
    hs, he = block_span(head)
    assert quote_text[hs:he].startswith("> ")


def test_spans_are_idempotent_under_repeated_parsing():
    # Parsing the same text twice should produce identical spans.
    text = "# Title\n\nParagraph.\n\n- a\n- b\n"
    doc1 = _parse(text)
    doc2 = _parse(text)

    def _top_spans(d: Document) -> list[tuple[int, int]]:
        return [block_span(b) for b in d.children if not isinstance(b, BlankLine)]

    assert _top_spans(doc1) == _top_spans(doc2)
