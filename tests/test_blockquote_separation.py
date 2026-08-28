"""Adjacent blockquotes must stay separate blockquotes.

A blank line between two blockquotes makes them two `<blockquote>` elements. Dropping
that blank line merges them into one, which changes the rendered document.

The failure came from the blank-line bookkeeping: a heading records that it already
emitted a trailing blank line, `render_quote` then strips the quote's trailing newlines,
and the stale flag went on to swallow the document-level blank line separating this
quote from the next.
"""

import marko

from flowmark.formats.flowmark_markdown import flowmark_markdown


def _html(src: str) -> str:
    """Render markdown to HTML with stock marko, for semantic equivalence checks."""
    parser = marko.Markdown()
    return parser.render(parser.parse(src)).strip()


def test_quote_ending_in_heading_stays_separate_from_the_next_quote():
    md = flowmark_markdown()
    src = "> ### How Is This Different?\n\n> Pieces of this exist elsewhere.\n"
    out = md.convert(src)

    assert _html(src) == _html(out), out
    assert _html(out).count("<blockquote>") == 2, out


def test_adjacent_plain_quotes_stay_separate():
    md = flowmark_markdown()
    src = "> First quote.\n\n> Second quote.\n"
    out = md.convert(src)

    assert _html(src) == _html(out), out
    assert _html(out).count("<blockquote>") == 2, out


def test_quote_followed_by_a_paragraph_keeps_its_separation():
    md = flowmark_markdown()
    src = "> ### Heading\n\nOrdinary paragraph after the quote.\n"
    out = md.convert(src)

    assert _html(src) == _html(out), out


def test_adjacent_quotes_are_stable_across_passes():
    md = flowmark_markdown()
    src = "> ### How Is This Different?\n\n> Pieces of this exist elsewhere.\n"
    once = md.convert(src)
    assert md.convert(once) == once, once
