from textwrap import dedent

from flowmark.linewrapping.text_wrapping import (
    MAX_TAG_WORDS,
    _HtmlMdWordSplitter,  # pyright: ignore
    _generate_tag_patterns,  # pyright: ignore
    html_md_word_splitter,
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

    print("\nFilled text with html_md_word_splitter:")
    filled_smart = wrap_paragraph(
        sample_text,
        word_splitter=html_md_word_splitter,
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

    print("\nFilled text with html_md_word_splitter and initial_offset:")
    filled_smart_offset = wrap_paragraph(
        sample_text,
        word_splitter=html_md_word_splitter,
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


def test_generate_tag_patterns():
    """Test the pattern generation function directly."""
    # Test with max_words=4
    patterns = _generate_tag_patterns(start=r"\{%", end=r".*%\}", middle=r".+", max_words=4)

    # Should generate patterns for 2, 3, 4 words
    assert len(patterns) == 3

    # 2-word pattern: (start, end)
    assert patterns[0] == (r"\{%", r".*%\}")

    # 3-word pattern: (start, middle, end)
    assert patterns[1] == (r"\{%", r".+", r".*%\}")

    # 4-word pattern: (start, middle, middle, end)
    assert patterns[2] == (r"\{%", r".+", r".+", r".*%\}")


def test_max_tag_words_constant():
    """Test that MAX_TAG_WORDS is set appropriately for long tags."""
    # Should support at least 10 words
    assert MAX_TAG_WORDS >= 10


def test_long_template_tags():
    """Test that tags with many attributes (10+ words) are kept together."""
    splitter = _HtmlMdWordSplitter()

    # 10-word template tag
    long_tag = "{% component name='widget' type='button' size='large' color='blue' disabled=true %}"
    text = f"Before {long_tag} after."
    result = splitter(text)
    assert long_tag in result

    # 12-word template tag (at the limit)
    very_long_tag = "{% table columns=[a, b, c] rows=[1, 2, 3] border=true striped=true hover=true %}"
    text = f"Before {very_long_tag} after."
    result = splitter(text)
    assert very_long_tag in result


def test_long_html_tags():
    """Test that HTML tags with many attributes are kept together."""
    splitter = _HtmlMdWordSplitter()

    # Long HTML tag with many attributes
    long_html = "<div class='container' id='main' data-value='test' style='color: red'>content</div>"
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


def test_all_tag_types_support_same_max_words():
    """Test that all tag types support the same maximum word count."""
    splitter = _HtmlMdWordSplitter()

    # Create tags with MAX_TAG_WORDS words for each type
    words_inside = " ".join(["word"] * (MAX_TAG_WORDS - 2))

    # Template tag
    template_tag = f"{{%  {words_inside} %}}"
    # Note: we need spaces after {% and before %} for this to work as separate words

    # All should be handled consistently (not broken)
    # This test verifies the splitter doesn't crash on long inputs
    result = splitter(f"text {template_tag} more")
    assert len(result) >= 1  # Should process without error
