from textwrap import dedent

from flowmark.linewrapping.text_wrapping import (
    _HtmlMdWordSplitter,  # pyright: ignore
    get_html_md_word_splitter,
    markdown_escape_word,
    simple_word_splitter,
    wrap_paragraph,
    wrap_paragraph_lines,
)


def test_markdown_escape_word_function() -> None:
    # Cases that should be escaped
    assert markdown_escape_word("-") == "\\-"
    assert markdown_escape_word("+") == "\\+"
    assert markdown_escape_word("*") == "\\*"
    assert markdown_escape_word(">") == "\\>"
    assert markdown_escape_word("#") == "\\#"
    assert markdown_escape_word("##") == "\\##"
    assert markdown_escape_word("1.") == "1\\."
    assert markdown_escape_word("10.") == "10\\."
    assert markdown_escape_word("1)") == "1\\)"
    assert markdown_escape_word("99)") == "99\\)"

    # Cases that should NOT be escaped
    assert markdown_escape_word("word") == "word"
    assert markdown_escape_word("-word") == "-word"  # Starts with char, but not just char
    assert markdown_escape_word("word-") == "word-"  # Ends with char
    assert markdown_escape_word("#word") == "#word"
    assert markdown_escape_word("word#") == "word#"
    assert markdown_escape_word("1.word") == "1.word"
    assert markdown_escape_word("word1.") == "word1."
    assert markdown_escape_word("1)word") == "1)word"
    assert markdown_escape_word("word1)") == "word1)"
    assert markdown_escape_word("<tag>") == "<tag>"  # Other symbols
    assert markdown_escape_word("[link]") == "[link]"
    assert markdown_escape_word("1") == "1"  # Just number
    assert markdown_escape_word(".") == "."  # Just dot


def test_wrap_paragraph_lines_markdown_escaping():
    assert wrap_paragraph_lines(text="- word", width=10, is_markdown=True) == ["- word"]

    text = "word - word * word + word > word # word ## word 1. word 2) word"

    assert wrap_paragraph_lines(text=text, width=5, is_markdown=True) == [
        "word",
        "\\-",
        "word",
        "\\*",
        "word",
        "\\+",
        "word",
        "\\>",
        "word",
        "\\#",
        "word",
        "\\##",
        "word",
        "1\\.",
        "word",
        "2\\)",
        "word",
    ]
    assert wrap_paragraph_lines(text=text, width=10, is_markdown=True) == [
        "word -",
        "word *",
        "word +",
        "word >",
        "word #",
        "word ##",
        "word 1.",
        "word 2)",
        "word",
    ]
    assert wrap_paragraph_lines(text=text, width=15, is_markdown=True) == [
        "word - word *",
        "word + word >",
        "word # word ##",
        "word 1. word 2)",
        "word",
    ]
    assert wrap_paragraph_lines(text=text, width=20, is_markdown=True) == [
        "word - word * word +",
        "word > word # word",
        "\\## word 1. word 2)",
        "word",
    ]
    assert wrap_paragraph_lines(text=text, width=20, is_markdown=False) == [
        "word - word * word +",
        "word > word # word",
        "## word 1. word 2)",
        "word",
    ]

    test2 = """Testing - : Is Ketamine Contraindicated in Patients with Psychiatric Disorders? - REBEL EM - more words - accessed April 24, 2025, <https://rebelem.com/is-ketamine-contraindicated-in-patients-with-psychiatric-disorders/>"""
    assert wrap_paragraph_lines(text=test2, width=80, is_markdown=True) == [
        "Testing - : Is Ketamine Contraindicated in Patients with Psychiatric Disorders?",
        "\\- REBEL EM - more words - accessed April 24, 2025,",
        "<https://rebelem.com/is-ketamine-contraindicated-in-patients-with-psychiatric-disorders/>",
    ]


def test_smart_splitter():
    splitter = _HtmlMdWordSplitter()

    html_text = "This is <span class='test'>some text</span> and <a href='#'>this is a link</a>."
    assert splitter(html_text) == [
        "This",
        "is",
        "<span class='test'>some",
        "text</span>",
        "and",
        "<a href='#'>this",
        "is",
        "a",
        "link</a>.",
    ]

    md_text = "Here's a [Markdown link](https://example.com) and [another one](https://test.com)."
    assert splitter(md_text) == [
        "Here's",
        "a",
        "[Markdown link](https://example.com)",
        "and",
        "[another one](https://test.com).",
    ]

    mixed_text = "Text with <b>bold</b> and [a link](https://example.com)."
    assert splitter(mixed_text) == [
        "Text",
        "with",
        "<b>bold</b>",
        "and",
        "[a link](https://example.com).",
    ]


def test_wrap_text():
    sample_text = (
        "This is a sample text with a [Markdown link](https://example.com)"
        " and an <a href='#'>tag</a>. It should demonstrate the functionality of "
        "our enhanced text wrapping implementation."
    )

    print("\nFilled text with default splitter:")
    filled = wrap_paragraph(
        sample_text,
        word_splitter=simple_word_splitter,
        width=40,
        initial_indent=">",
        subsequent_indent=">>",
    )
    print(filled)
    filled_expected = dedent(
        """
        >This is a sample text with a [Markdown
        >>link](https://example.com) and an <a
        >>href='#'>tag</a>. It should
        >>demonstrate the functionality of our
        >>enhanced text wrapping implementation.
        """
    ).strip()

    print("\nFilled text with get_html_md_word_splitter():")
    filled_smart = wrap_paragraph(
        sample_text,
        word_splitter=get_html_md_word_splitter(),
        width=40,
        initial_indent=">",
        subsequent_indent=">>",
    )
    print(filled_smart)
    filled_smart_expected = dedent(
        """
        >This is a sample text with a
        >>[Markdown link](https://example.com)
        >>and an <a href='#'>tag</a>. It should
        >>demonstrate the functionality of our
        >>enhanced text wrapping implementation.
        """
    ).strip()

    print("\nFilled text with get_html_md_word_splitter() and initial_offset:")
    filled_smart_offset = wrap_paragraph(
        sample_text,
        word_splitter=get_html_md_word_splitter(),
        width=40,
        initial_indent=">",
        subsequent_indent=">>",
        initial_column=35,
    )
    print(filled_smart_offset)
    filled_smart_offset_expected = dedent(
        """
        This
        >>is a sample text with a
        >>[Markdown link](https://example.com)
        >>and an <a href='#'>tag</a>. It should
        >>demonstrate the functionality of our
        >>enhanced text wrapping implementation.
        """
    ).strip()

    assert filled == filled_expected
    assert filled_smart == filled_smart_expected
    assert filled_smart_offset == filled_smart_offset_expected


