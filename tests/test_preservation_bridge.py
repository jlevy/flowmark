from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest
from marko import block

from flowmark.formats.flowmark_markdown import (
    ProtectedBlock,
    ProtectedInline,
    flowmark_markdown,
)
from flowmark.linewrapping.text_wrapping import measure_protected_text
from flowmark.preservation.bridge import (
    ESCAPE_MARKER,
    TOKEN_END,
    TOKEN_LENGTH,
    TOKEN_START,
    InvalidTokenError,
    encode_token,
    parse_token,
    protect_source,
    restore_source,
)
from flowmark.preservation.normalization import normalize_source
from flowmark.preservation.scanner import scan_protected_regions
from flowmark.transforms.doc_cleanups import doc_cleanups
from flowmark.transforms.doc_transforms import rewrite_text_across_inlines, rewrite_text_content
from flowmark.typography.ellipses import ellipses
from flowmark.typography.smartquotes import smart_quotes


def _identity_wrapper(text: str, initial_indent: str, subsequent_indent: str) -> str:
    del subsequent_indent
    return initial_indent + text


def _protected(text: str):
    source = normalize_source(text)
    return protect_source(source, scan_protected_regions(source))


def test_authored_markers_round_trip_with_bounded_parser_text() -> None:
    collision = ESCAPE_MARKER * 4096 + TOKEN_START + TOKEN_END
    normalized = normalize_source(collision + " " + "$x$" * 2048)
    protected = protect_source(normalized, scan_protected_regions(normalized))

    assert len(protected.regions) == 2048
    assert len(protected.text) <= 5 * len(normalized.text)
    assert restore_source(protected.text, protected) == normalized.text


def test_authored_marker_escapes_retain_one_logical_column_each() -> None:
    collision = f"a{ESCAPE_MARKER}{TOKEN_START}{TOKEN_END}b"
    protected = _protected(collision)

    assert protected.regions == ()
    parser_text = protected.text.removesuffix("\n")
    assert measure_protected_text(parser_text, protected).final_width == len(collision)


@pytest.mark.parametrize("index", [0, 1, 255, 256, (1 << 64) - 1])
def test_token_encoding_is_fixed_width(index: int) -> None:
    token = encode_token(index)

    assert len(token) == TOKEN_LENGTH
    assert parse_token(token) == index


@pytest.mark.parametrize("index", [-1, True, 1 << 64])
def test_token_encoder_rejects_indexes_outside_unsigned_64_bits(index: int) -> None:
    with pytest.raises(InvalidTokenError, match="token index"):
        encode_token(index)


def test_token_parser_rejects_malformed_fixed_width_indexes() -> None:
    token = encode_token(0)
    malformed = token[:1] + "0" + token[2:]

    with pytest.raises(InvalidTokenError, match="token index"):
        parse_token(malformed)
    with pytest.raises(InvalidTokenError, match="malformed preservation token"):
        parse_token(token[:-1])


def test_protection_retains_block_scaffold_but_keeps_exact_source_in_side_table() -> None:
    protected = _protected("before $x_1$ after\n\n- intro\n  $$\n  __body__\n  $$\n  after")
    inline, block = protected.regions

    assert inline.source == "$x_1$"
    assert inline.source not in protected.text
    assert block.scaffold_prefix == "  "
    assert block.source == "  $$\n  __body__\n  $$\n"
    assert f"  {protected.tokens[1]}\n" in protected.text
    assert block.source not in protected.text


def test_marko_adapter_round_trips_parser_collisions_and_distinguishes_forms() -> None:
    text = (
        '# Heading $\\text{__init__} [link](url) &amp; <i>x</i> `code` "..."$\n\n'
        "- intro\n"
        "  $$\n"
        "  __not emphasis__ [not a link](\n"
        "  $$ {#equation}\n"
        "  after"
    )
    protected = _protected(text)
    markdown = flowmark_markdown(_identity_wrapper, _protected_source=protected)
    document = markdown.parse(protected.text)

    heading = cast(block.Heading, document.children[0])
    markdown_list = cast(block.List, document.children[2])
    list_item = cast(block.ListItem, markdown_list.children[0])
    heading_token = heading.children[1]
    block_token = list_item.children[1]
    assert isinstance(heading_token, ProtectedInline)
    assert isinstance(block_token, ProtectedBlock)

    doc_cleanups(document)
    rewrite_text_across_inlines(document, smart_quotes)
    rewrite_text_content(document, ellipses, coalesce_lines=True)
    rendered = markdown.render(document)
    restored = restore_source(rendered, protected)

    assert restored == normalize_source(text).text
    assert all(token not in restored for token in protected.tokens)


def test_an_inline_token_on_its_own_line_does_not_become_a_block() -> None:
    protected = _protected("$x$")
    markdown = flowmark_markdown(_identity_wrapper, _protected_source=protected)
    document = markdown.parse(protected.text)

    paragraph = cast(block.Paragraph, document.children[0])
    assert isinstance(paragraph.children[0], ProtectedInline)
    assert restore_source(markdown.render(document), protected) == "$x$\n"


def test_restoration_removes_only_a_parser_synthesized_block_prefix_blank() -> None:
    protected = _protected("Before\n$$\nbody\n$$\nAfter")
    token = protected.tokens[0]
    rendered = protected.text.replace(f"Before\n{token}", f"Before\n\n{token}")

    assert restore_source(rendered, protected) == "Before\n$$\nbody\n$$\nAfter\n"


def test_protected_code_supplies_immutable_context_to_cross_inline_rewrites() -> None:
    protected = _protected("The ``config``'s value and `` x ``'s type.")
    markdown = flowmark_markdown(_identity_wrapper, _protected_source=protected)
    document = markdown.parse(protected.text)

    rewrite_text_across_inlines(document, smart_quotes, protected_source=protected)
    restored = restore_source(markdown.render(document), protected)

    assert restored == "The ``config``’s value and `` x ``’s type.\n"


def test_restoration_fails_closed_for_missing_duplicate_reordered_and_unknown_tokens() -> None:
    protected = _protected("first $a$ then $b$")
    first, second = protected.tokens

    with pytest.raises(InvalidTokenError, match="missing"):
        restore_source(protected.text.replace(first, ""), protected)

    with pytest.raises(InvalidTokenError, match="duplicated"):
        restore_source(protected.text + first, protected)

    reordered = (
        protected.text.replace(first, "{FIRST}").replace(second, first).replace("{FIRST}", second)
    )
    with pytest.raises(InvalidTokenError, match="reordered"):
        restore_source(reordered, protected)

    unknown = protected.text.replace(first, encode_token(9))
    with pytest.raises(InvalidTokenError, match="reordered"):
        restore_source(unknown, protected)


def test_restoration_rejects_malformed_tokens_side_tables_and_block_newlines() -> None:
    inline = _protected("$a$")
    token = inline.tokens[0]
    malformed = inline.text.replace(token, token[:1] + "0" + token[2:])
    with pytest.raises(InvalidTokenError, match="token index"):
        restore_source(malformed, inline)

    with pytest.raises(InvalidTokenError, match="marker escape"):
        restore_source(ESCAPE_MARKER + "x" + inline.text, inline)

    with pytest.raises(InvalidTokenError, match="side table"):
        restore_source(inline.text, replace(inline, tokens=()))

    block = _protected("$$\nbody\n$$")
    without_structural_lf = block.text.removesuffix("\n")
    with pytest.raises(InvalidTokenError, match="structural LF"):
        restore_source(without_structural_lf, block)

    with pytest.raises(InvalidTokenError, match="line boundary"):
        restore_source("prefix" + block.text, block)
