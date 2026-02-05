"""Test strikethrough and tilde handling.

Tests that flowmark correctly distinguishes between:
- Actual GFM strikethrough: ~~text~~ or ~text~
- Literal tildes used as "approximately": ~60 seconds, ~130 words
"""

from flowmark.formats.flowmark_markdown import flowmark_markdown
from flowmark.linewrapping.markdown_filling import fill_markdown


def test_literal_tildes_before_numbers():
    """Tildes before numbers (meaning 'approximately') should be preserved as literal."""
    md = flowmark_markdown()

    result = md("Target: ~60 seconds, ~130 words total\n")
    assert result == "Target: ~60 seconds, ~130 words total\n"


def test_literal_tildes_not_converted_to_double():
    """The bug: ~60 seconds, ~130 should NOT become ~~60 seconds, ~~130."""
    result = fill_markdown("Target: ~60 seconds, ~130 words total")
    assert "~~" not in result
    assert result.strip() == "Target: ~60 seconds, ~130 words total"


def test_double_tilde_strikethrough():
    """Standard ~~strikethrough~~ should be preserved."""
    md = flowmark_markdown()

    result = md("This is ~~strikethrough~~ text\n")
    assert result == "This is ~~strikethrough~~ text\n"


def test_single_tilde_strikethrough():
    """Single-tilde ~strikethrough~ is valid GFM; flowmark normalizes to ~~double~~."""
    md = flowmark_markdown()

    result = md("This is ~strikethrough~ text\n")
    assert result == "This is ~~strikethrough~~ text\n"


def test_multiple_strikethroughs():
    """Multiple strikethrough spans in a single line."""
    md = flowmark_markdown()

    result = md("~one~ and ~two~ items\n")
    assert result == "~~one~~ and ~~two~~ items\n"


def test_single_tilde_no_closer():
    """A single tilde with no matching closer should remain literal."""
    md = flowmark_markdown()

    result = md("About ~50% of users\n")
    assert result == "About ~50% of users\n"


def test_tildes_with_space_before_closer():
    """Tildes where the 'closer' is preceded by whitespace should not be strikethrough."""
    md = flowmark_markdown()

    # The second ~ is preceded by a space, so it's not right-flanking and can't close.
    result = md("costs ~100 to ~200\n")
    assert result == "costs ~100 to ~200\n"


def test_tilde_space_after_opener():
    """A tilde followed by a space is not left-flanking, so no strikethrough."""
    md = flowmark_markdown()

    result = md("~ spaced ~\n")
    assert result == "~ spaced ~\n"


def test_tilde_space_before_closer():
    """A tilde preceded by a space is not right-flanking, so no strikethrough."""
    md = flowmark_markdown()

    result = md("~foo ~\n")
    assert result == "~foo ~\n"


def test_escaped_tildes_preserved():
    """Backslash-escaped tildes should remain escaped."""
    md = flowmark_markdown()

    result = md("Target: \\~60 seconds, \\~130 words total\n")
    assert result == "Target: \\~60 seconds, \\~130 words total\n"


def test_strikethrough_in_paragraph():
    """Strikethrough within a longer paragraph should be preserved during wrapping."""
    result = fill_markdown(
        "This paragraph has some ~~deleted text~~ in it and also mentions ~50 users."
    )
    assert "~~deleted text~~" in result
    assert "~50 users" in result
    # Make sure ~50 doesn't become ~~50
    assert "~~50" not in result