def test_wrap_width():
    text = dedent(
        """
        You may also simply ask a question and the kmd assistant will help you. Press
        `?` or just press space twice, then write your question or request. Press `?` and
        tab to get suggested questions.
        """
    ).strip()
    width = 80
    wrapped = wrap_paragraph_lines(text, width=width)
    print(wrapped)
    print([len(line) for line in wrapped])
    assert all(len(line) <= width for line in wrapped)


def test_line_wrap_to_width_with_markdown_breaks():
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    # Get a markdown-aware line wrapper
    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Test trailing space line breaks
    text_with_spaces = "This line ends with spaces  \nThis is a new line"
    wrapped_spaces = wrapper(text_with_spaces, initial_indent="", subsequent_indent="")
    assert wrapped_spaces == "This line ends with spaces\\\nThis is a new line"

    # Test backslash line breaks
    text_with_backslash = "This line ends with backslash\\\nThis is a new line"
    wrapped_backslash = wrapper(text_with_backslash, initial_indent="", subsequent_indent="")
    assert wrapped_backslash == "This line ends with backslash\\\nThis is a new line"

    # Test wrapping with indentation
    indented_wrapper = line_wrap_to_width(width=40, is_markdown=True)
    long_text = (
        "This is a very long line that will be wrapped and it ends with a line break  \n"
        "Next line with content that continues"
    )
    wrapped_long = indented_wrapper(long_text, initial_indent="  ", subsequent_indent="    ")
    assert wrapped_long == (
        "  This is a very long line that will be\n"
        "    wrapped and it ends with a line\n"
        "    break\\\n"
        "    Next line with content that\n"
        "    continues"
    )

    # Test different indentation for segments
    mixed_indent_wrapper = line_wrap_to_width(width=30, is_markdown=True)
    mixed_indent_text = "First segment  \nSecond segment\\\nThird segment"
    wrapped_mixed_indent = mixed_indent_wrapper(
        mixed_indent_text, initial_indent="* ", subsequent_indent="  "
    )
    assert wrapped_mixed_indent == ("* First segment\\\n  Second segment\\\n  Third segment")

    # Test empty segments
    empty_segment_text = "Before  \n\\\nAfter"
    wrapped_empty = wrapper(empty_segment_text, initial_indent="", subsequent_indent="")
    assert wrapped_empty == "Before\\\n\\\nAfter"

    # Test single segment (no line breaks)
    single_segment = "Text with no breaks"
    wrapped_single = wrapper(single_segment, initial_indent="> ", subsequent_indent="  ")
    assert wrapped_single == "> Text with no breaks"


def test_template_tag_splitter():
    """Test that template tags (Markdoc/Jinja/Nunjucks) are kept as atomic tokens."""
    splitter = _HtmlMdWordSplitter()

    # Markdoc-style tags: {% tag %}
    markdoc_text = "Text with {% if $condition %} template tags {% endif %} here."
    result = splitter(markdoc_text)
    assert "{% if $condition %}" in result
    assert "{% endif %}" in result

    # Self-closing Markdoc tags: {% tag /%}
    self_closing = "Include {% partial file='header.md' /%} here."
    result = splitter(self_closing)
    assert "{% partial file='header.md' /%}" in result

    # Jinja/Nunjucks comments: {# comment #}
    comment_text = "Text with {# this is a comment #} inline."
    result = splitter(comment_text)
    assert "{# this is a comment #}" in result

    # Jinja/Nunjucks variables: {{ variable }}
    variable_text = "Hello {{ user.name }} welcome."
    result = splitter(variable_text)
    assert "{{ user.name }}" in result

    # Complex Markdoc tag with attributes
    complex_tag = "Use {% callout type='warning' title='Note' %} for emphasis."
    result = splitter(complex_tag)
    assert "{% callout type='warning' title='Note' %}" in result

    # Multiple template tags in sequence (with spaces between)
    multi_tag = "{% if $a %} {% if $b %}nested{% /if %} {% /if %}"
    result = splitter(multi_tag)
    # Tags should be kept together
    assert "{% if $a %}" in result
    assert "{% /if %}" in result


def test_template_tag_wrapping():
    """Test that template tags don't break across lines during wrapping."""

    # Template tag should stay together even if it's long
    text_with_tag = "Some text {% callout type='warning' %} more text after the tag."
    result = wrap_paragraph_lines(text=text_with_tag, width=30, is_markdown=True)

    # The tag should not be split across lines
    full_result = " ".join(result)
    assert "{% callout type='warning' %}" in full_result

    # Jinja variable should stay together
    text_with_var = "Hello {{ user.first_name }} and welcome to the site."
    result = wrap_paragraph_lines(text=text_with_var, width=25, is_markdown=True)
    full_result = " ".join(result)
    assert "{{ user.first_name }}" in full_result

    # Comment should stay together
    text_with_comment = "Text {# TODO: fix this later #} and more text here."
    result = wrap_paragraph_lines(text=text_with_comment, width=20, is_markdown=True)
    full_result = " ".join(result)
    assert "{# TODO: fix this later #}" in full_result


