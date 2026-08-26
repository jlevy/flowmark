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
from flowmark.preservation.bridge import (
    INDEX_END,
    INDEX_START,
    SENTINEL_END,
    SENTINEL_REPEAT,
    InvalidTokenError,
    choose_sentinel,
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


def test_sentinel_selection_skips_every_authored_candidate_run() -> None:
    source = (
        f"a{SENTINEL_REPEAT}{SENTINEL_END}b"
        f"c{SENTINEL_REPEAT * 3}{SENTINEL_END}d"
        f"e{SENTINEL_REPEAT * 2}x{SENTINEL_END}f"
    )

    sentinel = choose_sentinel(source)

    assert sentinel == SENTINEL_REPEAT * 4 + SENTINEL_END
    assert sentinel not in source


@pytest.mark.parametrize("index", [0, 1, 35, 36, 1295, 1296])
def test_token_encoding_is_canonical_lowercase_base36(index: int) -> None:
    sentinel = choose_sentinel("")
    token = encode_token(sentinel, index)

    assert parse_token(token, sentinel) == index


@pytest.mark.parametrize("digits", ["", "00", "01", "A", "-1", "１"])
def test_token_parser_rejects_noncanonical_indexes(digits: str) -> None:
    sentinel = choose_sentinel("")
    token = f"{sentinel}{INDEX_START}{digits}{INDEX_END}{sentinel}"

    with pytest.raises(InvalidTokenError, match="token index"):
        parse_token(token, sentinel)


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
    assert protected.sentinel not in restored


def test_an_inline_token_on_its_own_line_does_not_become_a_block() -> None:
    protected = _protected("$x$")
    markdown = flowmark_markdown(_identity_wrapper, _protected_source=protected)
    document = markdown.parse(protected.text)

    paragraph = cast(block.Paragraph, document.children[0])
    assert isinstance(paragraph.children[0], ProtectedInline)
    assert restore_source(markdown.render(document), protected) == "$x$\n"


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

    unknown = protected.text.replace(first, encode_token(protected.sentinel, 9))
    with pytest.raises(InvalidTokenError, match="reordered"):
        restore_source(unknown, protected)


def test_restoration_rejects_malformed_tokens_side_tables_and_block_newlines() -> None:
    inline = _protected("$a$")
    malformed = inline.text.replace(INDEX_START + "0" + INDEX_END, INDEX_START + "00" + INDEX_END)
    with pytest.raises(InvalidTokenError, match="token index"):
        restore_source(malformed, inline)

    with pytest.raises(InvalidTokenError, match="side table"):
        restore_source(inline.text, replace(inline, tokens=()))

    block = _protected("$$\nbody\n$$")
    without_structural_lf = block.text.removesuffix("\n")
    with pytest.raises(InvalidTokenError, match="structural LF"):
        restore_source(without_structural_lf, block)

    with pytest.raises(InvalidTokenError, match="line boundary"):
        restore_source("prefix" + block.text, block)
