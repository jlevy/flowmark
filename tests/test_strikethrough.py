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


# --- Tilde-in-parentheses bug (GFM punctuation flanking rules) ---


def test_tilde_before_and_inside_parens():
    """~100 (~200) must NOT be parsed as strikethrough.

    The closing ~ in '(~200)' is preceded by '(' (punctuation) and followed
    by '2' (word char), so it is NOT right-flanking per GFM spec.
    """
    md = flowmark_markdown()
    result = md("~100 (~200)\n")
    assert result == "~100 (~200)\n"


def test_tilde_before_and_inside_parens_fill():
    """Same bug through the full fill_markdown pipeline."""
    result = fill_markdown("~100 (~200)")
    assert "~~" not in result
    assert result.strip() == "~100 (~200)"


def test_tilde_only_inside_parens():
    """100 (~200) — tilde only inside parens should remain literal."""
    md = flowmark_markdown()
    result = md("100 (~200)\n")
    assert result == "100 (~200)\n"


def test_tilde_inside_parens_with_text():
    """~100 (x ~200) — tilde inside parens with intervening text stays literal."""
    md = flowmark_markdown()
    result = md("~100 (x ~200)\n")
    assert result == "~100 (x ~200)\n"


def test_tilde_in_parens_then_outside():
    """(~200) ~100 — tilde in parens then outside, both literal."""
    md = flowmark_markdown()
    result = md("(~200) ~100\n")
    assert result == "(~200) ~100\n"


def test_tilde_before_parens_no_tilde_inside():
    """~100 (200) — tilde before parens without tilde inside stays literal."""
    md = flowmark_markdown()
    result = md("~100 (200)\n")
    assert result == "~100 (200)\n"


def test_strikethrough_inside_parens():
    """(~~text~~) — valid double-tilde strikethrough inside parens is preserved."""
    md = flowmark_markdown()
    result = md("(~~text~~) end\n")
    assert result == "(~~text~~) end\n"


def test_strikethrough_after_punctuation():
    """Strikethrough after punctuation like quotes should still work.

    Opening ~ after '"' (punctuation) is left-flanking because it's preceded by
    punctuation. Closing ~ before '"' (punctuation) is right-flanking because
    it's followed by punctuation.
    """
    md = flowmark_markdown()
    result = md('"~~text~~" end\n')
    assert result == '"~~text~~" end\n'


def test_strikethrough_with_punctuation_content():
    """~~hello!~~ — strikethrough containing punctuation at end of content.

    Closing ~~ after '!' (punctuation) is right-flanking because the next
    char after ~~ is whitespace or end of string.
    """
    md = flowmark_markdown()
    result = md("~~hello!~~ end\n")
    assert result == "~~hello!~~ end\n"


def test_tilde_in_brackets():
    """~100 [~200] — tilde near square brackets, same flanking logic."""
    md = flowmark_markdown()
    result = md("~100 [~200]\n")
    # The [ before closing ~ is punctuation, followed by word char → not right-flanking
    # But also [~200] has no matching closer for the ~ so stays literal anyway.
    assert "~~" not in result