def test_mixed_html_and_template_tags():
    """Test that HTML tags and template tags work together."""
    splitter = _HtmlMdWordSplitter()

    mixed = "Text <span class='x'>html</span> and {% if $y %} template {% endif %} here."
    result = splitter(mixed)

    # HTML should be coalesced
    assert "<span class='x'>html</span>" in result
    # Template tags should be kept together
    assert "{% if $y %}" in result
    assert "{% endif %}" in result


def test_long_template_tags():
    """Test that tags with many attributes (10+ words) are kept together."""
    splitter = _HtmlMdWordSplitter()

    # 10-word template tag
    long_tag = "{% component name='widget' type='button' size='large' color='blue' disabled=true %}"
    text = f"Before {long_tag} after."
    result = splitter(text)
    assert long_tag in result

    # 12-word template tag (at the limit)
    very_long_tag = (
        "{% table columns=[a, b, c] rows=[1, 2, 3] border=true striped=true hover=true %}"
    )
    text = f"Before {very_long_tag} after."
    result = splitter(text)
    assert very_long_tag in result


def test_long_html_tags():
    """Test that HTML tags with many attributes are kept together."""
    splitter = _HtmlMdWordSplitter()

    # Long HTML tag with many attributes
    long_html = (
        "<div class='container' id='main' data-value='test' style='color: red'>content</div>"
    )
    text = f"Before {long_html} after."
    result = splitter(text)
    assert long_html in result


def test_long_jinja_comments():
    """Test that long Jinja comments are kept together."""
    splitter = _HtmlMdWordSplitter()

    # Long comment with many words (12 words = MAX_TAG_WORDS)
    long_comment = "{# This is a long comment that spans many words here #}"
    text = f"Before {long_comment} after."
    result = splitter(text)
    assert long_comment in result


def test_inline_code_with_spaces():
    """Test that inline code spans with spaces are kept together."""
    splitter = _HtmlMdWordSplitter()

    # Simple inline code with spaces
    code = "`code with spaces`"
    text = f"Some {code} here."
    result = splitter(text)
    assert code in result

    # Inline code with HTML-like content
    code2 = "`<!-- not a real comment -->`"
    text2 = f"Check {code2} for details."
    result2 = splitter(text2)
    assert code2 in result2


def test_inline_code_with_surrounding_punctuation():
    """Test that inline code with surrounding punctuation stays together."""
    splitter = _HtmlMdWordSplitter()

    # Inline code with parentheses
    text = "syntax (`<!--% ... -->`)**"
    result = splitter(text)
    assert "(`<!--% ... -->`)**" in result

    # Inline code followed by punctuation
    text2 = "Use `foo bar`."
    result2 = splitter(text2)
    assert "`foo bar`." in result2


def test_html_comments_kept_together():
    """Test that HTML comments are kept as atomic units."""
    splitter = _HtmlMdWordSplitter()

    # Simple HTML comment
    comment = "<!-- a comment -->"
    text = f"Text with {comment} inline."
    result = splitter(text)
    assert comment in result

    # Longer HTML comment
    long_comment = "<!-- this is a longer comment with more words -->"
    text2 = f"Before {long_comment} after."
    result2 = splitter(text2)
    assert long_comment in result2


def test_single_word_inline_code_not_coalesced():
    """
    Test that single-word inline code spans do NOT incorrectly coalesce with following text.

    Regression test for bug where `getRequiredEnv()` would be coalesced with words
    following it, causing incorrect line breaks before the inline code.
    """
    splitter = _HtmlMdWordSplitter()

    # Single-word inline code should stay as one word, not coalesce with following text
    text = "access env vars via `getRequiredEnv()` and must live in files"
    result = splitter(text)

    # The backticked code should be its own separate token
    assert "`getRequiredEnv()`" in result

    # Find the token containing the inline code
    code_token = next(r for r in result if "`getRequiredEnv()`" in r)
    # It should be EXACTLY the inline code, not merged with other words
    assert code_token == "`getRequiredEnv()`", f"Expected exact match, got {code_token!r}"

    # "and" should be a separate word
    assert "and" in result


def test_multiple_single_word_inline_codes():
    """
    Test text with multiple single-word inline code spans.
    """
    splitter = _HtmlMdWordSplitter()

    text = 'via `getRequiredEnv()` and must live in files with `"use node"`.'
    result = splitter(text)

    # Each inline code should be separate
    assert "`getRequiredEnv()`" in result
    # The second code span with quotes should be handled correctly too
    # Note: this has internal spaces so may be multiple words, but should not
    # incorrectly coalesce with "via" or "and"
    assert "via" in result
    assert "and" in result


def test_inline_code_in_table_cells():
    """
    Test that inline code in table cell content is tokenized correctly.

    Tables are parsed by Marko as special blocks and don't go through line
    wrapping, but the word splitter should still handle table cell content
    correctly if it's ever processed.
    """
    splitter = _HtmlMdWordSplitter()

    # Typical table cell with inline code
    cell1 = "the field is `runId: v.id('experimentRuns')` or maybe `foo`?"
    result1 = splitter(cell1)
    # Single-word code spans should be separate tokens
    assert "`foo`?" in result1 or any("`foo`" in r for r in result1)
    # Code without spaces stays as one token
    assert "`runId: v.id('experimentRuns')`" in result1

    # Simple code-only cell
    cell2 = "`detailedLogs`"
    result2 = splitter(cell2)
    assert result2 == ["`detailedLogs`"]

    # Cell with multiple code spans
    cell3 = "`a` and `b` and `c`"
    result3 = splitter(cell3)
    assert "`a`" in result3
    assert "`b`" in result3
    assert "`c`" in result3
    assert "and" in result3


