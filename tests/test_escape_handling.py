"""Test smart escape handling - only preserve escapes when necessary."""

from flowmark.formats.flowmark_markdown import flowmark_markdown


def test_escape_in_heading():
    """Escapes in headings should be removed - they're never needed."""
    md = flowmark_markdown()

    # Period after number in heading
    result = md("## 1\\. Test Heading\n")
    assert result == "## 1. Test Heading\n\n"

    # Multiple escapes in heading
    result = md("### Item 1\\. and 2\\. in title\n")
    assert result == "### Item 1. and 2. in title\n\n"


def test_escape_at_paragraph_start():
    """Escape at paragraph start should be preserved to prevent list interpretation."""
    md = flowmark_markdown()

    # At start of paragraph - KEEP escape
    result = md("1\\. Not a list\n")
    assert result == "1\\. Not a list\n"

    # Multi-digit number
    result = md("10\\. Not a list either\n")
    assert result == "10\\. Not a list either\n"


def test_escape_in_paragraph_middle():
    """Escapes in middle of paragraph should be removed."""
    md = flowmark_markdown()

    # Period in middle of text
    result = md("Text with 1\\. in middle\n")
    assert result == "Text with 1. in middle\n"

    # Period at end of text
    result = md("End with number 1\\.\n")
    assert result == "End with number 1.\n"


def test_escape_in_list_item():
    """Test escape handling in list items."""
    md = flowmark_markdown()

    # In middle of list item - remove escape
    result = md("- List item 1\\. in middle\n")
    assert result == "- List item 1. in middle\n"

    # At start of list item - preserve escape
    result = md("- 1\\. At start of item\n")
    assert result == "- 1\\. At start of item\n"


def test_escape_in_quote():
    """Test escape handling in block quotes."""
    md = flowmark_markdown()

    # In middle of quote line - remove escape
    result = md("> Quote with 1\\. in middle\n")
    assert result == "> Quote with 1. in middle\n"

    # At start of quote content - preserve escape
    # Note: The "> " prefix comes first, so "1." is at line start
    result = md("> 1\\. Quote start\n")
    assert result == "> 1\\. Quote start\n"


def test_escape_in_table():
    """Escapes in table cells should be removed."""
    md = flowmark_markdown()

    result = md("""| Header | 1\\. Cell |
| --- | --- |
| 1\\. | Value 1\\. here |
""")

    expected = """| Header | 1. Cell |
| --- | --- |
| 1. | Value 1. here |
"""
    assert result == expected


def test_actual_list_no_escape():
    """Real lists without escapes should remain unchanged."""
    md = flowmark_markdown()

    result = md("1. First item\n2. Second item\n")
    assert result == "1. First item\n\n2. Second item\n"


def test_mixed_escapes():
    """Test document with mixed escape scenarios."""
    md = flowmark_markdown()

    input_md = """## 1\\. Heading

Paragraph with 1\\. in middle.

1\\. Start of paragraph

- List 1\\. middle
- 1\\. start

> 1\\. quote start
"""

    expected = """## 1. Heading

Paragraph with 1. in middle.

1\\. Start of paragraph

- List 1. middle

- 1\\. start

> 1\\. quote start
"""

    result = md(input_md)
    assert result == expected


def test_other_escaped_chars():
    r"""
    Test that other escaped characters are preserved (only periods are handled specially).

    Per CommonMark spec, any ASCII punctuation can be escaped: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
    We only intelligently handle periods - all other escapes are preserved as-is.
    """
    md = flowmark_markdown()

    # Asterisks - could create emphasis
    result = md("Test \\* not emphasis\n")
    assert result == "Test \\* not emphasis\n"

    # Hash - could create heading (at line start)
    result = md("Test \\# not heading\n")
    assert result == "Test \\# not heading\n"

    # Dollar signs - common in math expressions
    result = md("Cost is \\$420K\n")
    assert result == "Cost is \\$420K\n"

    # Hyphens - could create lists (at line start)
    result = md("Text with \\- hyphen\n")
    assert result == "Text with \\- hyphen\n"

    # Underscores - could create emphasis
    result = md("Text with \\_underscore\\_\n")
    assert result == "Text with \\_underscore\\_\n"

    # Brackets - could create links
    result = md("Text with \\[bracket\\]\n")
    assert result == "Text with \\[bracket\\]\n"

    # Backticks - could create code spans
    result = md("Text with \\` backtick\n")
    assert result == "Text with \\` backtick\n"


def test_escaped_chars_in_headings():
    """
    Test that non-period escaped characters in headings are preserved.

    While we remove period escapes from headings (they can't form lists),
    other characters might still have meaning or could be ambiguous,
    so we preserve their escapes.
    """
    md = flowmark_markdown()

    # Asterisk in heading - preserve escape
    result = md("## Test \\* Heading\n")
    assert result == "## Test \\* Heading\n\n"

    # Hash in heading - preserve escape
    result = md("## Test \\# Heading\n")
    assert result == "## Test \\# Heading\n\n"

    # Hyphen in heading - preserve escape
    result = md("## Test \\- Heading\n")
    assert result == "## Test \\- Heading\n\n"


def test_escaped_chars_at_line_start():
    """
    Test that escaped characters at line start are preserved.

    These escapes prevent the characters from being interpreted as:
    - * or - as bullet lists
    - # as headings
    - digits followed by . or ) as numbered lists
    """
    md = flowmark_markdown()

    # Asterisk at line start - would create bullet list
    result = md("\\* Not a list\n")
    assert result == "\\* Not a list\n"

    # Hyphen at line start - would create bullet list
    result = md("\\- Not a list\n")
    assert result == "\\- Not a list\n"

    # Hash at line start - would create heading
    result = md("\\# Not a heading\n")
    assert result == "\\# Not a heading\n"


def test_mixed_escapes_comprehensive():
    """
    Comprehensive test showing our escape handling policy:
    - Periods: smart handling (remove when unnecessary)
    - Other chars: preserve all escapes (conservative)
    """
    md = flowmark_markdown()

    input_md = """## 1\\. Heading with \\* asterisk

Text with 1\\. period and \\* asterisk and \\# hash.

1\\. Not a list (period escape kept)
\\* Not a list (asterisk escape kept)

Cost: \\$100 (dollar escape kept)
"""

    expected = """## 1. Heading with \\* asterisk

Text with 1. period and \\* asterisk and \\# hash.

1\\. Not a list (period escape kept) \\* Not a list (asterisk escape kept)

Cost: \\$100 (dollar escape kept)
"""

    result = md(input_md)
    assert result == expected
