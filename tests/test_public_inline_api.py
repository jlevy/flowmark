"""Tests for the public Markdown-inline API: flowmark.atomic_spans and flowmark.markdown_ast."""

from __future__ import annotations

from flowmark import Link, extract_links, flowmark_markdown
from flowmark.atomic_spans import (
    ATOMIC_PATTERNS,
    AUTOLINK,
    BARE_URL,
    INLINE_CODE_SPAN,
    MARKDOWN_INLINE_PATTERNS,
    MARKDOWN_LINK,
    AtomicPattern,
    iter_atomic_spans,
    iter_atomic_words,
    split_sentences_atomic,
    split_sentences_with_spans,
)
from flowmark.markdown_ast import walk_elements


def _parse(text: str):
    return flowmark_markdown().parse(text)


def test_atomic_pattern_constructs_with_name_and_pattern_only():
    p = AtomicPattern(name="x", pattern=r"foo")
    assert p.open_delim == "" and p.close_delim == "" and p.open_re == "" and p.close_re == ""


def test_markdown_inline_patterns_includes_links_and_urls():
    assert MARKDOWN_INLINE_PATTERNS == (INLINE_CODE_SPAN, MARKDOWN_LINK, AUTOLINK, BARE_URL)
    # Purpose-built, deliberately NOT a subset of the wrapping set.
    assert not set(MARKDOWN_INLINE_PATTERNS).issubset(set(ATOMIC_PATTERNS))


def test_autolink_pattern_matches_angle_url_and_email():
    import re

    pat = re.compile(AUTOLINK.pattern)
    assert pat.fullmatch("<http://example.com>")
    assert pat.fullmatch("<user@example.com>")


def test_bare_url_pattern_excludes_trailing_sentence_punctuation():
    import re

    pat = re.compile(BARE_URL.pattern)
    m = pat.search("Visit https://example.com. Next.")
    assert m is not None
    assert m.group(0) == "https://example.com"
    assert pat.search("see www.example.com/x").group(0) == "www.example.com/x"  # pyright: ignore[reportOptionalMemberAccess]


def test_extract_inline_link_with_title():
    doc = _parse('See [text](http://x.com "the title") here.\n')
    assert extract_links(doc) == [Link("text", "http://x.com", "the title")]


def test_extract_reference_link_resolves_destination():
    doc = _parse("See [text][r].\n\n[r]: http://ref.com\n")
    assert extract_links(doc) == [Link("text", "http://ref.com", None)]


def test_extract_collapsed_and_shortcut_references():
    doc = _parse("[r][] and [r].\n\n[r]: http://ref.com\n")
    assert [link.url for link in extract_links(doc)] == ["http://ref.com", "http://ref.com"]


def test_nested_inline_markup_in_link_text():
    doc = _parse("[**bold** and `code`](http://x.com)\n")
    links = extract_links(doc)
    assert len(links) == 1
    assert links[0].url == "http://x.com"
    assert "bold" in links[0].text and "code" in links[0].text


def test_escaped_brackets_are_not_a_link():
    doc = _parse("not a \\[link\\] here.\n")
    assert extract_links(doc) == []


def test_images_excluded_by_default_included_on_request():
    doc = _parse("![alt](img.png)\n")
    assert extract_links(doc) == []
    assert extract_links(doc, include_images=True) == [Link("alt", "img.png", None)]


def test_email_autolink_text_is_display_not_destination():
    doc = _parse("<user@example.com>\n")
    assert extract_links(doc) == [Link("user@example.com", "mailto:user@example.com", None)]


def test_empty_link_title_is_preserved_distinct_from_none():
    assert extract_links(_parse('[x](http://u "")\n')) == [Link("x", "http://u", "")]
    assert extract_links(_parse("[x](http://u)\n")) == [Link("x", "http://u", None)]


def test_angle_autolink_and_bare_url_extraction():
    doc = _parse("<http://auto.com> and https://bare.com/x\n")
    urls = [link.url for link in extract_links(doc)]
    assert "http://auto.com" in urls
    assert "https://bare.com/x" in urls
    assert extract_links(doc, include_autolinks=False) == []


def test_duplicate_link_text_yields_separate_links():
    doc = _parse("[go](http://1.com) and [go](http://2.com)\n")
    assert [link.url for link in extract_links(doc)] == ["http://1.com", "http://2.com"]


def test_link_syntax_inside_code_span_is_not_a_link():
    doc = _parse("`[notalink](x)` text\n")
    assert extract_links(doc) == []


def test_walk_elements_yields_code_block_text_but_extract_links_excludes_it():
    from marko import block

    doc = _parse("```\n[notalink](x)\n```\n")
    # The generic walk reaches the fenced code block...
    assert any(isinstance(el, block.FencedCode) for el in walk_elements(doc))
    # ...but no link is extracted from code-block content.
    assert extract_links(doc) == []


def test_walk_elements_is_read_only():
    doc = _parse("a [b](http://x.com) c\n")
    before = flowmark_markdown().render(doc)
    list(walk_elements(doc))
    assert flowmark_markdown().render(doc) == before


def test_iter_atomic_spans_round_trip_and_offsets():
    s = "See [a b](http://x.com) and `co de` end."
    spans = list(iter_atomic_spans(s))
    assert "".join(sp.text for sp in spans) == s
    assert all(s[sp.start : sp.end] == sp.text for sp in spans)
    assert [sp.text for sp in spans if sp.is_atomic] == ["[a b](http://x.com)", "`co de`"]


def test_atomic_span_name_distinguishes_link_from_code():
    s = "[a b](http://x.com) and `co de`"
    atomic = [sp for sp in iter_atomic_spans(s) if sp.is_atomic]
    assert [(sp.text, sp.name) for sp in atomic] == [
        ("[a b](http://x.com)", "markdown_link"),
        ("`co de`", "inline_code_span"),
    ]
    # Non-atomic gaps carry no name.
    assert all(sp.name is None for sp in iter_atomic_spans(s) if not sp.is_atomic)


def test_iter_atomic_spans_empty_patterns_yields_single_nonatomic_span():
    from flowmark.atomic_spans import AtomicSpan

    assert list(iter_atomic_spans("abc", patterns=())) == [AtomicSpan("abc", 0, 3, False)]
    assert list(iter_atomic_spans("", patterns=())) == []


def test_iter_atomic_words_glues_atomic_and_keeps_offsets():
    s = "foo[a](b)bar [click here](u) end"
    words = list(iter_atomic_words(s))
    assert [w.text for w in words] == ["foo[a](b)bar", "[click here](u)", "end"]
    assert all(s[w.start : w.end] == w.text for w in words)


def test_split_sentences_with_spans_are_verbatim():
    s = "This is one sentence. Here is the second one."
    spans = split_sentences_with_spans(s, min_length=0)
    assert all(s[sp.start : sp.end] == sp.text for sp in spans)
    assert [sp.text for sp in spans] == ["This is one sentence.", "Here is the second one."]


def test_sentence_span_never_bisects_a_link_with_spaces():
    s = "See [click here for info](http://x.com) now. Done with it."
    spans = split_sentences_with_spans(s, min_length=0)
    assert all(s[sp.start : sp.end] == sp.text for sp in spans)
    # The whole link stays inside a single sentence span (never split on its inner space).
    assert any("[click here for info](http://x.com)" in sp.text for sp in spans)


def test_split_sentences_atomic_does_not_break_inside_link_with_period():
    # "St." inside the link text must not end a sentence (it does with the plain splitter).
    s = "He attended [St. John's School](http://x.com) in England."
    assert split_sentences_atomic(s, min_length=0) == [s]