def test_newline_after_opening_tag():
    """
    Test that newlines after opening Jinja/Markdoc tags are preserved.

    When a tag is followed by a newline, the content should start on a new line.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_by_sentence, line_wrap_to_width

    # Test with line_wrap_to_width
    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Opening tag followed by newline and content
    text = "{% description ref='example' %}\nThis is content after the tag."
    result = wrapper(text, "", "")
    # The newline after the tag should be preserved
    assert "{% description ref='example' %}\n" in result or result.startswith(
        "{% description ref='example' %}\n"
    )

    # HTML comment tag followed by newline
    text2 = "<!-- f:description ref='example' -->\nContent after HTML comment tag."
    result2 = wrapper(text2, "", "")
    assert "<!-- f:description ref='example' -->\n" in result2

    # Test with line_wrap_by_sentence
    wrapper2 = line_wrap_by_sentence(width=80, is_markdown=True)
    result3 = wrapper2(text, "", "")
    assert "{% description ref='example' %}\n" in result3


def test_newline_before_closing_tag():
    """
    Test that newlines before closing Jinja/Markdoc tags are preserved.

    When a closing tag is preceded by a newline, it should stay on its own line.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Content followed by newline and closing tag
    text = "Some content here.\n{% /description %}"
    result = wrapper(text, "", "")
    # The closing tag should be on its own line
    assert "\n{% /description %}" in result

    # HTML comment closing tag
    text2 = "Some content.\n<!-- /f:description -->"
    result2 = wrapper(text2, "", "")
    assert "\n<!-- /f:description -->" in result2


def test_paired_tags_not_broken():
    """
    Test that paired tags on the same line stay together during wrapping.

    Common pattern: {% field %}{% /field %} for empty fields.
    """
    splitter = _HtmlMdWordSplitter()

    # Paired Jinja tags - the opening+closing pair is kept as a single token
    paired = "{% field kind='string' id='email' %}{% /field %}"
    text = f"Some text before {paired} and after."
    result = splitter(text)
    # The pair is kept together as a single token (with normalized space between)
    full_result = " ".join(result)
    assert "{% field kind='string' id='email' %}" in full_result
    assert "{% /field %}" in full_result

    # HTML comment paired tags - kept together as a single token
    paired_html = "<!-- f:field kind='string' --><!-- /f:field -->"
    text2 = f"Before {paired_html} after."
    result2 = splitter(text2)
    full_result2 = " ".join(result2)
    assert "<!-- f:field kind='string' -->" in full_result2
    assert "<!-- /f:field -->" in full_result2

    # Wrapping should not break either tag in a pair
    long_text = f"This is a longer piece of text with {paired} embedded in the middle."
    wrapped = wrap_paragraph_lines(text=long_text, width=40, is_markdown=True)
    full_result = " ".join(wrapped)
    # Both tags should be intact (not broken across lines)
    assert "{% field kind='string' id='email' %}" in full_result
    assert "{% /field %}" in full_result


def test_nested_tags_newlines_preserved():
    """
    Test that newlines between nested tags are preserved.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Nested structure with newlines
    text = "{% form id='test' %}\n{% group id='section' %}\n{% field id='name' %}{% /field %}\n{% /group %}\n{% /form %}"
    result = wrapper(text, "", "")

    # Each tag should be on its own line
    assert "{% form id='test' %}\n" in result
    assert "\n{% group id='section' %}\n" in result
    assert "\n{% /group %}\n" in result
    assert "\n{% /form %}" in result


def test_backslash_in_tag_attributes():
    r"""
    Test that backslashes in tag attribute values are preserved.

    Common case: regex patterns like pattern="^[^@]+\.[^@]+$"
    """
    splitter = _HtmlMdWordSplitter()

    # Tag with regex pattern containing backslash
    tag_with_backslash = r"{% field pattern='^[^@]+\.[^@]+$' %}"
    text = f"Use {tag_with_backslash} for email."
    result = splitter(text)

    # The backslash should be preserved
    assert tag_with_backslash in result

    # In wrapped output
    wrapped = wrap_paragraph_lines(text=text, width=80, is_markdown=True)
    full_result = " ".join(wrapped)
    assert r"\." in full_result


def test_tag_with_list_items():
    """
    Test that tags containing lists don't merge with list items.

    The closing tag should stay on its own line, not merge with last list item.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Simulating what happens when a paragraph contains tag + list + closing tag
    # Note: In real Markdown, lists are separate blocks, but we test the wrapping behavior
    text = "- Option A {% #option_a %}\n{% /field %}"
    result = wrapper(text, "", "")

    # The closing tag should NOT be merged onto the list item line
    assert "\n{% /field %}" in result


def test_block_heuristics_table_rows():
    """
    Test that table rows inside tags have their newlines preserved.

    Block heuristics should:
    - Preserve newline after opening tag before table
    - Preserve newlines between table rows
    - Preserve newline after table before closing tag
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Table inside tags WITHOUT blank lines (tests block heuristics)
    text = "{% field %}\n| A | B |\n|---|---|\n| 1 | 2 |\n{% /field %}"
    result = wrapper(text, "", "")

    # Each table row should be on its own line
    assert "{% field %}\n" in result
    assert "\n| A | B |\n" in result
    assert "\n|---|---|\n" in result
    assert "\n| 1 | 2 |\n" in result
    assert "\n{% /field %}" in result


def test_table_rows_preserved_without_tags():
    """
    Test that table rows are preserved on their own lines even without tags.

    Table rows (lines starting with |) are structural markdown elements that must
    never be line-wrapped, regardless of whether template tags are present.
    This prevents the bug where Marko parses a table adjacent to paragraph text
    as a single paragraph, and the line wrapper then breaks the table row.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Table rows after paragraph text (no tags) — each row stays on its own line
    text = "Some text\n| A | B | C |\n|---|---|---|\n| 1 | 2 | 3 |"
    result = wrapper(text, "", "")

    assert "Some text\n" in result
    assert "\n| A | B | C |\n" in result
    assert "\n|---|---|---|\n" in result
    assert "| 1 | 2 | 3 |" in result


def test_wide_table_rows_not_wrapped():
    """
    Test that table rows wider than the wrap width are NOT broken across lines.

    This is the core issue from GitHub #36: a wide table header exceeding the
    wrap width was being broken mid-cell by the line wrapper.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=88, is_markdown=True)

    wide_header = "| Quarter | Revenue ($M) | YoY % | QoQ % | Segment A % | Segment B % | Geo: US % | Geo: Intl % |"
    separator = "|---------|-------------|-------|-------|-------------|-------------|-----------|-------------|"
    data_row = "| Q1 2025 | 125.3 | +12% | +3% | 45% | 55% | 60% | 40% |"

    # Wide table after paragraph text (the exact reproduction case from #36)
    text = f"Paragraph text here.\n{wide_header}\n{separator}\n{data_row}"
    result = wrapper(text, "", "")

    # Each table row must remain on a single line, not wrapped
    assert wide_header in result
    assert separator in result
    assert data_row in result
    # Verify they're each on their own line
    result_lines = result.split("\n")
    assert any(line == wide_header for line in result_lines)
    assert any(line == separator for line in result_lines)
    assert any(line == data_row for line in result_lines)


def test_table_rows_with_semantic_wrapping():
    """
    Test that table rows are preserved with semantic (sentence-based) wrapping.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_by_sentence

    wrapper = line_wrap_by_sentence(width=88, min_line_len=40, is_markdown=True)

    wide_header = "| Quarter | Revenue ($M) | YoY % | QoQ % | Segment A % | Segment B % | Geo: US % | Geo: Intl % |"
    separator = "|---------|-------------|-------|-------|-------------|-------------|-----------|-------------|"
    data_row = "| Q1 2025 | 125.3 | +12% | +3% | 45% | 55% | 60% | 40% |"

    text = f"Paragraph text. Another sentence here.\n{wide_header}\n{separator}\n{data_row}"
    result = wrapper(text, "", "")

    # Table rows must not be wrapped even in semantic mode
    assert wide_header in result
    assert separator in result
    assert data_row in result


def test_table_rows_only_no_surrounding_text():
    """
    Test that table-only content (no surrounding text, no tags) is preserved.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=40, is_markdown=True)

    # Just table rows, no surrounding text
    text = "| A long header | Another long header |\n|---|---|\n| Cell data | More cell data |"
    result = wrapper(text, "", "")

    assert "| A long header | Another long header |" in result
    assert "|---|---|" in result
    assert "| Cell data | More cell data |" in result


def test_block_heuristics_list_items():
    """
    Test that list items inside tags have their newlines preserved.

    Block heuristics should preserve newlines around list items when tags present.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # List inside tags WITHOUT blank lines (tests block heuristics)
    text = "{% field %}\n- Item 1\n- Item 2\n- Item 3\n{% /field %}"
    result = wrapper(text, "", "")

    # Each list item should be on its own line
    assert "{% field %}\n" in result
    assert "\n- Item 1\n" in result
    assert "\n- Item 2\n" in result
    assert "\n- Item 3\n" in result
    assert "\n{% /field %}" in result


def test_block_heuristics_only_with_tags_for_lists():
    """
    Test that list heuristics only apply when tags are present.

    Normal markdown text with lists should NOT have list items treated as
    segment boundaries. Table rows, however, are ALWAYS preserved on their
    own lines since they are structural markdown elements.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # List WITHOUT tags - list items should NOT be treated as segment boundaries
    text = "Some text\n- list item\nMore text"
    result = wrapper(text, "", "")

    # Without tags, list items are merged with surrounding text
    assert "- list item" in result
    # The list item might be merged with surrounding text (no segment break)
    assert "\n- list item\n" not in result

    # Table WITHOUT tags - table rows ARE still preserved as segment boundaries
    text = "Some text\n| A | B |\nMore text"
    result = wrapper(text, "", "")

    # Table rows are always preserved on their own line
    assert "\n| A | B |\n" in result


def test_block_heuristics_mixed_content():
    """
    Test block heuristics with mixed content (text + block elements).
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Mixed content: text, table, more text, all inside tags
    text = (
        "{% field %}\nIntro text here.\n| Col1 | Col2 |\n|------|------|\nOutro text.\n{% /field %}"
    )
    result = wrapper(text, "", "")

    # Opening tag preserved
    assert "{% field %}\n" in result
    # Table rows should each be on own line
    assert "\n| Col1 | Col2 |\n" in result
    assert "\n|------|------|\n" in result
    # Closing tag preserved
    assert "\n{% /field %}" in result


def test_block_heuristics_blank_line_normalization():
    """
    Test that block content between tags gets exactly one blank line at boundaries.

    This ensures:
    - One blank line after opening tag before list/table
    - One blank line after list/table before closing tag

    This prevents CommonMark lazy continuation from merging tags into blocks.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # List between tags - should get blank lines around it
    text = "{% field %}\n- Item 1\n- Item 2\n{% /field %}"
    result = wrapper(text, "", "")

    # Verify blank line after opening tag (two newlines = blank line)
    assert "{% field %}\n\n" in result, f"Expected blank line after opening tag, got: {result}"

    # Verify blank line before closing tag
    assert "\n\n{% /field %}" in result, f"Expected blank line before closing tag, got: {result}"


def test_block_heuristics_table_blank_lines():
    """
    Test blank line normalization specifically for tables.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Table between tags
    text = "{% field %}\n| A | B |\n|---|---|\n{% /field %}"
    result = wrapper(text, "", "")

    # Should have blank lines around table
    assert "{% field %}\n\n" in result
    assert "\n\n{% /field %}" in result


def test_block_heuristics_preserves_existing_blank_lines():
    """
    Test that if there are already blank lines, we don't add extras.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Already has blank lines
    text = "{% field %}\n\n- Item 1\n\n{% /field %}"
    result = wrapper(text, "", "")

    # Should still have exactly one blank line (not doubled)
    # Note: the wrapper may normalize, so we just check it's not more than 2 newlines
    assert "{% field %}\n\n" in result
    lines = result.split("\n")
    # Count consecutive empty lines - should not exceed 1
    max_consecutive_empty = 0
    current_consecutive = 0
    for line in lines:
        if line.strip() == "":
            current_consecutive += 1
            max_consecutive_empty = max(max_consecutive_empty, current_consecutive)
        else:
            current_consecutive = 0
    assert max_consecutive_empty <= 1, f"Too many consecutive blank lines: {result}"


def test_self_closing_jinja_tags():
    """
    Test self-closing Jinja tags (tags without a separate closing tag).

    Examples: {% break %}, {% continue %}, {% include "file" %}, {% set x = 1 %}
    These should be kept atomic and preserve newlines around them.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Self-closing tag on its own line
    text = "Some content.\n{% break %}\nMore content."
    result = wrapper(text, "", "")
    assert "\n{% break %}\n" in result

    # Self-closing tag with attributes
    text2 = "Before.\n{% include 'header.html' %}\nAfter."
    result2 = wrapper(text2, "", "")
    assert "\n{% include 'header.html' %}\n" in result2

    # Multiple self-closing tags
    text3 = "{% set x = 1 %}\n{% set y = 2 %}\n{% set z = 3 %}"
    result3 = wrapper(text3, "", "")
    assert "{% set x = 1 %}\n" in result3
    assert "\n{% set y = 2 %}\n" in result3
    assert "\n{% set z = 3 %}" in result3

    # Self-closing tag inline with text (should stay together)
    splitter = _HtmlMdWordSplitter()
    inline = "Use {% include 'partial.html' %} to include."
    tokens = splitter(inline)
    assert "{% include 'partial.html' %}" in tokens


def test_self_closing_html_comment_tags():
    """
    Test self-closing HTML comment tags (comments without a closing counterpart).

    Examples: <!-- note -->, <!-- TODO: fix this -->, <!-- @annotation -->
    These should be kept atomic and preserve newlines around them.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Self-closing comment on its own line
    text = "Some content.\n<!-- note: important -->\nMore content."
    result = wrapper(text, "", "")
    assert "\n<!-- note: important -->\n" in result

    # Comment with longer content
    text2 = "Before.\n<!-- TODO: refactor this section later -->\nAfter."
    result2 = wrapper(text2, "", "")
    assert "\n<!-- TODO: refactor this section later -->\n" in result2

    # Multiple self-closing comments
    text3 = "<!-- start -->\nContent here.\n<!-- end -->"
    result3 = wrapper(text3, "", "")
    assert "<!-- start -->\n" in result3
    assert "\n<!-- end -->" in result3

    # Self-closing comment inline (should stay together)
    splitter = _HtmlMdWordSplitter()
    inline = "See <!-- ref: section 3 --> for details."
    tokens = splitter(inline)
    assert "<!-- ref: section 3 -->" in tokens


def test_self_closing_jinja_variable_tags():
    """
    Test Jinja variable tags {{ ... }} which are always self-closing.

    Examples: {{ name }}, {{ user.email }}, {{ items | length }}
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Variable tag on its own line
    text = "Name:\n{{ user.name }}\nEmail:"
    result = wrapper(text, "", "")
    assert "\n{{ user.name }}\n" in result

    # Variable tag with filter
    text2 = "Count:\n{{ items | length }}\nDone."
    result2 = wrapper(text2, "", "")
    assert "\n{{ items | length }}\n" in result2

    # Variable inline (should stay together)
    splitter = _HtmlMdWordSplitter()
    inline = "Hello {{ name }}, welcome!"
    tokens = splitter(inline)
    assert "{{ name }}," in tokens or "{{ name }}" in tokens


def test_self_closing_jinja_comment_tags():
    """
    Test Jinja comment tags {# ... #} which are always self-closing.

    Examples: {# TODO #}, {# This is a comment #}
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Comment tag on its own line
    text = "Code here.\n{# TODO: optimize this #}\nMore code."
    result = wrapper(text, "", "")
    assert "\n{# TODO: optimize this #}\n" in result

    # Comment inline (should stay together)
    splitter = _HtmlMdWordSplitter()
    inline = "Value {# in bytes #} is 1024."
    tokens = splitter(inline)
    assert "{# in bytes #}" in tokens


def test_adjacent_jinja_tags_no_space():
    """
    Test that adjacent Jinja tags stay adjacent (no space inserted).

    When tags like %}{% are adjacent, normalization adds a space for tokenization,
    but denormalization must remove it in the final output.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_by_sentence, line_wrap_to_width
    from flowmark.linewrapping.tag_handling import (
        denormalize_adjacent_tags,
        normalize_adjacent_tags,
    )

    # Test normalize/denormalize directly
    original = "{% field kind='string' %}{% /field %}"
    normalized = normalize_adjacent_tags(original)
    assert normalized == "{% field kind='string' %} {% /field %}", (
        f"Expected space, got: {normalized}"
    )
    denormalized = denormalize_adjacent_tags(normalized)
    assert denormalized == original, f"Expected {original}, got: {denormalized}"

    # Test with line_wrap_to_width (uses wrap_paragraph)
    wrapper1 = line_wrap_to_width(width=80, is_markdown=True)
    result1 = wrapper1(original, "", "")
    assert result1 == original, f"line_wrap_to_width: Expected {original}, got: {result1}"

    # Test with line_wrap_by_sentence (uses wrap_paragraph_lines)
    wrapper2 = line_wrap_by_sentence(width=80, is_markdown=True)
    result2 = wrapper2(original, "", "")
    assert result2 == original, f"line_wrap_by_sentence: Expected {original}, got: {result2}"


def test_adjacent_html_comment_tags_no_space():
    """
    Test that adjacent HTML comment tags stay adjacent (no space inserted).

    This is critical for Markform-style HTML comment syntax.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_by_sentence, line_wrap_to_width
    from flowmark.linewrapping.tag_handling import (
        denormalize_adjacent_tags,
        normalize_adjacent_tags,
    )

    # Test normalize/denormalize directly
    original = '<!-- f:field kind="string" id="name" --><!-- /f:field -->'
    normalized = normalize_adjacent_tags(original)
    assert " <!-- /f:field -->" in normalized, (
        f"Expected space after normalization, got: {normalized}"
    )
    denormalized = denormalize_adjacent_tags(normalized)
    assert denormalized == original, f"Expected {original}, got: {denormalized}"

    # Test with line_wrap_to_width
    wrapper1 = line_wrap_to_width(width=80, is_markdown=True)
    result1 = wrapper1(original, "", "")
    assert result1 == original, f"line_wrap_to_width: Expected {original}, got: {result1}"

    # Test with line_wrap_by_sentence
    wrapper2 = line_wrap_by_sentence(width=80, is_markdown=True)
    result2 = wrapper2(original, "", "")
    assert result2 == original, f"line_wrap_by_sentence: Expected {original}, got: {result2}"


def test_adjacent_jinja_variable_tags_no_space():
    """
    Test that adjacent Jinja variable tags stay adjacent.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_by_sentence
    from flowmark.linewrapping.tag_handling import (
        denormalize_adjacent_tags,
        normalize_adjacent_tags,
    )

    original = "{{ a }}{{ b }}"
    normalized = normalize_adjacent_tags(original)
    assert normalized == "{{ a }} {{ b }}", f"Expected space, got: {normalized}"
    denormalized = denormalize_adjacent_tags(normalized)
    assert denormalized == original, f"Expected {original}, got: {denormalized}"

    wrapper = line_wrap_by_sentence(width=80, is_markdown=True)
    result = wrapper(original, "", "")
    assert result == original, f"Expected {original}, got: {result}"


def test_adjacent_jinja_comment_tags_no_space():
    """
    Test that adjacent Jinja comment tags stay adjacent.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_by_sentence
    from flowmark.linewrapping.tag_handling import (
        denormalize_adjacent_tags,
        normalize_adjacent_tags,
    )

    original = "{# first #}{# second #}"
    normalized = normalize_adjacent_tags(original)
    assert normalized == "{# first #} {# second #}", f"Expected space, got: {normalized}"
    denormalized = denormalize_adjacent_tags(normalized)
    assert denormalized == original, f"Expected {original}, got: {denormalized}"

    wrapper = line_wrap_by_sentence(width=80, is_markdown=True)
    result = wrapper(original, "", "")
    assert result == original, f"Expected {original}, got: {result}"


def test_adjacent_tags_full_pipeline():
    """
    Test adjacent tags through the full Markdown processing pipeline.

    This catches bugs where normalization happens but denormalization doesn't.
    """
    from flowmark import fill_markdown

    # Jinja tags
    jinja_input = "{% field kind='string' %}{% /field %}"
    jinja_result = fill_markdown(jinja_input, semantic=True)
    assert jinja_result.strip() == jinja_input, (
        f"Jinja: Expected {jinja_input}, got: {jinja_result.strip()}"
    )

    # HTML comment tags
    html_input = '<!-- f:field kind="string" id="name" --><!-- /f:field -->'
    html_result = fill_markdown(html_input, semantic=True)
    assert html_result.strip() == html_input, (
        f"HTML: Expected {html_input}, got: {html_result.strip()}"
    )

    # With surrounding text
    mixed_input = "Before {% field %}{% /field %} after."
    mixed_result = fill_markdown(mixed_input, semantic=True)
    assert "{% field %}{% /field %}" in mixed_result, f"Mixed: Space inserted in: {mixed_result}"


def test_paragraph_text_no_extra_blank_lines():
    """
    Test that paragraph text between tags does NOT get extra blank lines.

    Regular paragraph text should NOT trigger blank line insertion before
    closing tags. Only block content (lists/tables) should get blank lines.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Simple paragraph text between tags - NO blank lines added
    text = "{% description %}\nThis is a simple note.\nJust paragraph text.\n{% /description %}"
    result = wrapper(text, "", "")

    # Should NOT have double newlines before the closing tag
    assert "\n\n{% /description %}" not in result, (
        f"Unexpected blank line before closing tag: {result}"
    )
    # The closing tag should still be on its own line
    assert "\n{% /description %}" in result

    # HTML comment version
    text2 = "<!-- f:note -->\nThis is text content.\n<!-- /f:note -->"
    result2 = wrapper(text2, "", "")
    assert "\n\n<!-- /f:note -->" not in result2, (
        f"Unexpected blank line before closing tag: {result2}"
    )
    assert "\n<!-- /f:note -->" in result2


def test_list_content_gets_blank_lines():
    """
    Test that list content between tags DOES get blank lines.

    List items are block content that requires blank lines to prevent
    CommonMark lazy continuation from merging tags into the list.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # List between tags - SHOULD get blank lines
    text = "{% field %}\n- Item 1\n- Item 2\n{% /field %}"
    result = wrapper(text, "", "")

    # Should have blank line after opening tag (before list)
    assert "{% field %}\n\n" in result, f"Expected blank line after opening tag: {result}"

    # Should have blank line before closing tag (after list)
    assert "\n\n{% /field %}" in result, f"Expected blank line before closing tag: {result}"


def test_table_content_gets_blank_lines():
    """
    Test that table content between tags DOES get blank lines.

    Table rows are block content that requires blank lines.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Table between tags - SHOULD get blank lines
    text = "{% field %}\n| A | B |\n|---|---|\n| 1 | 2 |\n{% /field %}"
    result = wrapper(text, "", "")

    # Should have blank line before table
    assert "{% field %}\n\n" in result, f"Expected blank line after opening tag: {result}"

    # Should have blank line before closing tag
    assert "\n\n{% /field %}" in result, f"Expected blank line before closing tag: {result}"


def test_mixed_content_blank_lines_correct():
    """
    Test that mixed content (text followed by list) gets correct blank lines.

    Only the transition between tag and block content needs blank lines.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Text then list between tags
    text = "{% field %}\nSome intro text.\n- Item 1\n- Item 2\n{% /field %}"
    result = wrapper(text, "", "")

    # Should have blank line before list (list is block content)
    # and blank line before closing tag (after list)
    assert "\n\n{% /field %}" in result, f"Expected blank line before closing tag: {result}"


def test_closing_tag_spacing_function():
    """
    Test the _fix_closing_tag_spacing function directly.

    This function should only add blank lines when the previous line is
    block content (list item or table row), not for regular text.
    """
    from flowmark.linewrapping.tag_handling import (
        _fix_closing_tag_spacing,  # pyright: ignore[reportPrivateUsage]
    )

    # Paragraph text - NO blank line added
    text1 = "Regular text.\n{% /tag %}"
    result1 = _fix_closing_tag_spacing(text1)
    assert result1 == "Regular text.\n{% /tag %}", f"Unexpected change: {result1}"

    # List item - blank line added
    text2 = "- List item\n{% /tag %}"
    result2 = _fix_closing_tag_spacing(text2)
    assert result2 == "- List item\n\n{% /tag %}", f"Expected blank line: {result2}"

    # Table row - blank line added
    text3 = "| A | B |\n{% /tag %}"
    result3 = _fix_closing_tag_spacing(text3)
    assert result3 == "| A | B |\n\n{% /tag %}", f"Expected blank line: {result3}"

    # Already has blank line - no change
    text4 = "- Item\n\n{% /tag %}"
    result4 = _fix_closing_tag_spacing(text4)
    assert result4 == "- Item\n\n{% /tag %}", f"Should not add extra: {result4}"

    # Closing tag with indentation gets stripped
    text5 = "- Item\n   {% /tag %}"
    result5 = _fix_closing_tag_spacing(text5)
    # Blank line added AND indentation stripped
    assert result5 == "- Item\n\n{% /tag %}", f"Expected stripped: {result5}"

    # HTML comment closing tags
    text6 = "Regular text.\n<!-- /tag -->"
    result6 = _fix_closing_tag_spacing(text6)
    assert result6 == "Regular text.\n<!-- /tag -->", f"Unexpected change: {result6}"

    text7 = "- Item\n<!-- /tag -->"
    result7 = _fix_closing_tag_spacing(text7)
    assert result7 == "- Item\n\n<!-- /tag -->", f"Expected blank line: {result7}"


def test_various_tag_types_with_tables():
    """
    Test tables with various tag types (Jinja, HTML comments, variables).

    Tables should always get blank lines regardless of tag type.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Jinja tags with table
    jinja = "{% table %}\n| A | B |\n{% /table %}"
    jinja_result = wrapper(jinja, "", "")
    assert "{% table %}\n\n" in jinja_result
    assert "\n\n{% /table %}" in jinja_result

    # HTML comment tags with table
    html = "<!-- f:table -->\n| A | B |\n<!-- /f:table -->"
    html_result = wrapper(html, "", "")
    assert "<!-- f:table -->\n\n" in html_result
    assert "\n\n<!-- /f:table -->" in html_result

    # Jinja variable tags (edge case - less common with tables)
    var = "{{ header }}\n| A | B |\n{{ footer }}"
    var_result = wrapper(var, "", "")
    # Variable tags should also trigger block heuristics
    assert "{{ header }}\n\n" in var_result


def test_paragraph_only_content_various_tags():
    """
    Test paragraph-only content with various tag types.

    None of these should get extra blank lines.
    """
    from flowmark.linewrapping.line_wrappers import line_wrap_to_width

    wrapper = line_wrap_to_width(width=80, is_markdown=True)

    # Jinja tags
    jinja = "{% note %}\nSimple paragraph.\n{% /note %}"
    jinja_result = wrapper(jinja, "", "")
    assert "\n\n{% /note %}" not in jinja_result

    # HTML comment tags
    html = "<!-- f:warning -->\nWarning text here.\n<!-- /f:warning -->"
    html_result = wrapper(html, "", "")
    assert "\n\n<!-- /f:warning -->" not in html_result

    # Longer paragraph
    long = "{% tip %}\nThis is a longer paragraph with more text that spans across multiple sentences. It should all be wrapped normally.\n{% /tip %}"
    long_result = wrapper(long, "", "")
    assert "\n\n{% /tip %}" not in long_result
